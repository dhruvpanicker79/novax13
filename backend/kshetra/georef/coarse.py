"""Coarse global alignment, run *before* any parcel matching.

Discovered empirically, and it is one of the more important findings in this
project: matching parcels before georeferencing them does not work. Urban
plots are ~11 m across while legacy misregistration is routinely 5-15 m, so an
unaligned legacy parcel physically overlaps its *neighbour* more than its own
counterpart. Any matcher fed that geometry is forced to fall back on attribute
joins -- which defeats the purpose, because unreliable attributes are exactly
why spatial matching is needed.

So the pipeline is strictly ordered: align globally, then match locally.

The alignment runs in three stages, each robust to the failure mode of the one
before it:

1. **Translation voting.** Every source centroid votes for the displacement to
   each of its k nearest reference centroids. The true translation is shared by
   thousands of parcels while wrong pairings scatter, so it appears as a sharp
   peak in a 2-D histogram of the votes. This is a Hough transform, and unlike
   ICP it has no initialisation requirement and cannot fall into a local
   minimum.
2. **Robust similarity refinement.** Starting from the voted translation, fit
   rotation, scale and translation on mutual-nearest-neighbour pairs, rejecting
   outliers by a trimmed residual threshold, and iterate.
3. **Residual reporting.** The remaining error is the non-linear part (paper
   warp), which the fine georeferencing stage removes later using matched
   parcels as control points.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from kshetra.geometry import safe_polygon
from kshetra.georef.transform import Similarity

__all__ = ["CoarseAlignment", "vote_translation", "coarse_align"]


@dataclass
class CoarseAlignment:
    transform: Similarity
    translation: tuple[float, float]
    rotation_deg: float
    scale: float
    n_inliers: int
    residual_rmse: float
    residual_median: float
    iterations: int
    # Physical displacement applied at the centre of the data. The raw
    # ``transform.tx/ty`` are the translation of a rotation about the
    # coordinate *origin*; with UTM northings near 3.1 million a rotation of a
    # fraction of a degree makes them enormous and physically meaningless.
    # This is the number to quote and to show a surveyor.
    displacement: tuple[float, float] = (0.0, 0.0)

    @property
    def displacement_m(self) -> float:
        return float(np.hypot(*self.displacement))

    def apply_layer(self, layer):
        """Return a copy of ``layer`` with the alignment applied."""
        return layer.map_geometry(
            lambda g: self.transform.apply_geometry(safe_polygon(g)))


def _centroids(layer) -> np.ndarray:
    return np.array([[f.geometry.centroid.x, f.geometry.centroid.y]
                     for f in layer])


def vote_translation(src_pts: np.ndarray, tgt_pts: np.ndarray,
                     max_shift: float = 60.0, k: int = 6,
                     bin_size: float = 1.0) -> tuple[float, float]:
    """Estimate the dominant translation by Hough voting on displacements.

    Parameters
    ----------
    max_shift:
        Largest displacement considered, in metres. Votes outside are ignored.
    k:
        Nearest reference points each source point votes for. The true
        correspondence need only be *among* the k nearest, not the first.
    bin_size:
        Vote histogram resolution in metres.
    """
    tree = cKDTree(tgt_pts)
    k = min(k, len(tgt_pts))
    _, idx = tree.query(src_pts, k=k)
    idx = np.atleast_2d(idx.T).T if idx.ndim == 1 else idx

    # Displacement vector for every (source, candidate reference) pairing.
    dx = tgt_pts[idx][:, :, 0] - src_pts[:, None, 0]
    dy = tgt_pts[idx][:, :, 1] - src_pts[:, None, 1]
    dx, dy = dx.ravel(), dy.ravel()

    m = (np.abs(dx) <= max_shift) & (np.abs(dy) <= max_shift)
    dx, dy = dx[m], dy[m]
    if len(dx) == 0:
        return 0.0, 0.0

    n_bins = int(2 * max_shift / bin_size) + 1
    edges = np.linspace(-max_shift, max_shift, n_bins + 1)
    H, xe, ye = np.histogram2d(dx, dy, bins=[edges, edges])

    bi, bj = np.unravel_index(np.argmax(H), H.shape)
    # Refine to sub-bin precision using the centroid of the 3x3 neighbourhood
    # around the peak, which removes the quantisation error of the histogram.
    i0, i1 = max(0, bi - 1), min(H.shape[0], bi + 2)
    j0, j1 = max(0, bj - 1), min(H.shape[1], bj + 2)
    patch = H[i0:i1, j0:j1]
    xs = 0.5 * (xe[i0:i1] + xe[i0 + 1:i1 + 1])
    ys = 0.5 * (ye[j0:j1] + ye[j0 + 1:j1 + 1])
    w = patch.sum()
    if w <= 0:
        return float(0.5 * (xe[bi] + xe[bi + 1])), float(0.5 * (ye[bj] + ye[bj + 1]))
    tx = float((patch.sum(axis=1) * xs).sum() / w)
    ty = float((patch.sum(axis=0) * ys).sum() / w)
    return tx, ty


def coarse_align(src_layer, tgt_layer, max_shift: float = 60.0,
                 max_iter: int = 12, trim_quantile: float = 0.70,
                 tol: float = 1e-3) -> CoarseAlignment:
    """Align ``src_layer`` onto ``tgt_layer`` with a global similarity.

    Returns a :class:`CoarseAlignment`; apply it with ``.apply_layer()``.
    """
    src = _centroids(src_layer)
    tgt = _centroids(tgt_layer)
    if len(src) < 3 or len(tgt) < 3:
        return CoarseAlignment(Similarity(), (0.0, 0.0), 0.0, 1.0, 0,
                               float("nan"), float("nan"), 0, (0.0, 0.0))

    # --- stage 1: translation vote -----------------------------------
    tx, ty = vote_translation(src, tgt, max_shift=max_shift)
    model = Similarity(a=1.0, b=0.0, tx=tx, ty=ty)

    tree = cKDTree(tgt)
    n_in = 0
    resid = np.array([np.nan])
    it = 0

    # --- stage 2: robust similarity refinement ------------------------
    for it in range(1, max_iter + 1):
        moved = model.apply(src)
        dist, idx = tree.query(moved, k=1)

        # Trimmed least squares: fit only on the closest fraction of pairs, so
        # genuine one-to-one correspondences dominate and split/merge/spurious
        # parcels cannot drag the fit.
        cut = np.quantile(dist, trim_quantile)
        keep = dist <= max(cut, 1e-6)
        if keep.sum() < 3:
            break

        new_model = Similarity.fit(src[keep], tgt[idx[keep]])
        moved_new = new_model.apply(src)
        d_new = np.linalg.norm(moved_new - tgt[idx], axis=1)

        shift = np.abs(np.array([new_model.tx - model.tx,
                                 new_model.ty - model.ty])).max()
        model = new_model
        n_in = int(keep.sum())
        resid = d_new[keep]
        if shift < tol:
            break

    centre = src.mean(axis=0, keepdims=True)
    moved_centre = model.apply(centre)[0]
    disp = (float(moved_centre[0] - centre[0, 0]),
            float(moved_centre[1] - centre[0, 1]))

    return CoarseAlignment(
        transform=model,
        translation=(model.tx, model.ty),
        displacement=disp,
        rotation_deg=model.rotation_deg,
        scale=model.scale,
        n_inliers=n_in,
        residual_rmse=float(np.sqrt((resid ** 2).mean())),
        residual_median=float(np.median(resid)),
        iterations=it,
    )
