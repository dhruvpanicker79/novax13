"""Classification and calibration metrics.

Hand-implemented because ``scikit-learn`` is blocked by Application Control on
the target machine. All functions take plain numpy arrays.

Calibration gets as much attention here as accuracy, deliberately. The purpose
of this system is triage: an officer trusts the high-confidence matches and
reviews the rest. A model that is 95% accurate but claims 99% confidence on
everything is useless for triage, because there is no safe threshold. Expected
Calibration Error and the reliability curve are therefore first-class outputs,
not diagnostics.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "confusion", "precision_recall_f1", "roc_auc", "average_precision",
    "brier_score", "expected_calibration_error", "reliability_curve",
    "classification_report", "coverage_at_precision",
]


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    y_true = np.asarray(y_true).astype(bool)
    y_pred = np.asarray(y_pred).astype(bool)
    return {
        "tp": int((y_true & y_pred).sum()),
        "fp": int((~y_true & y_pred).sum()),
        "fn": int((y_true & ~y_pred).sum()),
        "tn": int((~y_true & ~y_pred).sum()),
    }


def precision_recall_f1(y_true, y_pred) -> dict[str, float]:
    c = confusion(y_true, y_pred)
    tp, fp, fn = c["tp"], c["fp"], c["fn"]
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": p, "recall": r, "f1": f1, **c}


def roc_auc(y_true, y_score) -> float:
    """Area under the ROC curve, computed via the rank-sum identity."""
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score, dtype=float)
    n_pos = int(y_true.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(y_score, kind="mergesort")
    ranks = np.empty(len(y_score), dtype=float)
    ranks[order] = np.arange(1, len(y_score) + 1)
    # Average ranks within tied score groups.
    s_sorted = y_score[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    return float((ranks[y_true == 1].sum() - n_pos * (n_pos + 1) / 2)
                 / (n_pos * n_neg))


def average_precision(y_true, y_score) -> float:
    """Area under the precision-recall curve (step interpolation)."""
    y_true = np.asarray(y_true).astype(int)
    order = np.argsort(-np.asarray(y_score, dtype=float), kind="mergesort")
    y = y_true[order]
    tp = np.cumsum(y)
    fp = np.cumsum(1 - y)
    prec = tp / np.maximum(tp + fp, 1)
    n_pos = y_true.sum()
    if n_pos == 0:
        return float("nan")
    rec = tp / n_pos
    return float(np.sum(np.diff(np.concatenate([[0.0], rec])) * prec))


def brier_score(y_true, y_prob) -> float:
    """Mean squared error of the probability estimates. Lower is better."""
    return float(np.mean((np.asarray(y_prob, dtype=float)
                          - np.asarray(y_true, dtype=float)) ** 2))


def reliability_curve(y_true, y_prob, n_bins: int = 10):
    """Bin predictions and report mean confidence vs observed frequency."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    rows = []
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        m = (y_prob >= lo) & (y_prob < hi if b < n_bins - 1 else y_prob <= hi)
        if m.sum() == 0:
            rows.append((lo, hi, 0, float("nan"), float("nan")))
        else:
            rows.append((lo, hi, int(m.sum()),
                         float(y_prob[m].mean()), float(y_true[m].mean())))
    return rows


def expected_calibration_error(y_true, y_prob, n_bins: int = 10) -> float:
    """ECE: sample-weighted mean gap between confidence and accuracy."""
    rows = reliability_curve(y_true, y_prob, n_bins)
    total = sum(r[2] for r in rows)
    if total == 0:
        return float("nan")
    return float(sum(r[2] * abs(r[3] - r[4]) for r in rows if r[2] > 0) / total)


def coverage_at_precision(y_true, y_prob, target_precision: float = 0.99):
    """Largest fraction auto-acceptable while holding a precision floor.

    This is the number that actually matters operationally: "what share of
    parcels can we finalise without human review, and still be right 99% of
    the time?" Returns ``(coverage, threshold, achieved_precision)``.
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob, dtype=float)
    order = np.argsort(-y_prob, kind="mergesort")
    y = y_true[order]
    tp = np.cumsum(y)
    prec = tp / np.arange(1, len(y) + 1)
    ok = np.where(prec >= target_precision)[0]
    if len(ok) == 0:
        return 0.0, 1.0, float("nan")
    k = int(ok[-1])
    return ((k + 1) / len(y), float(y_prob[order][k]), float(prec[k]))


def classification_report(y_true, y_prob, threshold: float = 0.5) -> dict:
    y_pred = np.asarray(y_prob, dtype=float) >= threshold
    out = precision_recall_f1(y_true, y_pred)
    out.update({
        "threshold": threshold,
        "roc_auc": roc_auc(y_true, y_prob),
        "avg_precision": average_precision(y_true, y_prob),
        "brier": brier_score(y_true, y_prob),
        "ece": expected_calibration_error(y_true, y_prob),
        "n": int(len(y_true)),
        "positives": int(np.asarray(y_true).sum()),
    })
    return out
