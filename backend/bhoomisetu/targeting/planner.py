"""Greedy submodular selection of ground-truth survey locations.

The question this answers:

    Given a fixed survey budget, which K locations should a surveyor visit so
    that positional uncertainty across the *whole* city falls as far as
    possible?

This is the sensor-placement problem. Formally, with S the chosen set,

    F(S) = sum_i [ var(x_i | {}) - var(x_i | S) ]        (total variance reduction)

F is monotone and submodular in S -- each additional observation helps, but
helps less once nearby ground is already covered -- so the greedy algorithm is
guaranteed within a factor (1 - 1/e) ~ 63% of the optimal set, and the problem
is NP-hard to solve exactly. Method and bound: Krause, Singh & Guestrin,
*Near-Optimal Sensor Placements in Gaussian Processes*, JMLR 9 (2008).

Two properties make this practical:

* **Posterior variance does not depend on measured values**, only on where you
  observe. The entire plan can therefore be computed before anyone goes out.
* **The marginal gain has a closed form.** Adding candidate c to S gives

      var(x | S + c) = var(x | S) - cov(x, c | S)^2 / (var(c | S) + noise)

  so the gain for every candidate can be evaluated for every parcel in a
  single vectorised pass, with no iteration over candidates.

The output is deliberately shaped like a work order: ranked coordinates, the
marginal value of each, and the point at which further survey stops paying.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from bhoomisetu.targeting.uncertainty import UncertaintyField

__all__ = ["SurveyPoint", "SurveyPlan", "SurveyPlanner"]

# Tamil Nadu's official resurvey rate quoted to DoLR. Used only to express the
# plan in money; override per state.
RESURVEY_RATE_PER_SQKM = 56_725.0
# Indicative cost of establishing one GNSS/DGPS control point (crew, travel,
# observation time). Adjustable in the UI.
COST_PER_SURVEY_POINT = 5_750.0


@dataclass
class SurveyPoint:
    rank: int
    x: float
    y: float
    lon: float | None = None
    lat: float | None = None
    marginal_gain: float = 0.0          # variance removed by this point alone
    rmse_after: float = 0.0             # city-wide expected RMSE once surveyed
    rmse_delta: float = 0.0             # improvement this point contributes
    parcel_fid: str | None = None       # nearest parcel, for the field crew
    reason: str = ""

    def to_geojson(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {"type": "Point",
                         "coordinates": [self.lon if self.lon is not None else self.x,
                                         self.lat if self.lat is not None else self.y]},
            "properties": {
                "rank": self.rank, "marginal_gain": self.marginal_gain,
                "rmse_after_m": round(self.rmse_after, 4),
                "rmse_delta_m": round(self.rmse_delta, 4),
                "parcel_fid": self.parcel_fid, "reason": self.reason,
                "utm_x": self.x, "utm_y": self.y,
            },
        }


@dataclass
class SurveyPlan:
    points: list[SurveyPoint] = field(default_factory=list)
    rmse_before: float = 0.0
    rmse_after: float = 0.0
    n_parcels: int = 0
    area_sqkm: float = 0.0
    hyper: str = ""
    stopped_because: str = ""

    @property
    def improvement_pct(self) -> float:
        if self.rmse_before <= 0:
            return 0.0
        return 100.0 * (self.rmse_before - self.rmse_after) / self.rmse_before

    @property
    def plan_cost(self) -> float:
        return len(self.points) * COST_PER_SURVEY_POINT

    @property
    def full_resurvey_cost(self) -> float:
        return self.area_sqkm * RESURVEY_RATE_PER_SQKM

    def summary(self) -> str:
        return (
            f"SURVEY PLAN — {len(self.points)} points over "
            f"{self.area_sqkm:.1f} sq km ({self.n_parcels:,} parcels)\n"
            f"  GP: {self.hyper}\n"
            f"  expected city-wide RMSE  {self.rmse_before:.3f} m -> "
            f"{self.rmse_after:.3f} m  ({self.improvement_pct:+.1f}%)\n"
            f"  plan cost  Rs {self.plan_cost:,.0f}   vs full resurvey "
            f"Rs {self.full_resurvey_cost:,.0f}\n"
            f"  stopped: {self.stopped_because}"
        )

    def to_geojson(self) -> dict:
        return {"type": "FeatureCollection",
                "features": [p.to_geojson() for p in self.points]}

    def gain_curve(self) -> list[tuple[int, float]]:
        """(k, expected RMSE after k points) — the diminishing-returns curve."""
        return [(p.rank, p.rmse_after) for p in self.points]


class SurveyPlanner:
    """Greedy (1 - 1/e)-optimal selection of survey locations."""

    def __init__(self, field_model: UncertaintyField):
        if field_model.hyper is None:
            raise ValueError("UncertaintyField must be fitted first")
        self.f = field_model

    # ------------------------------------------------------------------
    def plan(self, parcel_xy: np.ndarray, candidate_xy: np.ndarray,
             k: int = 40, existing_xy: np.ndarray | None = None,
             min_gain_ratio: float = 0.002,
             min_separation: float = 25.0,
             parcel_fids: list[str] | None = None,
             area_sqkm: float | None = None) -> SurveyPlan:
        """Select up to ``k`` survey points.

        Parameters
        ----------
        parcel_xy:
            (N, 2) the locations whose uncertainty we care about -- parcel
            centroids. This is the *objective* set.
        candidate_xy:
            (M, 2) the locations a surveyor could actually occupy. Parcel
            corners are the right choice: they are physical, identifiable
            monuments a crew can find, unlike arbitrary grid points.
        existing_xy:
            Control already established (CORS stations, prior GT). Included in
            the conditioning set from the start, so the plan never recommends
            re-surveying ground that is already constrained.
        min_gain_ratio:
            Stop when a point's marginal gain falls below this fraction of the
            first point's. Prevents padding a plan with worthless visits.
        min_separation:
            Metres. Blocks near-duplicate recommendations. Submodularity
            already discourages clustering; this makes it explicit and
            survey-practical.
        """
        h = self.f.hyper
        X = np.atleast_2d(np.asarray(parcel_xy, dtype=float))
        C = np.atleast_2d(np.asarray(candidate_xy, dtype=float))
        n, m = len(X), len(C)

        if area_sqkm is None:
            span = np.ptp(X, axis=0)
            area_sqkm = float(span[0] * span[1]) / 1e6

        S = ([] if existing_xy is None or len(existing_xy) == 0
             else list(np.atleast_2d(np.asarray(existing_xy, dtype=float))))

        rmse_before = self.f.rmse(X, np.array(S) if S else None)
        plan = SurveyPlan(rmse_before=rmse_before, rmse_after=rmse_before,
                          n_parcels=n, area_sqkm=area_sqkm, hyper=str(h))

        # Precompute the static kernel blocks.
        K_XC = self.f._k(X, C, h)          # (n, m)
        chosen: list[int] = []
        first_gain = None
        stopped = f"reached k={k}"

        for step in range(1, k + 1):
            if S:
                Sarr = np.array(S)
                K_SS = self.f._k(Sarr, Sarr, h)
                K_SS[np.diag_indices_from(K_SS)] += h.noise_var + self.f.jitter
                c_f = cho_factor(K_SS, lower=True)
                K_SC = self.f._k(Sarr, C, h)            # (ns, m)
                K_XS = self.f._k(X, Sarr, h)            # (n, ns)
                A = cho_solve(c_f, K_SC)                # (ns, m)
                # cov(x, c | S) for every parcel/candidate pair
                cov = K_XC - K_XS @ A                   # (n, m)
                var_c = h.signal_var - np.einsum("ij,ij->j", K_SC, A)
            else:
                cov = K_XC
                var_c = np.full(m, h.signal_var)

            denom = np.maximum(var_c + h.noise_var, 1e-12)
            gains = np.einsum("ij,ij->j", cov, cov) / denom   # (m,)

            # Exclude already-chosen and anything too close to them.
            if chosen:
                taken = C[chosen]
                d2 = ((C[:, None, :] - taken[None, :, :]) ** 2).sum(axis=-1)
                gains[(d2.min(axis=1) < min_separation ** 2)] = -np.inf
            gains[chosen] = -np.inf

            best = int(np.argmax(gains))
            g = float(gains[best])
            if not np.isfinite(g) or g <= 0:
                stopped = "no candidate offers any further reduction"
                break
            if first_gain is None:
                first_gain = g
            elif g < first_gain * min_gain_ratio:
                stopped = (f"marginal gain fell below {min_gain_ratio:.1%} "
                           f"of the first point")
                break

            chosen.append(best)
            S.append(C[best])
            rmse_now = self.f.rmse(X, np.array(S))
            prev = plan.points[-1].rmse_after if plan.points else rmse_before

            plan.points.append(SurveyPoint(
                rank=step, x=float(C[best, 0]), y=float(C[best, 1]),
                marginal_gain=g, rmse_after=rmse_now,
                rmse_delta=prev - rmse_now,
                parcel_fid=(parcel_fids[int(np.argmin(
                    ((X - C[best]) ** 2).sum(axis=1)))] if parcel_fids else None),
                reason=self._reason(step, g, first_gain),
            ))
            plan.rmse_after = rmse_now

        plan.stopped_because = stopped
        return plan

    @staticmethod
    def _reason(step: int, gain: float, first: float) -> str:
        share = gain / first if first else 0.0
        if step == 1:
            return "highest-uncertainty region; anchors the whole sheet"
        if share > 0.5:
            return "large unconstrained area, far from existing control"
        if share > 0.15:
            return "fills a gap between established control points"
        return "marginal refinement"

    # ------------------------------------------------------------------
    @staticmethod
    def candidates_from_parcels(polygons, max_candidates: int = 2500,
                                seed: int = 0) -> np.ndarray:
        """Parcel corners as candidate survey locations.

        A surveyor needs a physical, identifiable point to occupy. A plot
        corner is a real monument; a grid node in the middle of a field is not.
        Corners are thinned to keep the candidate set tractable.
        """
        pts = []
        for g in polygons:
            if g is None or g.is_empty:
                continue
            try:
                pts.extend(list(g.exterior.coords)[:-1])
            except AttributeError:
                continue
        arr = np.array(pts, dtype=float)
        if len(arr) > max_candidates:
            rng = np.random.default_rng(seed)
            arr = arr[rng.choice(len(arr), max_candidates, replace=False)]
        return arr
