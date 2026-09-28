"""Automatic mapping of department column names onto canonical fields.

Every department names its columns differently, and no two states agree.
``KHSRA_NUM``, ``survey_no``, ``gat_no`` and ``kitta`` are all the same field;
``KHATEDAR_NM``, ``pattadar``, ``bhogvatadar`` and ``owner_name`` are all the
same field. Hard-coding a lookup per source is exactly the manual GIS labour
this project exists to remove, so the mapping is inferred.

Three independent signals are combined, because none alone is reliable:

**Name similarity** against an Indian revenue lexicon. Strong when the column is
named conventionally, useless when it is called ``F14`` or ``COL_3``.

**Value profiling** — dtype, cardinality, uniqueness, and regex shape. A column
that is 99% unique and matches ``\\d+(/\\d+)?`` is a khasra number whatever it is
called; a column with four distinct values across 3,000 rows is categorical and
cannot be an owner name.

**Unit inference against geometry** — the part that matters most in practice.
Recorded area is meaningless until you know its unit, and records are variously
kept in square metres, bigha, biswa, acres or square yards. Rather than trust a
column name, we divide recorded values by the *surveyed* area of the same
parcels and look at the modal ratio: if it clusters near 1 the unit is m², near
1/2529 it is bigha, and so on.

That last check is not academic. NIC's own Bhu-Naksha manual documents a
manually entered per-state scale factor on shapefile import -- UP ×4000,
Himachal ×22 (karam digitised in centimetres). Inferring it from the data
removes a hand-entered magic number from the critical path.

Assignment is 1:1 via the Hungarian algorithm, so two columns cannot both claim
to be the owner field.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment

from kshetra.attributes.text import jaro_winkler, normalise_name
from kshetra.matching.features import FieldMap

__all__ = ["CANONICAL", "AREA_UNITS", "FieldGuess", "SchemaMatch", "match_schema"]

CANONICAL = ["khasra", "owner", "area", "land_use", "tenure", "ward", "ulpin"]

# Column-name vocabulary per canonical field, across north and south Indian
# revenue systems. Deliberately includes romanisation variants.
LEXICON: dict[str, list[str]] = {
    "khasra": [
        "khasra", "khsra", "khasra no", "khasra number", "survey no", "survey number",
        "sy no", "s no", "plot no", "plot number", "parcel id", "parcel no",
        "gat no", "gat", "kitta", "field no", "cts no", "hissa", "num", "id",
    ],
    "owner": [
        "owner", "owner name", "khatedar", "khatadar", "khatedar name", "holder",
        "pattadar", "patadar", "bhogvatadar", "occupant", "name", "possessor",
        "raiyat", "ryot", "tenant name",
    ],
    "area": [
        "area", "rakba", "rakaba", "raqba", "kshetrafal", "extent", "measurement",
        "area sqm", "area bigha", "acre", "hectare", "bigha", "biswa", "sq yards",
        "sqm", "size",
    ],
    "land_use": [
        "land use", "landuse", "lu code", "lu", "luc", "use", "classification",
        "kism", "kisam", "nature", "category", "class",
    ],
    "tenure": [
        "tenure", "tenure type", "tenancy", "patta", "patta type", "title",
        "right", "adhikar", "ownership type", "holding type",
    ],
    "ward": [
        "ward", "ward no", "zone", "mohalla", "sector", "block", "circle",
        "village", "mauza", "revenue circle",
    ],
    "ulpin": [
        "ulpin", "upin", "uid", "parcel uid", "bhu aadhaar", "bhuaadhaar",
        "unique id", "global id",
    ],
}

# Square metres per unit. The inference divides recorded values by surveyed
# geometric area and looks for whichever of these the modal ratio matches.
AREA_UNITS: dict[str, float] = {
    "sqm": 1.0,
    "sq_yard": 0.836127,
    "sq_ft": 0.092903,
    "biswa": 126.44,           # 1/20 bigha (pucca, UP)
    "bigha": 2529.285,         # pucca, UP
    "acre": 4046.86,
    "hectare": 10000.0,
    "guntha": 101.17,
    "cent": 40.4686,
    "ground": 222.967,         # Tamil Nadu
}

_KHASRA_RE = re.compile(r"^\s*\d+\s*(/\s*\d+)?\s*(-\s*\d+)?\s*$")
_WARD_RE = re.compile(r"^[A-Za-z]{0,3}[-_ ]?\d{1,3}$")


@dataclass
class FieldGuess:
    canonical: str
    column: str | None
    confidence: float
    name_score: float = 0.0
    profile_score: float = 0.0
    evidence: str = ""
    alternatives: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class SchemaMatch:
    guesses: dict[str, FieldGuess]
    area_unit: str | None = None
    area_scale: float = 1.0
    area_unit_confidence: float = 0.0
    area_unit_evidence: str = ""
    unmapped_columns: list[str] = field(default_factory=list)

    def to_field_map(self) -> FieldMap:
        g = self.guesses
        pick = lambda k: (g[k].column if k in g and g[k].column else None)
        return FieldMap(
            khasra=pick("khasra"), owner=pick("owner"), area=pick("area"),
            land_use=pick("land_use"), ward=pick("ward"),
            area_scale=self.area_scale,
        )

    def summary(self) -> str:
        rows = [f"{'field':<10} {'column':<16} {'conf':>6}  evidence"]
        rows.append("-" * 74)
        for c in CANONICAL:
            g = self.guesses.get(c)
            if not g or not g.column:
                rows.append(f"{c:<10} {'— unmapped —':<16} {'':>6}")
                continue
            rows.append(f"{c:<10} {g.column:<16} {g.confidence:>6.3f}  {g.evidence}")
        if self.area_unit:
            rows.append("")
            rows.append(f"area unit: {self.area_unit} (x{self.area_scale:.4f} -> m2), "
                        f"confidence {self.area_unit_confidence:.3f}")
            rows.append(f"  {self.area_unit_evidence}")
        return "\n".join(rows)


# --------------------------------------------------------------------------
# signal 1: column-name similarity
# --------------------------------------------------------------------------
def _tokenise(col: str) -> str:
    s = re.sub(r"[_\-]+", " ", str(col))
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _name_score(column: str, canonical: str) -> tuple[float, str]:
    c = _tokenise(column)
    best, term = 0.0, ""
    for cand in LEXICON[canonical]:
        s = jaro_winkler(c, cand)
        # Abbreviations are pervasive ("KHSRA_NUM"), so reward containment.
        if cand in c or c in cand:
            s = max(s, 0.92)
        if s > best:
            best, term = s, cand
    return best, term


# --------------------------------------------------------------------------
# signal 2: value profiling
# --------------------------------------------------------------------------
def _profile(values: Sequence[Any]) -> dict[str, float]:
    vals = [v for v in values if v is not None and v != ""]
    n = len(vals)
    if n == 0:
        return {"n": 0}
    strs = [str(v) for v in vals]
    uniq = len(set(strs))
    nums = []
    for v in vals:
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            pass
    return {
        "n": n,
        "fill": n / max(len(values), 1),
        "unique_ratio": uniq / n,
        "numeric_ratio": len(nums) / n,
        "mean_tokens": float(np.mean([len(s.split()) for s in strs])),
        "mean_len": float(np.mean([len(s) for s in strs])),
        "khasra_like": sum(1 for s in strs if _KHASRA_RE.match(s)) / n,
        "ward_like": sum(1 for s in strs if _WARD_RE.match(s)) / n,
        "rel_marker": sum(1 for s in strs
                          if re.search(r"\b[swd]\s*/\s*o\b", s, re.I)) / n,
        "alpha_num_fixed": sum(1 for s in strs
                               if s.isalnum() and len(s) >= 10) / n,
    }


def _profile_score(canonical: str, p: dict[str, float]) -> tuple[float, str]:
    """How well a column's value shape fits a canonical field."""
    if p.get("n", 0) == 0:
        return 0.0, "empty column"
    u, num = p["unique_ratio"], p["numeric_ratio"]

    if canonical == "khasra":
        s = 0.55 * p["khasra_like"] + 0.45 * min(u * 1.2, 1.0)
        return s, f"{p['khasra_like']*100:.0f}% match n or n/m, {u*100:.0f}% unique"
    if canonical == "owner":
        multi = min(p["mean_tokens"] / 4.0, 1.0)
        s = 0.4 * multi + 0.3 * min(u * 1.2, 1.0) + 0.3 * min(p["rel_marker"] * 2, 1.0)
        return s, (f"{p['mean_tokens']:.1f} tokens/value, "
                   f"{p['rel_marker']*100:.0f}% carry s/o|w/o|d/o")
    if canonical == "area":
        s = 0.75 * num + 0.25 * min(u * 1.2, 1.0)
        return s, f"{num*100:.0f}% numeric"
    if canonical in ("land_use", "tenure"):
        # Categorical: few distinct values over many rows.
        cat = 1.0 - min(u * 12, 1.0)
        s = 0.8 * cat + 0.2 * (1 - num)
        return s, f"{int(u * p['n'])} distinct values in {int(p['n'])} rows"
    if canonical == "ward":
        s = 0.6 * p["ward_like"] + 0.4 * (1.0 - min(u * 12, 1.0))
        return s, f"{p['ward_like']*100:.0f}% look like a ward code"
    if canonical == "ulpin":
        s = 0.6 * p["alpha_num_fixed"] + 0.4 * min(u * 1.1, 1.0)
        return s, f"{p['alpha_num_fixed']*100:.0f}% long alphanumeric, {u*100:.0f}% unique"
    return 0.0, ""


