"""
Monitoring: data drift, model drift, prediction anomalies, risk threshold breaches.
"""
import logging
from typing import Any

import pandas as pd

from src.data_validation.drift import detect_data_drift

logger = logging.getLogger(__name__)

DEFAULT_PSI_THRESHOLD = 0.25
DEFAULT_RISK_CRITICAL = 0.8
DEFAULT_RISK_HIGH = 0.6


def check_data_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    psi_threshold: float = DEFAULT_PSI_THRESHOLD,
) -> dict[str, Any]:
    """Check for data drift between reference and current; return result and alert flag."""
    result = detect_data_drift(reference, current, psi_threshold=psi_threshold)
    result["alert"] = result["drift_detected"]
    return result


def check_model_drift(
    reference_predictions: pd.Series,
    current_predictions: pd.Series,
    psi_threshold: float = DEFAULT_PSI_THRESHOLD,
) -> dict[str, Any]:
    """Check for model/prediction distribution drift."""
    from src.data_validation.drift import compute_psi
    psi = compute_psi(reference_predictions, current_predictions)
    drift_detected = psi > psi_threshold
    return {
        "drift_detected": drift_detected,
        "psi": round(psi, 4),
        "psi_threshold": psi_threshold,
        "alert": drift_detected,
    }


def check_prediction_anomaly(
    predictions: list[float],
    lower_bound: float = 0.0,
    upper_bound: float = 1.0,
    anomaly_fraction_threshold: float = 0.1,
) -> dict[str, Any]:
    """Flag if too many predictions fall outside expected bounds."""
    preds = [p for p in predictions if p is not None]
    if not preds:
        return {"anomaly_detected": False, "anomaly_fraction": 0.0, "alert": False}
    outside = sum(1 for p in preds if p < lower_bound or p > upper_bound)
    frac = outside / len(preds)
    anomaly = frac >= anomaly_fraction_threshold
    return {
        "anomaly_detected": anomaly,
        "anomaly_fraction": round(frac, 4),
        "n_outside": outside,
        "alert": anomaly,
    }


def check_risk_threshold_breach(
    risk_score: float,
    critical_threshold: float = DEFAULT_RISK_CRITICAL,
    high_threshold: float = DEFAULT_RISK_HIGH,
) -> dict[str, Any]:
    """Check if risk score breaches critical or high threshold."""
    critical = risk_score >= critical_threshold
    high = risk_score >= high_threshold and not critical
    return {
        "breach_critical": critical,
        "breach_high": high,
        "risk_score": risk_score,
        "alert": critical or high,
    }
