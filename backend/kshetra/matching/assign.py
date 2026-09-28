"""Global assignment: turning pairwise scores into a consistent mapping.

The model scores each candidate pair independently, which is not enough. A
cadastre is a *partition* of space, so the final mapping must be globally
coherent: one parcel cannot be matched to three others simply because all
three scored well individually.

This module enforces that coherence and, in doing so, recovers the cases that
matter most to a cadastral officer:

``one_to_one``
    The parcel is unchanged between the two layers.
``split``
    Several source parcels correspond to one reference parcel -- the holding
    was **subdivided** (a plot sold off in parts).
``merge``
    One source parcel covers several reference parcels -- the holdings were
    **amalgamated**.
``unmatched_source``
    Present in the source but nowhere in the reference: either a genuinely new
    parcel, or a spurious record.
``unmatched_reference``
    Present in the reference but missing from the source.

Splits and merges are not noise to be suppressed. They are the legally
significant events that a mutation record is supposed to capture, and
surfacing them automatically is a large part of this system's value.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from kshetra.geometry import safe_polygon

__all__ = ["Match", "AssignmentResult", "assign_matches"]


@dataclass
class Match:
    src_fid: str
    tgt_fids: list[str]
    relation: str
    confidence: float
    evidence: dict = field(default_factory=dict)


@dataclass
class AssignmentResult:
    matches: list[Match]
    unmatched_source: list[str]
    unmatched_reference: list[str]

    def by_relation(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for m in self.matches:
            out[m.relation] = out.get(m.relation, 0) + 1
        out["unmatched_source"] = len(self.unmatched_source)
        out["unmatched_reference"] = len(self.unmatched_reference)
        return out

    def src_to_tgt(self) -> dict[str, list[str]]:
        return {m.src_fid: m.tgt_fids for m in self.matches}


def _coverage(parts, whole) -> float:
    """Fraction of ``whole`` covered by the union of ``parts``."""
    from shapely.ops import unary_union
    if whole.area <= 0:
        return 0.0
    u = unary_union([safe_polygon(p) for p in parts])
    return float(u.intersection(safe_polygon(whole)).area / whole.area)


def assign_matches(cand, probs: np.ndarray, src_layer, tgt_layer,
                   min_prob: float = 0.10,
                   split_merge_coverage: float = 0.55,
                   containment: float = 0.50,
                   part_min_prob: float = 0.40) -> AssignmentResult:
    """Resolve pairwise probabilities into a globally consistent mapping.

    Parameters
    ----------
    cand:
        The :class:`~kshetra.matching.features.CandidateSet` that produced
        ``probs`` (supplies the pair index array).
    probs:
        Calibrated match probability per candidate pair.
    min_prob:
        Pairs below this are discarded outright. Kept low: the assignment
        stage is better placed than a fixed threshold to reject weak pairs,
        because it can see the alternatives.
    split_merge_coverage:
        How much of a parcel the candidate parts must cover before the group
        is declared a genuine subdivision or amalgamation rather than several
        competing matches.
    containment:
        How much of a part must lie inside the whole to count as one of its
        pieces. Lower values recover more subdivisions but start admitting
        merely-adjacent parcels, so this trades split recall against precision.
    part_min_prob:
        Minimum model probability for a pair to be considered as a piece of a
        split or merge group.
    """
    pairs = cand.pairs
    keep = probs >= min_prob
    pairs_k = pairs[keep]
    probs_k = probs[keep]

    n_src, n_tgt = len(src_layer), len(tgt_layer)
    src_feats, tgt_feats = src_layer.features, tgt_layer.features

    matches: list[Match] = []
    matched_src: set[int] = set()
    matched_tgt: set[int] = set()

    if len(pairs_k) == 0:
        return AssignmentResult(
            [], [f.fid for f in src_feats], [f.fid for f in tgt_feats])

    # --- connected components of the surviving bipartite graph -----------
    # Sources occupy node ids [0, n_src); references occupy [n_src, n_src+n_tgt).
    rows = pairs_k[:, 0]
    cols = pairs_k[:, 1] + n_src
    adj = coo_matrix(
        (np.ones(len(pairs_k)), (rows, cols)), shape=(n_src + n_tgt,) * 2)
    n_comp, labels = connected_components(adj, directed=False)

    comp_pairs: dict[int, list[int]] = {}
    for k, (i, j) in enumerate(pairs_k):
        comp_pairs.setdefault(labels[i], []).append(k)

    # Containment ratios are what distinguish a genuine subdivision from two
    # parcels competing for the same match: the parts of a subdivided holding
    # each lie almost entirely *inside* the parent, and together they fill it.
    frac_src_in_tgt: dict[tuple[int, int], float] = {}
    frac_tgt_in_src: dict[tuple[int, int], float] = {}
    for (i, j), pr in (((int(a), int(b)), float(pr))
                       for (a, b), pr in zip(pairs_k, probs_k)):
        if pr < min(part_min_prob, 0.20):
            continue
        a_geom = safe_polygon(src_feats[i].geometry)
        b_geom = safe_polygon(tgt_feats[j].geometry)
        inter = a_geom.intersection(b_geom).area if a_geom.intersects(b_geom) else 0.0
        frac_src_in_tgt[(i, j)] = inter / a_geom.area if a_geom.area > 0 else 0.0
        frac_tgt_in_src[(i, j)] = inter / b_geom.area if b_geom.area > 0 else 0.0

    for comp, ks in comp_pairs.items():
        ks = np.array(ks)
        srcs = sorted(set(pairs_k[ks, 0].tolist()))
        tgts = sorted(set(pairs_k[ks, 1].tolist()))
        prob_lookup = {(int(a), int(b)): float(pr)
                       for (a, b), pr in zip(pairs_k[ks], probs_k[ks])}

        # --- trivial 1:1 component ---------------------------------
        if len(srcs) == 1 and len(tgts) == 1:
            i, j = srcs[0], tgts[0]
            matches.append(Match(
                src_feats[i].fid, [tgt_feats[j].fid], "one_to_one",
                prob_lookup[(i, j)], {"component_size": 1}))
            matched_src.add(i)
            matched_tgt.add(j)
            continue

        claimed_src: set[int] = set()
        claimed_tgt: set[int] = set()

        # --- pass A: subdivision (several sources fill one reference) ---
        for j in tgts:
            parts = [i for i in srcs
                     if i not in claimed_src
                     and prob_lookup.get((i, j), 0.0) >= part_min_prob
                     and frac_src_in_tgt.get((i, j), 0.0) >= containment]
            if len(parts) < 2 or j in claimed_tgt:
                continue
            cov = _coverage([src_feats[i].geometry for i in parts],
                            tgt_feats[j].geometry)
            if cov < split_merge_coverage:
                continue
            conf = float(np.mean([prob_lookup[(i, j)] for i in parts]))
            for i in parts:
                matches.append(Match(
                    src_feats[i].fid, [tgt_feats[j].fid], "split", conf,
                    {"coverage": cov, "n_parts": len(parts),
                     "siblings": [src_feats[s].fid for s in parts if s != i]}))
                matched_src.add(i)
                claimed_src.add(i)
            matched_tgt.add(j)
            claimed_tgt.add(j)

        # --- pass B: amalgamation (one source fills several references) ---
        for i in srcs:
            if i in claimed_src:
                continue
            parts = [j for j in tgts
                     if j not in claimed_tgt
                     and prob_lookup.get((i, j), 0.0) >= part_min_prob
                     and frac_tgt_in_src.get((i, j), 0.0) >= containment]
            if len(parts) < 2:
                continue
            cov = _coverage([tgt_feats[j].geometry for j in parts],
                            src_feats[i].geometry)
            if cov < split_merge_coverage:
                continue
            conf = float(np.mean([prob_lookup[(i, j)] for j in parts]))
            matches.append(Match(
                src_feats[i].fid, [tgt_feats[j].fid for j in parts],
                "merge", conf, {"coverage": cov, "n_parts": len(parts)}))
            matched_src.add(i)
            claimed_src.add(i)
            matched_tgt.update(parts)
            claimed_tgt.update(parts)

        # --- pass C: optimal 1:1 assignment for whatever is left -------
        rem_s = [i for i in srcs if i not in claimed_src]
        rem_t = [j for j in tgts if j not in claimed_tgt]
        if not rem_s or not rem_t:
            continue

        si = {s: a for a, s in enumerate(rem_s)}
        ti = {t: b for b, t in enumerate(rem_t)}
        BIG = 1e3
        cost = np.full((len(rem_s), len(rem_t)), BIG)
        for (a, b), pr in prob_lookup.items():
            if a in si and b in ti:
                cost[si[a], ti[b]] = -np.log(max(pr, 1e-9))

        r, c = linear_sum_assignment(cost)
        for a, b in zip(r, c):
            if cost[a, b] >= BIG:
                continue
            i, j = rem_s[a], rem_t[b]
            matches.append(Match(
                src_feats[i].fid, [tgt_feats[j].fid], "one_to_one",
                prob_lookup[(i, j)],
                {"component_size": len(srcs) + len(tgts),
                 "resolved_by": "hungarian",
                 "n_candidates": len(rem_t)}))
            matched_src.add(i)
            matched_tgt.add(j)

    unmatched_src = [src_feats[i].fid for i in range(n_src)
                     if i not in matched_src]
    unmatched_tgt = [tgt_feats[j].fid for j in range(n_tgt)
                     if j not in matched_tgt]
    return AssignmentResult(matches, unmatched_src, unmatched_tgt)
