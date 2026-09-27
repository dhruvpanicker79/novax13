"""String similarity tuned for Indian land-record attributes.

Written from scratch: ``rapidfuzz`` and ``scikit-learn`` are both blocked by
Application Control on the target machine, and in any case generic fuzzy
matching underperforms here. Owner names in revenue records are romanised by
hand from Devanagari or Urdu, so the same person appears as "Mohammed Qureshi",
"Mohd. Kureshi" and "MOHAMMAD QURESHI". The normalisation step below folds
those variants together *before* any distance is computed, which matters far
more than the choice of distance metric.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

__all__ = [
    "normalise_name", "jaro_winkler", "levenshtein_ratio", "token_set_ratio",
    "name_similarity", "khasra_similarity", "parse_khasra",
]

# Romanisation variants that should collapse to a single canonical form.
# Ordered longest-first so that e.g. "mohammed" is folded before "mohd".
_FOLD = [
    (r"\bmohammad\b|\bmohammed\b|\bmuhammad\b|\bmohd\b|\bmd\b", "mohammad"),
    (r"\babdool\b|\babdul\b", "abdul"),
    (r"\bkureshi\b|\bqureshi\b|\bqurashi\b", "qureshi"),
    (r"\bsing\b|\bsingh\b", "singh"),
    (r"\bsarma\b|\bsharma\b|\bshrama\b", "sharma"),
    (r"\bvarma\b|\bverma\b", "verma"),
    (r"\bgupt\b|\bgupta\b", "gupta"),
    (r"\bchouhan\b|\bchauhan\b|\bchowhan\b", "chauhan"),
    (r"\bjadav\b|\byadav\b|\byadaw\b", "yadav"),
    (r"\bagarwal\b|\baggarwal\b|\bagrawal\b", "agarwal"),
    (r"\bmisra\b|\bmishra\b", "mishra"),
    (r"\bansaari\b|\bansari\b", "ansari"),
    (r"\bkr\b|\bkumar\b", "kumar"),
    (r"\btiwary\b|\btiwari\b|\btewari\b", "tiwari"),
]

# Relationship markers carry no identifying information on their own, but the
# *name that follows them* does, so we keep the token and normalise its form.
_REL = re.compile(r"\b([swd])\s*[/\.]?\s*o\b", re.I)


def normalise_name(name) -> str:
    """Canonicalise an owner name for comparison."""
    if name is None:
        return ""
    s = str(name).lower().strip()
    s = _REL.sub(lambda m: m.group(1) + "/o", s)
    s = re.sub(r"[^a-z0-9/\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for pat, repl in _FOLD:
        s = re.sub(pat, repl, s)
    return s


def jaro_winkler(a: str, b: str, prefix_weight: float = 0.1) -> float:
    """Jaro-Winkler similarity in [0, 1].

    Favours strings agreeing on a common prefix, which suits names where
    corruption tends to hit the tail (suffixes, honorifics) more than the head.
    """
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0

    window = max(la, lb) // 2 - 1
    if window < 0:
        window = 0
    a_flags = [False] * la
    b_flags = [False] * lb

    matches = 0
    for i in range(la):
        lo = max(0, i - window)
        hi = min(i + window + 1, lb)
        for j in range(lo, hi):
            if not b_flags[j] and a[i] == b[j]:
                a_flags[i] = b_flags[j] = True
                matches += 1
                break
    if matches == 0:
        return 0.0

    # Count transpositions among the matched characters.
    k = 0
    transpositions = 0
    for i in range(la):
        if a_flags[i]:
            while not b_flags[k]:
                k += 1
            if a[i] != b[k]:
                transpositions += 1
            k += 1
    transpositions //= 2

    m = float(matches)
    jaro = (m / la + m / lb + (m - transpositions) / m) / 3.0

    prefix = 0
    for i in range(min(4, la, lb)):
        if a[i] == b[i]:
            prefix += 1
        else:
            break
    return jaro + prefix * prefix_weight * (1 - jaro)


def levenshtein_ratio(a: str, b: str) -> float:
    """Normalised edit similarity via difflib (stdlib, no dependency)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def token_set_ratio(a: str, b: str) -> float:
    """Order-independent token overlap (Jaccard on word sets).

    Owner fields routinely reorder name components between departments
    ("Ramesh Kumar Singh" vs "Singh Ramesh Kumar"), so an order-sensitive
    metric alone is not enough.
    """
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def name_similarity(a, b) -> dict[str, float]:
    """All three name signals at once, on normalised input.

    Returned separately rather than blended: the matching model learns how to
    weight them, and the three disagree in informative ways. A high token
    overlap with low Jaro-Winkler means reordered components; the reverse
    means a typo inside one token.
    """
    na, nb = normalise_name(a), normalise_name(b)
    if not na or not nb:
        return {"name_jw": 0.0, "name_lev": 0.0, "name_tok": 0.0,
                "name_present": 0.0}
    return {
        "name_jw": jaro_winkler(na, nb),
        "name_lev": levenshtein_ratio(na, nb),
        "name_tok": token_set_ratio(na, nb),
        "name_present": 1.0,
    }


_KHASRA_RE = re.compile(r"(\d+)(?:\s*/\s*(\d+))?(?:\s*-\s*(\d+))?")


def parse_khasra(value) -> tuple[int | None, int | None, int | None]:
    """Split a khasra string into (parent, child, sub-child).

    Handles the common forms: ``123``, ``123/4``, ``123/4-1``.
    """
    if value is None:
        return (None, None, None)
    m = _KHASRA_RE.search(str(value))
    if not m:
        return (None, None, None)
    g = m.groups()
    return (int(g[0]) if g[0] else None,
            int(g[1]) if g[1] else None,
            int(g[2]) if g[2] else None)


def khasra_similarity(a, b) -> dict[str, float]:
    """Structured comparison of two khasra numbers.

    The hierarchy is meaningful: parcels sharing a parent khasra are
    neighbours in the same original holding, which is strong evidence when the
    geometry is ambiguous, and is exactly the signal that identifies a
    subdivision.
    """
    pa, ca, sa = parse_khasra(a)
    pb, cb, sb = parse_khasra(b)
    if pa is None or pb is None:
        return {"kh_exact": 0.0, "kh_parent": 0.0, "kh_child": 0.0,
                "kh_present": 0.0}
    return {
        "kh_exact": 1.0 if (pa, ca) == (pb, cb) else 0.0,
        "kh_parent": 1.0 if pa == pb else 0.0,
        "kh_child": 1.0 if (ca is not None and ca == cb) else 0.0,
        "kh_present": 1.0,
    }
