"""Provenance-weighted resolution of conflicting claims about one parcel.

When n sources describe the same parcel and disagree, "which one wins" is not a
single question. It depends on *what* is being claimed:

* **Geometry** — a GNSS/CORS observation at 3 cm beats a 1987 paper sheet at
  6 m, and the correct way to combine independent measurements of the same
  quantity is inverse-variance weighting (1/sigma^2), not a hand-set priority list.
* **Ownership** — accuracy is irrelevant. A drone cannot observe who owns a
  plot. The revenue record is *legally authoritative* regardless of how
  precisely anything else was measured.

So authority is **per attribute, not per source**, and the engine keeps the two
separate: a statistical rule for measured quantities, a legal rule for recorded
ones. Conflating them is the classic mistake, and it produces a system that
will confidently overwrite a title with a photograph.

Every resolution records the rule that fired, so a reviewer can see *why* a
value changed rather than being handed a merged layer to trust.

Transitive inconsistency is detected separately. If A agrees with B and B
agrees with C but A contradicts C, no pairwise comparison can see the problem;
it needs the whole claim set at once, and it is a strong signal that one source
is systematically wrong in this area.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np

from kshetra.attributes.text import name_similarity, normalise_name

__all__ = [
    "SourceProfile", "Claim", "Resolution", "ParcelResolution",
    "resolve_parcel", "GEOMETRIC_FIELDS", "AUTHORITATIVE_FIELDS",
]

# Fields that are *measured*: combine by inverse-variance.
GEOMETRIC_FIELDS = {"geometry", "area_sqm", "centroid", "boundary"}
# Fields that are *recorded*: decided by legal authority, never by accuracy.
AUTHORITATIVE_FIELDS = {"owner", "tenure", "khasra", "land_use", "ulpin"}


@dataclass(frozen=True)
class SourceProfile:
    """What a source is, how precise it is, and what it is allowed to decide."""
    source_id: str
    label: str
    accuracy_m: float
    vintage: int
    #: Canonical fields this source is legally authoritative for.
    authority: frozenset[str] = frozenset()

    @property
    def weight(self) -> float:
        """Inverse-variance weight for measured quantities."""
        return 1.0 / max(self.accuracy_m, 0.01) ** 2

    def recency_factor(self, now: int = 2026, half_life: int = 25) -> float:
        """Recency only breaks ties between sources of comparable accuracy.

        It must never let a recent-but-crude source outrank precise control,
        so it is bounded well above zero and applied multiplicatively.
        """
        age = max(now - self.vintage, 0)
        return float(0.5 + 0.5 * np.exp(-age / half_life))


@dataclass
class Claim:
    source: SourceProfile
    field: str
    value: Any
    #: Optional per-feature confidence, e.g. Microsoft's footprint score.
    confidence: float | None = None


@dataclass
class Resolution:
    field: str
    value: Any
    source_id: str
    rule: str
    confidence: float
    agreement: float                       # 0..1, how much the sources concurred
    alternatives: list[tuple[str, Any, float]] = field(default_factory=list)
    note: str = ""


@dataclass
class ParcelResolution:
    fid: str
    resolutions: dict[str, Resolution] = field(default_factory=dict)
    transitive_conflicts: list[str] = field(default_factory=list)
    needs_human: bool = False
    reason: str = ""

    def audit_lines(self) -> list[str]:
        out = []
        for f, r in self.resolutions.items():
            out.append(f"{self.fid} {f}: {r.source_id} wins by {r.rule} "
                       f"(conf {r.confidence:.3f}, agreement {r.agreement:.2f})")
        for t in self.transitive_conflicts:
            out.append(f"{self.fid} TRANSITIVE: {t}")
        return out


# --------------------------------------------------------------------------
def _numeric_consensus(claims: Sequence[Claim]) -> tuple[float, float, float]:
    """Inverse-variance weighted mean of numeric claims.

    Returns ``(value, combined_sigma, agreement)``. Agreement is how tightly
    the sources cluster relative to their own stated uncertainty: near 1 they
    concur within their error bars, near 0 at least one is inconsistent with
    the rest and the combined sigma understates the real disagreement.
    """
    vals = np.array([float(c.value) for c in claims])
    w = np.array([c.source.weight * c.source.recency_factor() for c in claims])
    mu = float((vals * w).sum() / w.sum())
    sigma = float(np.sqrt(1.0 / w.sum()))

    if len(vals) < 2:
        return mu, sigma, 1.0
    # chi-square-style: residuals measured in units of each source's own sigma
    resid = np.array([(v - mu) / max(c.source.accuracy_m, 0.01)
                      for v, c in zip(vals, claims)])
    chi2 = float((resid ** 2).mean())
    agreement = float(np.clip(np.exp(-chi2 / 4.0), 0.0, 1.0))
    return mu, sigma, agreement


def _categorical_consensus(claims: Sequence[Claim]) -> tuple[Any, float, dict]:
    """Weighted vote over non-numeric claims, folding name variants together."""
    buckets: dict[str, dict] = {}
    for c in claims:
        keyed = normalise_key(c.value)
        b = buckets.setdefault(keyed, {"value": c.value, "w": 0.0, "srcs": []})
        b["w"] += c.source.weight * c.source.recency_factor() * (c.confidence or 1.0)
        b["srcs"].append(c.source.source_id)
    total = sum(b["w"] for b in buckets.values()) or 1.0
    best = max(buckets.values(), key=lambda b: b["w"])
    return best["value"], best["w"] / total, buckets


def normalise_key(v: Any) -> str:
    """Fold transliteration variants so 'Mohd. Kureshi' and 'Mohammed Qureshi'
    do not split the vote between themselves and hand victory to a third."""
    if v is None:
        return ""
    s = str(v)
    return normalise_name(s) if any(ch.isalpha() for ch in s) else s.strip().lower()


def _detect_transitive(claims: Sequence[Claim], field_name: str,
                       tol: float = 0.82) -> list[str]:
    """Find A~B, B~C, A!~C triples within one field's claims."""
    if len(claims) < 3:
        return []
    n = len(claims)
    sim = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = claims[i].value, claims[j].value
            try:
                fa, fb = float(a), float(b)
                s = 1.0 - min(abs(fa - fb) / max(abs(fa), abs(fb), 1e-9), 1.0)
            except (TypeError, ValueError):
                s = name_similarity(a, b)["name_jw"]
            sim[i, j] = sim[j, i] = s

    out = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if i >= j or j >= k:
                    continue
                if sim[i, j] >= tol and sim[j, k] >= tol and sim[i, k] < tol:
                    out.append(
                        f"{field_name}: {claims[i].source.source_id} ~ "
                        f"{claims[j].source.source_id} ~ "
                        f"{claims[k].source.source_id}, but "
                        f"{claims[i].source.source_id} != "
                        f"{claims[k].source.source_id} "
                        f"(sim {sim[i, k]:.2f})")
    return out


