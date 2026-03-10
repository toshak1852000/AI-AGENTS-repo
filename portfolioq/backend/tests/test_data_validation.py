"""Unit tests for data validation (schema, clean, drift)."""
import numpy as np
import pandas as pd
import pytest

from src.data_validation.schema import validate_price_schema, validate_factor_schema
from src.data_validation.clean import handle_missing, detect_outliers, clean_series
from src.data_validation.drift import compute_psi, detect_data_drift


def test_validate_price_schema():
    df = pd.DataFrame({"close_price": [1.0, 2.0]})
    valid, errs = validate_price_schema(df)
    assert valid is True
    assert len(errs) == 0

    df2 = pd.DataFrame({"open": [1.0]})
    valid2, errs2 = validate_price_schema(df2)
    assert valid2 is False
    assert any("close_price" in e for e in errs2)


def test_validate_factor_schema():
    cols = ["market", "small_cap", "value", "momentum", "oil", "gold", "bonds", "usd"]
    df = pd.DataFrame({c: np.random.randn(10) for c in cols})
    valid, errs = validate_factor_schema(df)
    assert valid is True

    df2 = pd.DataFrame({"market": [1.0]})
    valid2, errs2 = validate_factor_schema(df2)
    assert valid2 is False


def test_handle_missing():
    s = pd.Series([1.0, np.nan, 3.0])
    assert handle_missing(s, "drop").tolist() == [1.0, 3.0]
    assert handle_missing(s, "fill_zero").isna().sum() == 0


def test_detect_outliers():
    s = pd.Series([1, 2, 3, 4, 5, 100])
    mask = detect_outliers(s, "iqr")
    assert mask.iloc[-1] is False  # 100 is outlier
    assert mask.iloc[0] is True


def test_clean_series():
    s = pd.Series([1.0, np.nan, 2.0, 3.0])
    out = clean_series(s, missing_strategy="fill_zero")
    assert out.isna().sum() == 0


def test_compute_psi():
    exp = pd.Series(np.random.randn(100))
    act = pd.Series(np.random.randn(100) + 0.5)  # shifted
    psi = compute_psi(exp, act)
    assert psi >= 0


def test_detect_data_drift():
    ref = pd.DataFrame({"a": np.random.randn(100), "b": np.random.randn(100)})
    cur = pd.DataFrame({"a": np.random.randn(100) + 1, "b": np.random.randn(100)})
    result = detect_data_drift(ref, cur, psi_threshold=0.25)
    assert "drift_detected" in result
    assert "psi_values" in result
