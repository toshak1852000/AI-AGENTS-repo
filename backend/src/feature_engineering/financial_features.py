"""
Financial feature generation: volatility, sector exposure, factor sensitivity, rolling stats.
"""
import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_VOLATILITY_WINDOW = 20
DEFAULT_ROLLING_WINDOWS = [5, 10, 20, 60]
FACTOR_NAMES = ["market", "small_cap", "value", "momentum", "oil", "gold", "bonds", "usd"]


def compute_volatility_indicators(
    returns: pd.Series,
    window: int = DEFAULT_VOLATILITY_WINDOW,
) -> dict[str, float]:
    """Compute volatility-based indicators (rolling std, annualized vol)."""
    if returns.empty or len(returns) < 2:
        return {"volatility_20d": 0.0, "volatility_annualized": 0.0}
    r = returns.dropna()
    if len(r) < window:
        window = max(2, len(r) // 2)
    vol = r.rolling(window, min_periods=2).std().iloc[-1]
    # Approximate annualized (252 trading days)
    vol_ann = float(vol * np.sqrt(252)) if not np.isnan(vol) else 0.0
    return {
        "volatility_20d": round(float(vol), 6) if not np.isnan(vol) else 0.0,
        "volatility_annualized": round(vol_ann, 6),
    }


def compute_rolling_statistics(
    series: pd.Series,
    windows: list[int] | None = None,
) -> dict[str, float]:
    """Compute rolling mean and std for given windows; return last values."""
    windows = windows or DEFAULT_ROLLING_WINDOWS
    result: dict[str, float] = {}
    for w in windows:
        if len(series) < w:
            continue
        result[f"rolling_mean_{w}"] = float(series.rolling(w).mean().iloc[-1])
        result[f"rolling_std_{w}"] = float(series.rolling(w).std().iloc[-1])
    return result


def compute_factor_risk_features(
    factor_returns: pd.DataFrame,
    factor_names: list[str] | None = None,
) -> dict[str, float]:
    """Compute per-factor volatility and correlation matrix summary (mean abs correlation)."""
    factors = factor_names or FACTOR_NAMES
    available = [c for c in factors if c in factor_returns.columns]
    if not available:
        return {}
    df = factor_returns[available].dropna()
    if df.empty:
        return {}
    vol = df.std()
    corr = df.corr()
    # Mean absolute off-diagonal correlation
    n = len(corr)
    off_diag = (corr.abs().sum().sum() - n) / max(1, n * (n - 1))
    result = {f"factor_vol_{c}": round(float(vol[c]), 6) for c in available}
    result["factor_corr_mean_abs"] = round(float(off_diag), 6)
    return result


def build_portfolio_feature_vector(
    total_exposure_pct: float,
    market_beta: float,
    scenario_severity: float,
    sector_concentration: float,
    top_holding_weight: float,
    n_holdings: float,
    market_volatility: float,
    oil_exposure: float,
    bond_exposure: float,
    regulatory_factor: float,
) -> dict[str, float]:
    """
    Build the risk model feature vector (aligns with risk_model.FEATURES).
    Used by risk engine and evaluation.
    """
    return {
        "total_exposure_pct": total_exposure_pct,
        "market_beta": market_beta,
        "scenario_severity": scenario_severity,
        "sector_concentration": sector_concentration,
        "top_holding_weight": top_holding_weight,
        "n_holdings": n_holdings,
        "market_volatility": market_volatility,
        "oil_exposure": oil_exposure,
        "bond_exposure": bond_exposure,
        "regulatory_factor": regulatory_factor,
    }
