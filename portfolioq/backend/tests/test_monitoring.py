"""Tests for monitoring (drift, risk breach)."""
import pandas as pd
import pytest

from src.monitoring import check_data_drift, check_risk_threshold_breach, check_prediction_anomaly


def test_check_risk_threshold_breach():
    out = check_risk_threshold_breach(0.85, critical_threshold=0.8, high_threshold=0.6)
    assert out["breach_critical"] is True
    assert out["alert"] is True

    out2 = check_risk_threshold_breach(0.5)
    assert out2["breach_critical"] is False


def test_check_prediction_anomaly():
    out = check_prediction_anomaly([0.1, 0.2, 1.5], upper_bound=1.0, anomaly_fraction_threshold=0.1)
    assert out["anomaly_detected"] is True
    assert out["n_outside"] >= 1


def test_check_data_drift():
    ref = pd.DataFrame({"x": [1, 2, 3] * 10, "y": [4, 5, 6] * 10})
    cur = pd.DataFrame({"x": [10, 20, 30] * 10, "y": [4, 5, 6] * 10})
    result = check_data_drift(ref, cur, psi_threshold=0.25)
    assert "drift_detected" in result
    assert "alert" in result
