"""Planar transformation models for georeferencing and rubber-sheeting.

Four models, in increasing order of flexibility. Georeferencing a legacy
cadastral sheet means picking the *least* flexible model that fits, because an
over-flexible model will happily absorb genuine survey error into the warp and
destroy the geometry it was meant to correct:

``Similarity``
    Rotation, uniform scale, translation (4 DoF). The physically honest model
    for a map that was correctly surveyed but wrongly registered.
``Affine``
    Adds shear and differential scale (6 DoF). Handles non-square pixel grids
    and uniformly stretched paper.
``Polynomial`` (order 2)
    Smooth global curvature (12 DoF). Handles lens and scanner distortion.
``ThinPlateSpline``
    Exact interpolation through every control point, minimum bending energy.
    Handles localised paper shrinkage, but needs well-distributed control
    points or it will oscillate wildly outside their convex hull.

All models expose ``fit``, ``apply``, ``apply_geometry`` and ``rmse``.
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

__all__ = [
    "Similarity", "Affine", "Polynomial", "ThinPlateSpline",
    "fit_best_transform", "transform_geometry",
]


def _as_xy(pts) -> np.ndarray:
    a = np.asarray(pts, dtype=float)
    if a.ndim != 2 or a.shape[1] != 2:
        raise ValueError("control points must be an (N, 2) array")
    return a


def transform_geometry(geom: BaseGeometry, fn) -> BaseGeometry:
    """Apply a coordinate-mapping callable to every vertex of a geometry."""
    if geom.is_empty:
        return geom
    if geom.geom_type == "Polygon":
        ext = fn(np.array(geom.exterior.coords))
        ints = [fn(np.array(r.coords)) for r in geom.interiors]
        return Polygon(ext, ints)
    if geom.geom_type == "MultiPolygon":
        return MultiPolygon([transform_geometry(g, fn) for g in geom.geoms])
    coords = fn(np.array(geom.coords))
    return type(geom)(coords)


class _Base:
    """Common fit/apply plumbing."""

    def apply(self, pts) -> np.ndarray:
        raise NotImplementedError

    def apply_geometry(self, geom: BaseGeometry) -> BaseGeometry:
        return transform_geometry(geom, self.apply)

    def rmse(self, src, dst) -> float:
        """Root-mean-square residual at the control points, in CRS units."""
        pred = self.apply(_as_xy(src))
        d = pred - _as_xy(dst)
        return float(np.sqrt((d ** 2).sum(axis=1).mean()))

    def residuals(self, src, dst) -> np.ndarray:
        pred = self.apply(_as_xy(src))
        return np.linalg.norm(pred - _as_xy(dst), axis=1)


class Similarity(_Base):
    """Rotation + uniform scale + translation (Helmert 2D, 4 parameters)."""

    def __init__(self, a=1.0, b=0.0, tx=0.0, ty=0.0):
        self.a, self.b, self.tx, self.ty = a, b, tx, ty

    @property
    def scale(self) -> float:
        return float(np.hypot(self.a, self.b))

    @property
    def rotation_deg(self) -> float:
        return float(np.degrees(np.arctan2(self.b, self.a)))

    @classmethod
    def fit(cls, src, dst) -> "Similarity":
        s, d = _as_xy(src), _as_xy(dst)
        if len(s) < 2:
            raise ValueError("similarity fit needs >= 2 control points")
        # Least squares on [x -y 1 0; y x 0 1] @ [a b tx ty] = [X Y]
        n = len(s)
        A = np.zeros((2 * n, 4))
        A[0::2, 0] = s[:, 0]; A[0::2, 1] = -s[:, 1]; A[0::2, 2] = 1
        A[1::2, 0] = s[:, 1]; A[1::2, 1] = s[:, 0];  A[1::2, 3] = 1
        y = np.empty(2 * n)
        y[0::2], y[1::2] = d[:, 0], d[:, 1]
        p, *_ = np.linalg.lstsq(A, y, rcond=None)
        return cls(*p)

    def apply(self, pts) -> np.ndarray:
        p = _as_xy(pts)
        x = self.a * p[:, 0] - self.b * p[:, 1] + self.tx
        y = self.b * p[:, 0] + self.a * p[:, 1] + self.ty
        return np.column_stack([x, y])


class Affine(_Base):
    """Full 6-parameter affine transform."""

    def __init__(self, m: np.ndarray | None = None):
        self.m = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]) if m is None else m

    @classmethod
    def fit(cls, src, dst) -> "Affine":
        s, d = _as_xy(src), _as_xy(dst)
        if len(s) < 3:
            raise ValueError("affine fit needs >= 3 control points")
        A = np.column_stack([s[:, 0], s[:, 1], np.ones(len(s))])
        mx, *_ = np.linalg.lstsq(A, d[:, 0], rcond=None)
        my, *_ = np.linalg.lstsq(A, d[:, 1], rcond=None)
        return cls(np.vstack([mx, my]))

    def apply(self, pts) -> np.ndarray:
        p = _as_xy(pts)
        A = np.column_stack([p[:, 0], p[:, 1], np.ones(len(p))])
        return np.column_stack([A @ self.m[0], A @ self.m[1]])


class Polynomial(_Base):
    """Second-order polynomial (12 parameters)."""

    def __init__(self, cx=None, cy=None, order: int = 2):
        self.cx, self.cy, self.order = cx, cy, order

    @staticmethod
    def _design(p: np.ndarray, order: int) -> np.ndarray:
        x, y = p[:, 0], p[:, 1]
        cols = [np.ones(len(p)), x, y]
        if order >= 2:
            cols += [x * x, x * y, y * y]
        if order >= 3:
            cols += [x**3, x**2 * y, x * y**2, y**3]
        return np.column_stack(cols)

    @classmethod
    def fit(cls, src, dst, order: int = 2) -> "Polynomial":
        s, d = _as_xy(src), _as_xy(dst)
        need = {1: 3, 2: 6, 3: 10}[order]
        if len(s) < need:
            raise ValueError(f"order-{order} polynomial needs >= {need} points")
        # Centre the data: raw UTM coordinates are ~1e6, and squaring them
        # destroys conditioning.
        mu = s.mean(axis=0)
        A = cls._design(s - mu, order)
        cx, *_ = np.linalg.lstsq(A, d[:, 0], rcond=None)
        cy, *_ = np.linalg.lstsq(A, d[:, 1], rcond=None)
        obj = cls(cx, cy, order)
        obj.mu = mu
        return obj

    def apply(self, pts) -> np.ndarray:
        p = _as_xy(pts)
        A = self._design(p - self.mu, self.order)
        return np.column_stack([A @ self.cx, A @ self.cy])


class ThinPlateSpline(_Base):
    """Thin-plate spline: exact interpolation, minimum bending energy.

    This is the classic 'rubber-sheeting' used by GIS analysts to force an old
    map onto modern control. ``smoothing`` > 0 relaxes exactness, which is
    almost always what you want with noisy survey control.
    """

    def __init__(self, ctrl=None, wx=None, wy=None, scale=1.0, mu=None):
        self.ctrl, self.wx, self.wy, self.scale, self.mu = ctrl, wx, wy, scale, mu

    @staticmethod
    def _kernel(r2: np.ndarray) -> np.ndarray:
        # U(r) = r^2 log(r); guard r = 0.
        out = np.zeros_like(r2)
        nz = r2 > 1e-12
        out[nz] = 0.5 * r2[nz] * np.log(r2[nz])
        return out

    @classmethod
    def fit(cls, src, dst, smoothing: float = 0.0) -> "ThinPlateSpline":
        s, d = _as_xy(src), _as_xy(dst)
        n = len(s)
        if n < 3:
            raise ValueError("TPS needs >= 3 control points")
        mu = s.mean(axis=0)
        scale = float(np.abs(s - mu).max()) or 1.0
        sc = (s - mu) / scale

        diff = sc[:, None, :] - sc[None, :, :]
        K = cls._kernel((diff ** 2).sum(axis=-1))
        if smoothing > 0:
            K = K + np.eye(n) * smoothing
        P = np.column_stack([np.ones(n), sc])
        L = np.zeros((n + 3, n + 3))
        L[:n, :n] = K
        L[:n, n:] = P
        L[n:, :n] = P.T

        rhs = np.zeros((n + 3, 2))
        rhs[:n] = d
        sol, *_ = np.linalg.lstsq(L, rhs, rcond=None)
        return cls(sc, sol[:, 0], sol[:, 1], scale, mu)

    def apply(self, pts) -> np.ndarray:
        p = (_as_xy(pts) - self.mu) / self.scale
        diff = p[:, None, :] - self.ctrl[None, :, :]
        K = self._kernel((diff ** 2).sum(axis=-1))
        P = np.column_stack([np.ones(len(p)), p])
        base = np.column_stack([P @ self.wx[-3:], P @ self.wy[-3:]])
        bend = np.column_stack([K @ self.wx[:-3], K @ self.wy[:-3]])
        return base + bend


def fit_best_transform(src, dst, max_rmse: float = 0.30):
    """Fit the least flexible transform that meets the accuracy target.

    Returns ``(model, name, rmse)``. Escalating only when necessary is the
    whole point: a similarity fit that already meets tolerance is preferable
    to a TPS that merely *looks* better because it interpolated the noise.
    """
    s, d = _as_xy(src), _as_xy(dst)
    attempts = []

    for name, ctor in (
        ("similarity", lambda: Similarity.fit(s, d)),
        ("affine", lambda: Affine.fit(s, d)),
        ("polynomial2", lambda: Polynomial.fit(s, d, order=2)),
        ("tps", lambda: ThinPlateSpline.fit(s, d, smoothing=1e-4)),
    ):
        try:
            model = ctor()
        except (ValueError, np.linalg.LinAlgError):
            continue
        err = model.rmse(s, d)
        attempts.append((name, model, err))
        if err <= max_rmse:
            return model, name, err

    if not attempts:
        raise ValueError("no transform could be fitted to the given points")
    name, model, err = min(attempts, key=lambda t: t[2])
    return model, name, err
