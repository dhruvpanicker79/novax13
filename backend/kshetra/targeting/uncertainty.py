"""Gaussian-process model of the residual positional-error field.

After coarse georeferencing, a legacy cadastral layer still carries error that
is *not* random per parcel. It is spatially correlated: paper shrinkage, sheet
joins and scanner distortion all deform whole neighbourhoods together. Two
parcels ten metres apart are wrong in almost the same direction and by almost
the same amount.

That correlation is precisely what makes survey planning possible. If errors
were independent, the only way to fix N parcels would be to survey N parcels,
and there would be nothing to optimise. Because they are correlated, one
well-placed GNSS observation constrains a whole neighbourhood -- and *where*
you place it matters enormously.

So we model the residual field as a Gaussian process

    r(x) ~ GP(0, k(x, x'))      k(x, x') = sf2 * exp(-||x - x'||^2 / 2l^2)

with observation noise sn2. Hyperparameters are fitted by maximising the log
marginal likelihood on the residuals we actually observed at matched parcels,
so the lengthscale is learned from the data rather than assumed.

The quantity the planner cares about is the posterior variance, which has the
property that makes everything else work: **it depends only on *where* you
observe, not on what you measure.** Variance reduction can therefore be
computed before any surveyor leaves the office.
"""
from __future__ import annotations

from dataclasses import dataclass

from typing import Sequence

import numpy as np
from scipy.optimize import minimize
from scipy.linalg import cho_factor, cho_solve

__all__ = ["UncertaintyField"]


@dataclass
class GPHyper:
    lengthscale: float      # metres over which errors stay correlated
    signal_var: float       # sf2, variance of the error field (m^2)
    noise_var: float        # sn2, per-observation noise (m^2)

    def __str__(self) -> str:
        return (f"lengthscale={self.lengthscale:.1f}m  "
                f"signal_sd={np.sqrt(self.signal_var):.3f}m  "
                f"noise_sd={np.sqrt(self.noise_var):.3f}m")


