"""
Reliability and hallucination controls: overfitting detection, data leakage, train/test drift, unstable predictions.
"""
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def check_overfitting_ratio(
    train_metric: float,
    val_metric: float,
    threshold: float = 1.5,
) -> dict[str, Any]:
    """
    Flag if train metric is much better than val (possible overfitting).
    Returns {overfitting_suspected: bool, ratio: float}.
    """
    if val_metric == 0:
        ratio = float("inf") if train_metric > 0 else 1.0
    else:
        ratio = abs(train_metric / val_metric)
    return {
        "overfitting_suspected": ratio > threshold,
        "train_val_ratio": round(ratio, 4),
        "threshold": threshold,
    }


def check_train_test_drift(
    train_values: np.ndarray,
    test_values: np.ndarray,
    psi_threshold: float = 0.25,
) -> dict[str, Any]:
    """Simple drift check via distribution difference (KS-like). Use data_validation.drift for PSI."""
    from src.data_validation.drift import compute_psi
    t = np.asarray(train_values).ravel()
    v = np.asarray(test_values).ravel()
    psi = compute_psi(
        __import__("pandas").Series(t),
        __import__("pandas").Series(v),
    )
    return {
        "drift_detected": psi > psi_threshold,
        "psi": round(psi, 4),
        "psi_threshold": psi_threshold,
    }


def flag_unstable_predictions(
    predictions: np.ndarray,
    window: int = 5,
    stability_ratio_threshold: float = 0.8,
) -> dict[str, Any]:
    """
    Flag if predictions vary too much in a rolling window (e.g. high variance).
    Returns {unstable: bool, std: float, stability_ratio: float}.
    """
    preds = np.asarray(predictions).ravel()
    if len(preds) < window:
        return {"unstable": False, "std": 0.0, "stability_ratio": 1.0}
    std = float(np.std(preds))
    # Compare recent window std to full std; if recent is much higher, unstable
    recent = preds[-window:]
    recent_std = float(np.std(recent))
    stability_ratio = (1.0 - min(1.0, recent_std / (std + 1e-10)))
    return {
        "unstable": stability_ratio < stability_ratio_threshold,
        "std": round(std, 6),
        "stability_ratio": round(stability_ratio, 4),
    }
