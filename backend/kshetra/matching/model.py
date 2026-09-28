"""The parcel-matching model.

A gradient-boosted decision tree over the pairwise features, followed by
isotonic calibration.

Why a GBDT and not a neural network: the input is ~29 heterogeneous tabular
features with strong monotone structure and heavy interaction (IoU matters far
more when the candidate count is low; name similarity matters far more when
IoU is ambiguous). Boosted trees are the right tool for that shape of problem,
they train in seconds on a laptop, and -- importantly for a land-administration
audit trail -- the decision path for any individual parcel can be printed and
defended.

Why calibration is a separate stage: raw GBDT margins pushed through a sigmoid
are systematically overconfident. Isotonic regression on a held-out split maps
them onto frequencies that actually hold, which is what makes the confidence
score usable as a triage threshold rather than decoration.

The model is trained on synthetic pairs whose correct answer is known, then
applied to unseen data. Splits are made *by source parcel*, never by pair, so
a parcel's candidates cannot straddle train and test.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import xgboost as xgb
from scipy.optimize import isotonic_regression

from kshetra.evaluation.metrics import classification_report
from kshetra.matching.features import FEATURE_NAMES

__all__ = ["ParcelMatcher", "group_train_test_split"]


def group_train_test_split(groups: np.ndarray, test_frac: float = 0.3,
                           seed: int = 0):
    """Split pair indices by group so no group spans both sides.

    ``groups`` is the source-parcel index for each candidate pair. Splitting
    on pairs instead would leak: two candidates for the same parcel are highly
    correlated, and the model would be scored on information it had seen.
    """
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    rng.shuffle(uniq)
    n_test = int(len(uniq) * test_frac)
    test_groups = set(uniq[:n_test].tolist())
    is_test = np.array([g in test_groups for g in groups])
    return ~is_test, is_test


@dataclass
class _Isotonic:
    """Monotone probability calibrator fitted on held-out predictions."""
    x: np.ndarray
    y: np.ndarray

    def __call__(self, p: np.ndarray) -> np.ndarray:
        return np.interp(np.asarray(p, dtype=float), self.x, self.y)

    def to_dict(self):
        return {"x": self.x.tolist(), "y": self.y.tolist()}

    @classmethod
    def from_dict(cls, d):
        return cls(np.array(d["x"]), np.array(d["y"]))


class ParcelMatcher:
    """Learned pairwise matcher with calibrated confidence output."""

    DEFAULT_PARAMS = {
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "max_depth": 6,
        "eta": 0.08,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 4,
        "lambda": 1.2,
        "verbosity": 0,
        "nthread": 4,
    }

    def __init__(self, params: dict | None = None, n_rounds: int = 320):
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self.n_rounds = n_rounds
        self.booster: xgb.Booster | None = None
        self.calibrator: _Isotonic | None = None
        self.feature_names = list(FEATURE_NAMES)
        self.train_report: dict | None = None

    # --- training ---------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray, groups: np.ndarray,
            calib_frac: float = 0.25, seed: int = 0, verbose: bool = True):
        """Train the booster, then fit the calibrator on a held-out slice.

        The calibration slice is carved out of the *training* data, so the
        evaluation split stays genuinely untouched.
        """
        fit_mask, calib_mask = group_train_test_split(groups, calib_frac, seed)

        dtrain = xgb.DMatrix(X[fit_mask], label=y[fit_mask],
                             feature_names=self.feature_names)
        dcalib = xgb.DMatrix(X[calib_mask], label=y[calib_mask],
                             feature_names=self.feature_names)

        # Positives are rare (one true match among many candidates), so
        # rebalance rather than let the model predict "no" for everything.
        n_pos = max(int(y[fit_mask].sum()), 1)
        n_neg = max(int((1 - y[fit_mask]).sum()), 1)
        params = {**self.params, "scale_pos_weight": n_neg / n_pos}

        self.booster = xgb.train(
            params, dtrain, num_boost_round=self.n_rounds,
            evals=[(dtrain, "train"), (dcalib, "calib")],
            early_stopping_rounds=40, verbose_eval=50 if verbose else False,
        )

        raw = self.booster.predict(dcalib)
        self._fit_calibrator(raw, y[calib_mask])
        self.train_report = classification_report(y[calib_mask],
                                                  self.calibrator(raw))
        return self

    def _fit_calibrator(self, p_raw: np.ndarray, y: np.ndarray) -> None:
        """Isotonic regression: the monotone map from score to frequency."""
        order = np.argsort(p_raw, kind="mergesort")
        xs = p_raw[order]
        ys = y[order].astype(float)
        fitted = isotonic_regression(ys).x
        # Collapse duplicate x values so np.interp stays well-defined.
        xs_u, idx = np.unique(xs, return_index=True)
        self.calibrator = _Isotonic(xs_u, fitted[idx])

    # --- inference --------------------------------------------------------
    def predict_raw(self, X: np.ndarray) -> np.ndarray:
        if self.booster is None:
            raise RuntimeError("model is not trained")
        d = xgb.DMatrix(X, feature_names=self.feature_names)
        return self.booster.predict(d)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Calibrated probability that a candidate pair is a true match."""
        raw = self.predict_raw(X)
        return self.calibrator(raw) if self.calibrator else raw

    # --- interpretability -------------------------------------------------
    def feature_importance(self, kind: str = "gain") -> list[tuple[str, float]]:
        if self.booster is None:
            raise RuntimeError("model is not trained")
        score = self.booster.get_score(importance_type=kind)
        total = sum(score.values()) or 1.0
        ranked = sorted(score.items(), key=lambda kv: -kv[1])
        return [(k, v / total) for k, v in ranked]

    def explain_pair(self, x: np.ndarray, top: int = 6) -> list[tuple[str, float]]:
        """Per-decision explanation via SHAP contributions.

        Returns the features that pushed this single pair toward or away from
        a match. This is what populates the evidence panel an officer sees
        before approving a flagged parcel.
        """
        if self.booster is None:
            raise RuntimeError("model is not trained")
        d = xgb.DMatrix(x.reshape(1, -1), feature_names=self.feature_names)
        contribs = self.booster.predict(d, pred_contribs=True)[0]
        pairs = list(zip(self.feature_names + ["_bias"], contribs))
        pairs.sort(key=lambda kv: -abs(kv[1]))
        return pairs[:top]

    # --- persistence ------------------------------------------------------
    def save(self, path: str) -> None:
        if self.booster is None:
            raise RuntimeError("model is not trained")
        self.booster.save_model(path + ".ubj")
        meta = {
            "feature_names": self.feature_names,
            "params": self.params,
            "calibrator": self.calibrator.to_dict() if self.calibrator else None,
            "train_report": self.train_report,
        }
        with open(path + ".meta.json", "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=1, default=float)

    @classmethod
    def load(cls, path: str) -> "ParcelMatcher":
        with open(path + ".meta.json", encoding="utf-8") as fh:
            meta = json.load(fh)
        obj = cls(params=meta["params"])
        obj.feature_names = meta["feature_names"]
        obj.booster = xgb.Booster()
        obj.booster.load_model(path + ".ubj")
        if meta.get("calibrator"):
            obj.calibrator = _Isotonic.from_dict(meta["calibrator"])
        obj.train_report = meta.get("train_report")
        return obj