class UncertaintyField:
    """Posterior variance of the residual error field over an AOI."""

    def __init__(self, jitter: float = 1e-8, prediction_scale: float = 1.0):
        self.hyper: GPHyper | None = None
        self.train_xy: np.ndarray | None = None
        self.jitter = jitter
        #: Multiplier applied to predicted RMSE, measured against achieved
        #: results on a held-out city. See :meth:`calibrate_prediction`.
        self.prediction_scale = prediction_scale
        self.calibration_note = "uncalibrated"

    # --- kernel ----------------------------------------------------------
    @staticmethod
    def _sqdist(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Pairwise squared euclidean distance, (na, nb)."""
        a2 = (a ** 2).sum(axis=1)[:, None]
        b2 = (b ** 2).sum(axis=1)[None, :]
        d2 = a2 + b2 - 2.0 * (a @ b.T)
        return np.maximum(d2, 0.0)

    def _k(self, a: np.ndarray, b: np.ndarray, h: GPHyper) -> np.ndarray:
        return h.signal_var * np.exp(
            -self._sqdist(a, b) / (2.0 * h.lengthscale ** 2))

    # --- fitting ---------------------------------------------------------
    def fit(self, xy: np.ndarray, residuals: np.ndarray,
            max_train: int = 600, seed: int = 0) -> "UncertaintyField":
        """Fit hyperparameters to observed residuals.

        Parameters
        ----------
        xy:
            (N, 2) projected coordinates (metres) where residuals were observed
            -- in practice the centroids of confidently matched parcels.
        residuals:
            (N,) or (N, 2) displacement. A 2-D input is treated as two
            independent draws from the same field, which is the usual
            assumption for isotropic map distortion and doubles the effective
            sample size.
        max_train:
            Hyperparameter fitting is O(n^3); subsample above this. The
            lengthscale is a smooth global property, so a few hundred points
            estimate it perfectly well.
        """
        xy = np.asarray(xy, dtype=float)
        r = np.asarray(residuals, dtype=float)
        if r.ndim == 1:
            r = r[:, None]

        if len(xy) > max_train:
            rng = np.random.default_rng(seed)
            idx = rng.choice(len(xy), max_train, replace=False)
            xy_f, r_f = xy[idx], r[idx]
        else:
            xy_f, r_f = xy, r

        # Sensible starting point: lengthscale ~ 1/6 of the AOI span, signal
        # variance ~ the empirical variance of the residuals.
        span = float(np.ptp(xy_f, axis=0).max()) or 100.0
        emp_var = float(r_f.var()) or 1.0
        x0 = np.log([span / 6.0, emp_var, max(emp_var * 0.05, 1e-4)])

        def nll(theta):
            l, sf2, sn2 = np.exp(theta)
            h = GPHyper(l, sf2, sn2)
            K = self._k(xy_f, xy_f, h)
            K[np.diag_indices_from(K)] += sn2 + self.jitter
            try:
                c, low = cho_factor(K, lower=True)
            except np.linalg.LinAlgError:
                return 1e12
            logdet = 2.0 * np.log(np.diag(c)).sum()
            total = 0.0
            for d in range(r_f.shape[1]):
                y = r_f[:, d]
                alpha = cho_solve((c, low), y)
                total += 0.5 * (y @ alpha) + 0.5 * logdet
            return float(total)

        res = minimize(nll, x0, method="Nelder-Mead",
                       options=dict(maxiter=400, xatol=1e-3, fatol=1e-3))
        l, sf2, sn2 = np.exp(res.x)
        # Guard against degenerate fits on small or near-constant samples.
        l = float(np.clip(l, 5.0, span * 2))
        sf2 = float(max(sf2, 1e-6))
        sn2 = float(np.clip(sn2, 1e-6, sf2))
        self.hyper = GPHyper(l, sf2, sn2)
        self.train_xy = xy
        return self

    def set_hyper(self, lengthscale: float, signal_var: float,
                  noise_var: float) -> "UncertaintyField":
        """Set hyperparameters directly (for tests or expert override)."""
        self.hyper = GPHyper(lengthscale, signal_var, noise_var)
        return self

    # --- posterior -------------------------------------------------------
    def prior_variance(self, n: int | None = None) -> float:
        """Variance before any observation: just the signal variance."""
        self._require()
        return self.hyper.signal_var

    def posterior_variance(self, query_xy: np.ndarray,
                           observed_xy: np.ndarray | None) -> np.ndarray:
        """Posterior variance at ``query_xy`` given observations at ``observed_xy``.

        Note what is absent: the observed *values*. Posterior variance in a GP
        depends only on the observation locations, which is exactly why a
        survey plan can be optimised before the survey happens.
        """
        self._require()
        h = self.hyper
        q = np.atleast_2d(np.asarray(query_xy, dtype=float))
        if observed_xy is None or len(observed_xy) == 0:
            return np.full(len(q), h.signal_var)

        s = np.atleast_2d(np.asarray(observed_xy, dtype=float))
        Kss = self._k(s, s, h)
        Kss[np.diag_indices_from(Kss)] += h.noise_var + self.jitter
        Kqs = self._k(q, s, h)
        c, low = cho_factor(Kss, lower=True)
        v = cho_solve((c, low), Kqs.T)              # (ns, nq)
        var = h.signal_var - np.einsum("ij,ji->i", Kqs, v)
        return np.maximum(var, 0.0)

    def posterior_sd(self, query_xy, observed_xy=None) -> np.ndarray:
        """Positional standard deviation in metres."""
        return np.sqrt(self.posterior_variance(query_xy, observed_xy))

    def posterior_mean(self, query_xy, observed_xy, observed_values) -> np.ndarray:
        """GP posterior mean — the correction the variance actually describes.

        This matters more than it looks. The planner reports the posterior
        *variance* that will remain after surveying a set of points. If the
        correction is then applied with a different interpolator (a thin-plate
        spline, say), the predicted and achieved errors describe two different
        estimators and will not agree — the prediction looks optimistic
        because it is answering a question nobody asked.

        Correcting with the posterior mean of the same GP closes that gap:
        predicted variance and achieved residual are now the same model.

        This is ordinary kriging, and unlike an exact-interpolating spline it
        handles observation noise properly: with ``noise_var > 0`` it does not
        force the surface through noisy control, which is the correct
        behaviour for real GNSS measurements.
        """
        self._require()
        h = self.hyper
        q = np.atleast_2d(np.asarray(query_xy, dtype=float))
        s = np.atleast_2d(np.asarray(observed_xy, dtype=float))
        y = np.asarray(observed_values, dtype=float)
        if y.ndim == 1:
            y = y[:, None]
        if len(s) == 0:
            return np.zeros((len(q), y.shape[1]))

        Kss = self._k(s, s, h)
        Kss[np.diag_indices_from(Kss)] += h.noise_var + self.jitter
        c, low = cho_factor(Kss, lower=True)
        alpha = cho_solve((c, low), y)          # (ns, d)
        Kqs = self._k(q, s, h)
        return Kqs @ alpha

    def rmse(self, query_xy, observed_xy=None, include_noise: bool = True) -> float:
        """Expected positional RMSE over the query set, in metres.

        The field is modelled per-axis, so 2-D error combines two independent
        components: RMSE_2d = sqrt(2) * sd_per_axis.

        ``include_noise`` matters, and defaulting it to True fixes a real
        error. :meth:`posterior_variance` describes the *latent field* — the
        smooth, spatially correlated part that more control points genuinely
        remove. It does not include the per-parcel noise term, which is
        digitising jitter, vertex decimation and boundary ambiguity. That part
        is independent between parcels, so no amount of survey control removes
        any of it.

        Reporting the latent variance alone lets the planner promise an
        accuracy below its own noise floor, which is not achievable and will
        be contradicted the moment anyone checks.
        """
        var = self.posterior_variance(query_xy, observed_xy)
        if include_noise:
            var = var + self.hyper.noise_var
        return float(np.sqrt(2.0 * var.mean()) * self.prediction_scale)

    def calibrate_prediction(self, pairs: Sequence[tuple[float, float]]
                             ) -> float:
        """Fit the prediction scale from measured (predicted, achieved) pairs.

        Maximum-likelihood hyperparameters systematically under-attribute
        variance to the noise term here: the fitted per-parcel scatter comes
        out well below what is actually observed, so the raw prediction is
        optimistic by a roughly constant factor. Because the factor *is*
        roughly constant across plan sizes, it is a scale error rather than a
        structural one, and measuring it is legitimate.

        The discipline is the same one the matcher uses for its probabilities:
        fit the correction on one city, apply it to another, and report both
        numbers so the correction is visible rather than buried.
        """
        arr = np.array([(p, a) for p, a in pairs if p > 0 and np.isfinite(a)])
        if len(arr) == 0:
            return self.prediction_scale
        ratios = arr[:, 1] / arr[:, 0]
        self.prediction_scale = float(np.median(ratios))
        self.calibration_note = (
            f"scale {self.prediction_scale:.3f} from {len(arr)} held-out "
            f"plans (ratios {ratios.min():.2f}-{ratios.max():.2f})")
        return self.prediction_scale

    def irreducible_rmse(self) -> float:
        """The floor: positional RMSE that survey control cannot reduce.

        Worth quoting alongside any plan. It is the honest answer to "why not
        just survey more points?" — beyond this, extra control buys nothing
        because the remaining error is independent per parcel.
        """
        self._require()
        return float(np.sqrt(2.0 * self.hyper.noise_var))

    def _require(self):
        if self.hyper is None:
            raise RuntimeError("UncertaintyField is not fitted")
