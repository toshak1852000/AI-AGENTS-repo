"""Unit tests for feature engineering."""
import numpy as np
import pandas as pd
import pytest

from src.feature_engineering.financial_features import (
    compute_volatility_indicators,
    compute_rolling_statistics,
    compute_factor_risk_features,
    build_portfolio_feature_vector,
)


def test_compute_volatility_indicators():
    r = pd.Series(np.random.randn(50) * 0.01)
    out = compute_volatility_indicators(r, window=20)
    assert "volatility_20d" in out
    assert "volatility_annualized" in out
    assert out["volatility_20d"] >= 0


def test_compute_rolling_statistics():
    s = pd.Series(np.cumsum(np.random.randn(100)))
    out = compute_rolling_statistics(s, windows=[5, 10])
    assert "rolling_mean_5" in out or "rolling_mean_10" in out


def test_compute_factor_risk_features():
    df = pd.DataFrame(np.random.randn(30, 8), columns=[
        "market", "small_cap", "value", "momentum", "oil", "gold", "bonds", "usd"
    ])
    out = compute_factor_risk_features(df)
    assert "factor_vol_market" in out or "factor_corr_mean_abs" in out


def test_build_portfolio_feature_vector():
    out = build_portfolio_feature_vector(
        0.5, 1.0, 0.7, 0.3, 0.2, 10.0, 0.02, 0.1, 0.15, 0.05
    )
    assert out["total_exposure_pct"] == 0.5
    assert out["market_beta"] == 1.0
    assert len(out) == 10
