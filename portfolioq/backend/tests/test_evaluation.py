"""Tests for evaluation metrics and reliability."""
import numpy as np
import pytest

from src.evaluation.metrics import forecasting_metrics, classification_metrics, risk_metrics_var_es
from src.evaluation.reliability import check_overfitting_ratio, check_train_test_drift, flag_unstable_predictions


def test_forecasting_metrics():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 2.0, 2.9])
    out = forecasting_metrics(y_true, y_pred)
    assert "rmse" in out
    assert "mae" in out
    assert "mape" in out


def test_classification_metrics():
    y_true = np.array([0, 1, 0, 1])
    y_pred = np.array([0, 1, 0, 0])
    out = classification_metrics(y_true, y_pred)
    assert "accuracy" in out
    assert "f1_weighted" in out


def test_check_overfitting_ratio():
    out = check_overfitting_ratio(0.95, 0.5, threshold=1.5)
    assert out["overfitting_suspected"] is True
    assert out["train_val_ratio"] > 1


def test_check_train_test_drift():
    train = np.random.randn(100)
    test = np.random.randn(100) + 2
    out = check_train_test_drift(train, test, psi_threshold=0.25)
    assert "drift_detected" in out
    assert "psi" in out


def test_flag_unstable_predictions():
    preds = np.array([0.5] * 5 + [0.9] * 5)
    out = flag_unstable_predictions(preds, window=5)
    assert "unstable" in out
    assert "stability_ratio" in out