# --------------------------------------------------------------------------
def resolve_parcel(fid: str, claims: Sequence[Claim],
                   escalate_below: float = 0.55,
                   owner_mismatch_to_human: bool = True) -> ParcelResolution:
    """Resolve every contested field for one parcel.

    ``owner_mismatch_to_human`` defaults on deliberately: an ownership
    disagreement is a legal question, and no weighting scheme should settle it
    silently.
    """
    pr = ParcelResolution(fid=fid)
    by_field: dict[str, list[Claim]] = {}
    for c in claims:
        by_field.setdefault(c.field, []).append(c)

    for fname, fclaims in by_field.items():
        pr.transitive_conflicts += _detect_transitive(fclaims, fname)

        if len(fclaims) == 1:
            c = fclaims[0]
            pr.resolutions[fname] = Resolution(
                fname, c.value, c.source.source_id, "sole source", 1.0, 1.0,
                note="only one source claims this field")
            continue

        # --- legally authoritative fields -----------------------------
        if fname in AUTHORITATIVE_FIELDS:
            auth = [c for c in fclaims if fname in c.source.authority]
            value, share, buckets = _categorical_consensus(fclaims)
            distinct = len(buckets)

            if auth:
                # Most recent authoritative source wins outright.
                win = max(auth, key=lambda c: c.source.vintage)
                disagreeing = distinct > 1
                # Report agreement with the value that actually won, not the
                # share of whichever bucket happened to be largest — otherwise
                # a resolution can read "agreement 1.00" while overriding a
                # source that disagreed.
                win_key = normalise_key(win.value)
                total_w = sum(b["w"] for b in buckets.values()) or 1.0
                win_agreement = buckets.get(win_key, {"w": 0.0})["w"] / total_w
                pr.resolutions[fname] = Resolution(
                    fname, win.value, win.source.source_id,
                    "legal authority", 1.0 if not disagreeing else 0.85,
                    win_agreement,
                    alternatives=[(b["srcs"][0], b["value"], b["w"])
                                  for b in buckets.values()][:3],
                    note=("authoritative source overrides measurement accuracy"
                          if disagreeing else "all sources concur"))
                if disagreeing and fname == "owner" and owner_mismatch_to_human:
                    pr.needs_human = True
                    pr.reason = ("ownership disagreement between sources — "
                                 "a legal question, not a measurement one")
            else:
                pr.resolutions[fname] = Resolution(
                    fname, value, "weighted vote", "provenance vote",
                    share, share,
                    note="no source holds authority for this field")
                if share < escalate_below:
                    pr.needs_human = True
                    pr.reason = f"no clear winner for {fname} (share {share:.2f})"
            continue

        # --- measured quantities ---------------------------------------
        numeric = all(_is_num(c.value) for c in fclaims)
        if numeric:
            mu, sigma, agree = _numeric_consensus(fclaims)
            best = min(fclaims, key=lambda c: c.source.accuracy_m)
            # A single source an order of magnitude better than the rest is
            # not "averaged with" them; it simply wins.
            others = [c for c in fclaims if c is not best]
            dominant = others and best.source.accuracy_m * 10 <= min(
                c.source.accuracy_m for c in others)
            if dominant:
                pr.resolutions[fname] = Resolution(
                    fname, best.value, best.source.source_id,
                    "dominant precision", float(np.clip(agree, 0.5, 1.0)), agree,
                    note=(f"sigma {best.source.accuracy_m:g} m vs "
                          f"{min(c.source.accuracy_m for c in others):g} m — "
                          f"combining would degrade it"))
            else:
                pr.resolutions[fname] = Resolution(
                    fname, mu, "inverse-variance", "inverse-variance fusion",
                    float(np.clip(agree, 0.0, 1.0)), agree,
                    note=f"combined sigma {sigma:.3f} m from {len(fclaims)} sources")
            if agree < escalate_below:
                pr.needs_human = True
                pr.reason = (f"{fname}: sources disagree by more than their "
                             f"stated accuracy (agreement {agree:.2f})")
        else:
            value, share, buckets = _categorical_consensus(fclaims)
            pr.resolutions[fname] = Resolution(
                fname, value, "weighted vote", "provenance vote", share, share)
            if share < escalate_below:
                pr.needs_human = True
                pr.reason = f"no clear winner for {fname} (share {share:.2f})"

    if pr.transitive_conflicts and not pr.needs_human:
        pr.needs_human = True
        pr.reason = "transitive inconsistency between sources"
    return pr


def _is_num(v: Any) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False
