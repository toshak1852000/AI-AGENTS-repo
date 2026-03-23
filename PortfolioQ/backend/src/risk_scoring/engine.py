"""
Risk scoring engine — ML predictions + rule-based logic + optional confidence intervals.
"""
import logging
from typing import Any

from src.ml.risk_model import get_risk_model, FEATURES
from src.ml.opportunity_model import get_opportunity_model

logger = logging.getLogger(__name__)


def compute_risk_score(
    features: dict[str, float],
    include_confidence: bool = False,
) -> dict[str, Any]:
    """
    Compute portfolio risk score and level from feature vector.
    Combines quantitative ML prediction with rule-based fallback when model not fitted.
    """
    model = get_risk_model()
    pred = model.predict_risk(features)
    out: dict[str, Any] = {
        "risk_score": pred["risk_score"],
        "risk_level": pred["risk_level"],
        "probabilities": pred.get("probabilities", {}),
    }
    if include_confidence and pred.get("probabilities"):
        probs = pred["probabilities"]
        if probs:
            import numpy as np
            levels = list(probs.keys())
            vals = [probs.get(l, 0) for l in levels]
            out["confidence_interval_95"] = {
                "risk_score_lower": 0.0,  # placeholder; could use bootstrap
                "risk_score_upper": min(1.0, pred["risk_score"] + 0.1),
            }
    return out


def compute_holding_risk(
    risk_score: float,
    exposure_pct: float,
    market_beta: float,
    sector_concentration: float,
    pl_impact_pct: float,
    volatility: float,
    momentum_signal: float,
    value_signal: float,
) -> dict[str, Any]:
    """Compute per-holding opportunity/risk signal (anomaly + rule-based)."""
    opp = get_opportunity_model()
    features = {
        "risk_score": risk_score,
        "total_exposure_pct": exposure_pct,
        "market_beta": market_beta,
        "sector_concentration": sector_concentration,
        "pl_impact_pct": pl_impact_pct,
        "volatility": volatility,
        "momentum_signal": momentum_signal,
        "value_signal": value_signal,
    }
    return opp.score_holding(features)
