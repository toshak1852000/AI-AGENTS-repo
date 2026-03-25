"""Risk assessment service: scoring, P&L stress-testing, and prioritization."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.models.exposure import RiskScore
from src.ml.risk_model import get_risk_model, FEATURES
from src.ml.opportunity_model import get_opportunity_model

logger = logging.getLogger(__name__)

SCENARIO_SEVERITY = {
    "market_shock": 0.9,
    "commodity_fluctuation": 0.7,
    "regulatory_change": 0.6,
    "geopolitical_event": 0.85,
    "interest_rate_change": 0.65,
    "currency_fluctuation": 0.55,
    "sector_decline": 0.75,
    "company_specific": 0.5,
}


def assess_risk(
    db: Session,
    portfolio_id: str,
    scenario: dict[str, Any],
    exposure_result: dict[str, Any],
    market_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute risk scores, stress P&L, and per-holding priorities.
    Persists to DB and returns structured result dict.
    """
    scenario_type = scenario.get("type", "market_shock")
    scenario_severity = SCENARIO_SEVERITY.get(scenario_type, 0.7)
    total_mv = float(exposure_result.get("total_exposure", 0) or 0)
    portfolio_pl = float(exposure_result.get("portfolio_pl_impact", 0) or 0)
    factor_betas = exposure_result.get("portfolio_factor_betas", {})
    company_exposures = exposure_result.get("company_exposures", [])

    # Build feature vector
    n_holdings = len(company_exposures)
    top_holding_weight = max((ce.get("exposure_pct", 0) for ce in company_exposures), default=0)
    sector_conc = _sector_concentration(exposure_result.get("sector_exposures", []))
    market_vol = market_data.get("factor_stats", {}).get("market", {}).get("volatility", 0.015)

    features = {
        "total_exposure_pct": min(1.0, total_mv / 1_000_000) if total_mv > 0 else 0.5,
        "market_beta": float(factor_betas.get("market", 1.0)),
        "scenario_severity": scenario_severity,
        "sector_concentration": sector_conc,
        "top_holding_weight": top_holding_weight,
        "n_holdings": float(n_holdings),
        "market_volatility": float(market_vol),
        "oil_exposure": float(abs(factor_betas.get("oil", 0))),
        "bond_exposure": float(abs(factor_betas.get("bonds", 0))),
        "regulatory_factor": 0.3 if scenario_type == "regulatory_change" else 0.05,
    }

    risk_pred = get_risk_model().predict_risk(features)
    risk_score = risk_pred["risk_score"]
    risk_level = risk_pred["risk_level"]

    # Prioritize holdings by |P&L impact|
    prioritized = sorted(
        company_exposures,
        key=lambda x: abs(x.get("scenario_pl_impact", 0)),
        reverse=True
    )

    # Per-holding opportunity signals
    opp_model = get_opportunity_model()
    holdings_with_signals = []
    for ce in prioritized[:20]:
        mv = float(ce.get("market_value", 0))
        pl = float(ce.get("scenario_pl_impact", 0))
        opp_features = {
            "risk_score": float(ce.get("risk_score", 0.5)),
            "total_exposure_pct": float(ce.get("exposure_pct", 0)),
            "market_beta": float(ce.get("factor_betas", {}).get("market", 1.0)),
            "sector_concentration": sector_conc,
            "pl_impact_pct": pl / mv if mv else 0,
            "volatility": float(market_vol),
            "momentum_signal": float(ce.get("factor_betas", {}).get("momentum", 0)),
            "value_signal": float(ce.get("factor_betas", {}).get("value", 0)),
        }
        signal = opp_model.score_holding(opp_features)
        holdings_with_signals.append({**ce, **signal})

    result = {
        "portfolio_id": portfolio_id,
        "scenario_id": scenario.get("id", ""),
        "scenario_type": scenario_type,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_probabilities": risk_pred.get("probabilities", {}),
        "pl_impact": portfolio_pl,
        "pl_impact_pct": round(portfolio_pl / total_mv * 100, 4) if total_mv else 0,
        "total_market_value": total_mv,
        "features_used": features,
        "prioritized_holdings": holdings_with_signals,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Persist to DB
    try:
        run_id = scenario.get("run_id", "")
        db_row = RiskScore(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            scenario_id=scenario.get("id") or None,
            run_id=run_id or None,
            score=risk_score,
            risk_level=risk_level,
            pl_impact=portfolio_pl,
            factors=features,
            model_version="xgb_v1",
        )
        db.add(db_row)
        db.commit()
        result["risk_score_id"] = db_row.id
    except Exception as exc:
        logger.warning("Could not persist risk score: %s", exc)
        db.rollback()

    return result


def _sector_concentration(sector_exposures: list[dict]) -> float:
    if not sector_exposures:
        return 0.5
    exposures = [s.get("exposure_pct", 0) for s in sector_exposures]
    if not exposures:
        return 0.5
    max_exp = max(exposures)
    hhi = sum(e ** 2 for e in exposures)
    return float(min(1.0, (max_exp + hhi) / 2))