# --------------------------------------------------------------------------
# signal 3: area unit inferred from geometry
# --------------------------------------------------------------------------
def infer_area_unit(recorded: Sequence[Any], geometric: Sequence[float]
                    ) -> tuple[str | None, float, float, str]:
    """Infer the unit of a recorded-area column by comparing it to surveyed area.

    Returns ``(unit, scale_to_sqm, confidence, evidence)``.

    The ratio recorded/geometric is computed per parcel and the *median* taken,
    which is robust to the minority of records that are simply wrong. The unit
    whose factor best explains that median wins.
    """
    pairs = []
    for r, g in zip(recorded, geometric):
        try:
            rv = float(r)
        except (TypeError, ValueError):
            continue
        if rv > 0 and g > 0:
            pairs.append(g / rv)          # m2 per recorded unit
    if len(pairs) < 20:
        return None, 1.0, 0.0, f"only {len(pairs)} usable pairs; not inferred"

    arr = np.array(pairs)
    med = float(np.median(arr))
    spread = float(np.percentile(arr, 75) / max(np.percentile(arr, 25), 1e-9))

    best, best_err = None, math.inf
    for unit, factor in AREA_UNITS.items():
        err = abs(math.log(med / factor))
        if err < best_err:
            best, best_err = unit, err

    # log-ratio error of 0.05 is ~5%; map that onto a confidence.
    conf = float(np.clip(1.0 - best_err / 0.35, 0.0, 1.0))
    # A tight interquartile spread means the ratio is a real constant rather
    # than noise, which is the whole basis of the inference.
    conf *= float(np.clip(1.5 - (spread - 1.0), 0.0, 1.0))

    ev = (f"median m2/unit = {med:.4f} over {len(pairs)} parcels "
          f"(IQR ratio {spread:.2f}); closest is {best} at {AREA_UNITS[best]:.4f}")
    return best, AREA_UNITS[best], conf, ev


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------
def match_schema(records: Sequence[dict], geometric_areas: Sequence[float] | None = None,
                 min_confidence: float = 0.45) -> SchemaMatch:
    """Infer a :class:`FieldMap` from raw attribute records.

    Parameters
    ----------
    records:
        The attribute dictionaries of a layer, as loaded from the source.
    geometric_areas:
        Surveyed area per record, in m². Supplying this enables unit inference,
        which is the difference between a usable area field and a number of
        unknown scale.
    """
    if not records:
        return SchemaMatch(guesses={}, unmapped_columns=[])

    columns = sorted({k for r in records for k in r.keys()})
    profiles = {c: _profile([r.get(c) for r in records]) for c in columns}

    # Score every (canonical, column) pair.
    S = np.zeros((len(CANONICAL), len(columns)))
    detail: dict[tuple[int, int], tuple[float, float, str]] = {}
    for i, canon in enumerate(CANONICAL):
        for j, col in enumerate(columns):
            ns, term = _name_score(col, canon)
            ps, ev = _profile_score(canon, profiles[col])
            # Name and shape are weighted evenly: a well-named column with the
            # wrong shape is as suspicious as the reverse.
            score = 0.5 * ns + 0.5 * ps
            S[i, j] = score
            detail[(i, j)] = (ns, ps, f"name~'{term}' ({ns:.2f}); {ev}")

    # 1:1 assignment, so two columns cannot both be the owner field.
    rows, cols = linear_sum_assignment(-S)

    guesses: dict[str, FieldGuess] = {}
    taken: set[int] = set()
    for i, j in zip(rows, cols):
        canon, col = CANONICAL[i], columns[j]
        ns, ps, ev = detail[(i, j)]
        conf = float(S[i, j])
        alts = sorted(
            ((columns[jj], float(S[i, jj])) for jj in range(len(columns)) if jj != j),
            key=lambda t: -t[1])[:3]
        if conf < min_confidence:
            guesses[canon] = FieldGuess(canon, None, conf, ns, ps,
                                        f"best candidate '{col}' scored {conf:.2f}, "
                                        f"below threshold {min_confidence}", alts)
        else:
            guesses[canon] = FieldGuess(canon, col, conf, ns, ps, ev, alts)
            taken.add(j)

    sm = SchemaMatch(
        guesses=guesses,
        unmapped_columns=[columns[j] for j in range(len(columns)) if j not in taken],
    )

    area_col = guesses.get("area").column if guesses.get("area") else None
    if area_col and geometric_areas is not None:
        unit, scale, conf, ev = infer_area_unit(
            [r.get(area_col) for r in records], geometric_areas)
        sm.area_unit, sm.area_scale = unit, scale
        sm.area_unit_confidence, sm.area_unit_evidence = conf, ev
    return sm
