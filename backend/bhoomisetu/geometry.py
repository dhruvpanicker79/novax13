"""Geometry primitives and shape descriptors.

These are the building blocks of the matching model: every descriptor here
becomes a feature in the parcel-matching feature vector, and each is chosen to
be invariant to the specific kinds of distortion legacy cadastral maps carry.
"""
from __future__ import annotations

import math

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

__all__ = [
    "iou", "centroid_offset", "area_ratio", "hausdorff", "compactness",
    "rectangularity", "elongation", "turning_signature", "signature_distance",
    "boundary_overlap_ratio", "safe_polygon", "normalised_symmetric_difference",
]


def safe_polygon(poly: Polygon) -> Polygon:
    """Return a valid polygon, repairing self-intersections if needed."""
    if poly.is_valid:
        return poly
    fixed = poly.buffer(0)
    if fixed.is_empty:
        return poly
    if fixed.geom_type == "MultiPolygon":
        return max(fixed.geoms, key=lambda g: g.area)
    return fixed


def iou(a: Polygon, b: Polygon) -> float:
    """Intersection over union. The single strongest geometric match signal."""
    a, b = safe_polygon(a), safe_polygon(b)
    if a.is_empty or b.is_empty:
        return 0.0
    inter = a.intersection(b).area
    if inter <= 0.0:
        return 0.0
    union = a.area + b.area - inter
    return float(inter / union) if union > 0 else 0.0


def normalised_symmetric_difference(a: Polygon, b: Polygon) -> float:
    """Symmetric difference area divided by mean area. 0 = identical."""
    a, b = safe_polygon(a), safe_polygon(b)
    mean_area = 0.5 * (a.area + b.area)
    if mean_area <= 0:
        return 1.0
    return float(a.symmetric_difference(b).area / mean_area)


def centroid_offset(a: Polygon, b: Polygon) -> float:
    """Distance between centroids, in the units of the CRS (metres)."""
    ca, cb = a.centroid, b.centroid
    return float(math.hypot(ca.x - cb.x, ca.y - cb.y))


def area_ratio(a: Polygon, b: Polygon) -> float:
    """Smaller area over larger area, so the result is always in (0, 1]."""
    aa, ab = a.area, b.area
    if aa <= 0 or ab <= 0:
        return 0.0
    return float(min(aa, ab) / max(aa, ab))


def hausdorff(a: Polygon, b: Polygon) -> float:
    """Hausdorff distance between boundaries: worst-case corner disagreement.

    Complements IoU, which can stay high while one corner is badly wrong.
    """
    return float(a.exterior.hausdorff_distance(b.exterior))


def compactness(poly: Polygon) -> float:
    """Polsby-Popper compactness: 4*pi*A / P^2. 1.0 for a circle."""
    p = poly.exterior.length
    if p <= 0:
        return 0.0
    return float(4.0 * math.pi * poly.area / (p * p))


def rectangularity(poly: Polygon) -> float:
    """Area over minimum-rotated-rectangle area. ~1.0 for urban plots.

    Most surveyed urban parcels are near-rectangular, so a large drop in this
    value is a strong hint that a geometry is corrupted rather than merely
    displaced.
    """
    mrr = poly.minimum_rotated_rectangle
    if mrr.area <= 0:
        return 0.0
    return float(poly.area / mrr.area)


def elongation(poly: Polygon) -> float:
    """Short side over long side of the minimum rotated rectangle."""
    mrr = poly.minimum_rotated_rectangle
    if mrr.geom_type != "Polygon":
        return 1.0
    xs, ys = np.array(mrr.exterior.coords[:-1]).T
    edges = []
    for i in range(len(xs)):
        j = (i + 1) % len(xs)
        edges.append(math.hypot(xs[j] - xs[i], ys[j] - ys[i]))
    edges = sorted(edges)
    long_side = edges[-1]
    short_side = edges[0]
    if long_side <= 0:
        return 1.0
    return float(short_side / long_side)


def turning_signature(poly: Polygon, n: int = 64) -> np.ndarray:
    """Scale- and translation-invariant shape signature.

    Walks the exterior ring at ``n`` equally-spaced arc-length positions and
    records the radius from the centroid, normalised by the mean radius. The
    result is invariant to translation and uniform scale, which is exactly the
    invariance we need: a legacy parcel that has been shifted and rescaled
    should still match its modern counterpart on shape alone.

    Rotation invariance is handled at comparison time by
    :func:`signature_distance`, which minimises over all cyclic rotations.
    """
    ring = poly.exterior
    total = ring.length
    if total <= 0:
        return np.ones(n)
    pts = np.array([ring.interpolate(total * i / n).coords[0] for i in range(n)])
    c = np.array(poly.centroid.coords[0])
    radii = np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1])
    mean_r = radii.mean()
    if mean_r <= 0:
        return np.ones(n)
    return radii / mean_r


def signature_distance(sig_a: np.ndarray, sig_b: np.ndarray) -> float:
    """Rotation-invariant distance between two turning signatures.

    Minimises mean absolute difference over every cyclic shift, so two copies
    of the same plot digitised starting from different corners still match.
    """
    n = len(sig_a)
    # Build every cyclic rotation of sig_b at once via fancy indexing, then
    # take the best-aligned one. Vectorised because this runs once per
    # candidate pair and there are tens of thousands of pairs.
    idx = (np.arange(n)[None, :] - np.arange(n)[:, None]) % n
    rolled = sig_b[idx]                       # (n_shifts, n)
    return float(np.abs(rolled - sig_a[None, :]).mean(axis=1).min())


def boundary_overlap_ratio(a: Polygon, b: Polygon, tol: float = 1.0) -> float:
    """Fraction of ``a``'s boundary lying within ``tol`` metres of ``b``'s.

    Detects shared edges between neighbouring parcels, which is how we spot
    subdivisions: a child parcel shares most of its boundary with its parent.
    """
    if a.exterior.length <= 0:
        return 0.0
    shared = a.exterior.intersection(b.buffer(tol).exterior.buffer(tol))
    return float(min(1.0, shared.length / a.exterior.length))


def dissolve(polys) -> Polygon:
    """Union a collection of polygons into one geometry."""
    return unary_union(list(polys))
