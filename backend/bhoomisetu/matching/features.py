"""Candidate generation and pairwise feature extraction for parcel matching.

Matching two cadastral layers is a *spatial entity resolution* problem, and it
is solved in three stages:

1. **Blocking** -- an R-tree restricts comparisons to spatially plausible
   pairs. Comparing all 3000 x 3000 pairs is both wasteful and harmful, since
   it floods the model with trivial negatives.
2. **Feature extraction** -- this module. Each surviving pair is described by
   geometric agreement, attribute agreement, and *context*.
3. **Scoring and assignment** -- see :mod:`bhoomisetu.matching.model` and
   :mod:`bhoomisetu.matching.assign`.

The context features matter more than they look. Raw IoU cannot distinguish
"this is a confident match" from "this is the best of several equally poor
options"; the rank and margin features make that distinction explicit, and
they are what allow the confidence score to be honest about ambiguity.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from shapely.strtree import STRtree

from bhoomisetu.attributes.text import khasra_similarity, name_similarity
from bhoomisetu.geometry import (
    compactness, elongation, iou, rectangularity, safe_polygon,
    signature_distance, turning_signature,
)
from bhoomisetu.layers import Layer

__all__ = ["FieldMap", "CandidateSet", "generate_candidates",
           "build_feature_matrix", "FEATURE_NAMES"]


@dataclass
class FieldMap:
    """Which attribute key in a layer holds each semantic field.

    Produced by the schema-matching stage, so the matcher never hard-codes
    column names. ``area_scale`` converts the recorded area into square metres
    (e.g. 2529.285 when the record is kept in bigha).
    """
    khasra: str | None = "khasra_no"
    owner: str | None = "owner_name"
    area: str | None = "recorded_area_sqm"
    land_use: str | None = "land_use"
    ward: str | None = "ward_no"
    area_scale: float = 1.0

    def get(self, feat, field: str):
        key = getattr(self, field)
        return feat.attrs.get(key) if key else None


FEATURE_NAMES = [
    # --- geometric agreement ---
    "iou", "sym_diff_norm", "centroid_dist", "centroid_dist_norm",
    "area_ratio", "hausdorff_norm", "sig_dist",
    "src_frac_in_tgt", "tgt_frac_in_src",
    # --- shape descriptors ---
    "d_compactness", "d_rectangularity", "d_elongation", "vertex_ratio",
    # --- attribute agreement ---
    "name_jw", "name_lev", "name_tok", "name_present",
    "kh_exact", "kh_parent", "kh_child", "kh_present",
    "area_attr_ratio", "land_use_match", "ward_match",
    # --- context / ambiguity ---
    "n_candidates", "iou_rank", "iou_margin", "is_best_iou", "rev_iou_rank",
]


@dataclass
class CandidateSet:
    """Candidate pairs plus the cached geometry derivatives they need."""
    src: Layer
    tgt: Layer
    pairs: np.ndarray            # (N, 2) int, indices into src / tgt
    src_sig: list
    tgt_sig: list


def generate_candidates(src: Layer, tgt: Layer, search_radius: float = 18.0,
                        max_per_source: int = 18) -> CandidateSet:
    """Blocking step: spatially plausible (source, target) pairs.

    ``search_radius`` must exceed the worst expected misregistration, or true
    matches are discarded before the model ever sees them. It is cheap to be
    generous here and let the model reject; it is fatal to be too tight.
    """
    src_geoms = [safe_polygon(f.geometry) for f in src]
    tgt_geoms = [safe_polygon(f.geometry) for f in tgt]
    tree = STRtree(tgt_geoms)

    pairs: list[tuple[int, int]] = []
    for i, g in enumerate(src_geoms):
        hits = tree.query(g.buffer(search_radius))
        if len(hits) == 0:
            continue
        # Keep the most plausible candidates when a source is crowded.
        # Ranking purely by intersection area starves small parcels: half of a
        # subdivided plot overlaps its parent by only a modest absolute area
        # and loses to larger neighbours. So overlap ranks first, and
        # non-overlapping candidates fall back to centroid proximity, which
        # keeps the true counterpart in contention for small geometries.
        if len(hits) > max_per_source:
            c = g.centroid

            def _rank(j):
                inter = g.intersection(tgt_geoms[j]).area
                if inter > 0:
                    return (1, inter)
                tc = tgt_geoms[j].centroid
                return (0, -((tc.x - c.x) ** 2 + (tc.y - c.y) ** 2))

            hits = sorted(hits, key=_rank, reverse=True)[:max_per_source]
        for j in hits:
            pairs.append((i, int(j)))

    src_sig = [turning_signature(g) for g in src_geoms]
    tgt_sig = [turning_signature(g) for g in tgt_geoms]
    return CandidateSet(src, tgt, np.array(pairs, dtype=int), src_sig, tgt_sig)


def _vertex_count(geom) -> int:
    return len(geom.exterior.coords)


def build_feature_matrix(cand: CandidateSet,
                         src_fields: FieldMap | None = None,
                         tgt_fields: FieldMap | None = None) -> np.ndarray:
    """Compute the (N, len(FEATURE_NAMES)) feature matrix for all candidates."""
    src_fields = src_fields or FieldMap()
    tgt_fields = tgt_fields or FieldMap()

    src_geoms = [safe_polygon(f.geometry) for f in cand.src]
    tgt_geoms = [safe_polygon(f.geometry) for f in cand.tgt]
    pairs = cand.pairs
    n = len(pairs)
    X = np.zeros((n, len(FEATURE_NAMES)), dtype=np.float32)

    # --- pass 1: pairwise quantities -------------------------------------
    ious = np.zeros(n)
    for k, (i, j) in enumerate(pairs):
        a, b = src_geoms[i], tgt_geoms[j]
        af, bf = cand.src[i], cand.tgt[j]

        inter = a.intersection(b).area if a.intersects(b) else 0.0
        union = a.area + b.area - inter
        v_iou = inter / union if union > 0 else 0.0
        ious[k] = v_iou

        mean_area = 0.5 * (a.area + b.area)
        scale = np.sqrt(mean_area) if mean_area > 0 else 1.0
        ca, cb = a.centroid, b.centroid
        cdist = float(np.hypot(ca.x - cb.x, ca.y - cb.y))

        row = {
            "iou": v_iou,
            "sym_diff_norm": (a.area + b.area - 2 * inter) / mean_area
                             if mean_area > 0 else 1.0,
            "centroid_dist": cdist,
            "centroid_dist_norm": cdist / scale,
            "area_ratio": (min(a.area, b.area) / max(a.area, b.area))
                          if a.area > 0 and b.area > 0 else 0.0,
            "hausdorff_norm": float(
                a.exterior.hausdorff_distance(b.exterior)) / scale,
            "sig_dist": signature_distance(cand.src_sig[i], cand.tgt_sig[j]),
            "src_frac_in_tgt": inter / a.area if a.area > 0 else 0.0,
            "tgt_frac_in_src": inter / b.area if b.area > 0 else 0.0,
            "d_compactness": abs(compactness(a) - compactness(b)),
            "d_rectangularity": abs(rectangularity(a) - rectangularity(b)),
            "d_elongation": abs(elongation(a) - elongation(b)),
            "vertex_ratio": (min(_vertex_count(a), _vertex_count(b))
                             / max(_vertex_count(a), _vertex_count(b))),
        }

        row.update(name_similarity(src_fields.get(af, "owner"),
                                   tgt_fields.get(bf, "owner")))
        row.update(khasra_similarity(src_fields.get(af, "khasra"),
                                     tgt_fields.get(bf, "khasra")))

        # Recorded area (converted to m2) against the target's true geometry.
        rec = src_fields.get(af, "area")
        if rec is None or b.area <= 0:
            row["area_attr_ratio"] = 0.0
        else:
            rec_m2 = float(rec) * src_fields.area_scale
            row["area_attr_ratio"] = (min(rec_m2, b.area)
                                      / max(rec_m2, b.area)) if rec_m2 > 0 else 0.0

        lu_a, lu_b = src_fields.get(af, "land_use"), tgt_fields.get(bf, "land_use")
        row["land_use_match"] = 1.0 if (lu_a and lu_b and lu_a == lu_b) else 0.0
        w_a, w_b = src_fields.get(af, "ward"), tgt_fields.get(bf, "ward")
        row["ward_match"] = 1.0 if (w_a and w_b and w_a == w_b) else 0.0

        for c, name in enumerate(FEATURE_NAMES):
            if name in row:
                X[k, c] = row[name]

    # --- pass 2: context features ----------------------------------------
    col = {name: i for i, name in enumerate(FEATURE_NAMES)}
    by_src: dict[int, list[int]] = {}
    by_tgt: dict[int, list[int]] = {}
    for k, (i, j) in enumerate(pairs):
        by_src.setdefault(i, []).append(k)
        by_tgt.setdefault(j, []).append(k)

    for i, ks in by_src.items():
        vals = ious[ks]
        order = np.argsort(-vals)
        ranks = np.empty(len(ks), dtype=float)
        ranks[order] = np.arange(len(ks))
        best = vals.max()
        second = np.sort(vals)[-2] if len(vals) > 1 else 0.0
        for pos, k in enumerate(ks):
            X[k, col["n_candidates"]] = len(ks)
            X[k, col["iou_rank"]] = ranks[pos]
            X[k, col["iou_margin"]] = best - second
            X[k, col["is_best_iou"]] = 1.0 if ranks[pos] == 0 else 0.0

    for j, ks in by_tgt.items():
        vals = ious[ks]
        order = np.argsort(-vals)
        ranks = np.empty(len(ks), dtype=float)
        ranks[order] = np.arange(len(ks))
        for pos, k in enumerate(ks):
            X[k, col["rev_iou_rank"]] = ranks[pos]

    return X
