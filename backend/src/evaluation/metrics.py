"""
Evaluation metrics: RMSE, MAE, MAPE; Accuracy, F1, ROC-AUC; VaR/ES error.
"""
import logging
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    roc_auc_score,
    mean_squared_error,
    mean_absolute_error,
)

logger = logging.getLogger(__name__)


def forecasting_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """RMSE, MAE, MAPE for regression/forecasting."""
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    if not np.any(mask):
        return {"rmse": 0.0, "mae": 0.0, "mape": 0.0}
    yt, yp = y_true[mask], y_pred[mask]
    rmse = float(np.sqrt(mean_squared_error(yt, yp)))
    mae = float(mean_absolute_error(yt, yp))
    denom = np.abs(yt)
    denom[denom == 0] = np.nan
    mape = float(np.nanmean(np.abs((yt - yp) / denom)) * 100) if np.any(denom > 0) else 0.0
    return {"rmse": rmse, "mae": mae, "mape": mape}


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
    average: str = "weighted",
) -> dict[str, float]:
    """Accuracy, F1 (weighted), ROC-AUC (if y_proba provided, multiclass ovr)."""
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()
    out: dict[str, float] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_weighted": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
    }
    if y_proba is not None and len(np.unique(y_true)) > 1:
        try:
            out["roc_auc_ovr"] = float(roc_auc_score(y_true, y_proba, multi_class="ovr", average="weighted"))
        except Exception as e:
            logger.debug("roc_auc failed: %s", e)
    return out


def risk_metrics_var_es(
    returns: np.ndarray,
    var_historical: float,
    es_historical: float,
    confidence: float = 0.95,
) -> dict[str, float]:
    """
    Value-at-Risk and Expected Shortfall error vs historical.
    Returns absolute error of model VaR/ES vs empirical.
    """
    returns = np.asarray(returns).ravel()
    returns = returns[~np.isnan(returns)]
    if len(returns) < 10:
        return {"var_error": 0.0, "expected_shortfall_error": 0.0}
    alpha = 1 - confidence
    var_emp = float(np.percentile(returns, alpha * 100))
    tail = returns[returns <= var_emp]
    es_emp = float(tail.mean()) if len(tail) > 0 else var_emp
    return {
        "var_error": abs(var_historical - var_emp),
        "expected_shortfall_error": abs(es_historical - es_emp),
    }
