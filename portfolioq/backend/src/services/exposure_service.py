"""Exposure calculation service using the factor model."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.config.constants import RiskLevel, RISK_SCORE_THRESHOLDS
from src.models.exposure import Exposure
from src.ml.factor_model import get_factor_model

logger = logging.getLogger(__name__)


def calculate_exposure(
    db: Session,
    portfolio_id: str,
    portfolio_name: str,
    holdings: list[dict[str, Any]],
    scenario: dict[str, Any],
    market_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute company- and sector-level exposure and sensitivity for a portfolio under a scenario.
    Persists result to DB and returns structured dict.
    """
    scenario_type = scenario.get("type", "market_shock")
    current_prices = market_data.get("current_prices", {})

    # Enrich holdings with latest prices
    enriched = []
    for h in holdings:
        sym = h["symbol"]
        price = current_prices.get(sym) or float(h.get("current_price") or h.get("average_price", 0))
        enriched.append({**h, "current_price": price})

    fm = get_factor_model()
    sensitivity = fm.portfolio_sensitivity(enriched, scenario_type)

    total_mv = sensitivity["total_market_value"]

    # Company-level exposure
    company_exposures = []
    for h_sens in sensitivity["holdings"]:
        sym = h_sens["symbol"]
        mv = h_sens["market_value"]
        exposure_pct = mv / total_mv if total_mv else 0
        risk_raw = (abs(h_sens["scenario_pl_impact"]) / mv) if mv else 0
        risk_score = min(1.0, risk_raw * 8)

        company_exposures.append({
            "symbol": sym,
            "market_value": mv,
            "exposure_pct": round(exposure_pct, 4),
            "scenario_pl_impact": h_sens["scenario_pl_impact"],
            "factor_betas": h_sens["factor_betas"],
            "risk_score": round(risk_score, 4),
        })

    # Sector-level aggregation
    sector_map: dict[str, dict] = {}
    for ce, h in zip(company_exposures, enriched):
        sector = h.get("sector") or "Unknown"
        if sector not in sector_map:
            sector_map[sector] = {"sector": sector, "market_value": 0, "pl_impact": 0, "symbols": []}
        sector_map[sector]["market_value"] += ce["market_value"]
        sector_map[sector]["pl_impact"] += ce["scenario_pl_impact"]
        sector_map[sector]["symbols"].append(ce["symbol"])

    sector_exposures = []
    for sec, sd in sector_map.items():
        sector_exposures.append({
            "sector": sec,
            "market_value": round(sd["market_value"], 2),
            "exposure_pct": round(sd["market_value"] / total_mv, 4) if total_mv else 0,
            "scenario_pl_impact": round(sd["pl_impact"], 2),
            "symbols": sd["symbols"],
        })

    portfolio_risk_score = sensitivity["sensitivity_score"]
    risk_level = _score_to_level(portfolio_risk_score)

    result = {
        "portfolio_id": portfolio_id,
        "portfolio_name": portfolio_name,
        "scenario_id": scenario.get("id", ""),
        "scenario_type": scenario_type,
        "total_exposure": total_mv,
        "total_exposure_pct": 1.0,
        "portfolio_pl_impact": sensitivity["portfolio_pl_impact"],
        "portfolio_return_pct": sensitivity["portfolio_return_pct"],
        "portfolio_factor_betas": sensitivity["portfolio_factor_betas"],
        "sensitivity_score": sensitivity["sensitivity_score"],
        "risk_score": round(portfolio_risk_score, 4),
        "risk_level": risk_level,
        "company_exposures": company_exposures,
        "sector_exposures": sector_exposures,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Persist to DB
    try:
        run_id = scenario.get("run_id", "")
        db_row = Exposure(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            scenario_id=scenario.get("id") or None,
            run_id=run_id or None,
            total_exposure=total_mv,
            risk_score=portfolio_risk_score,
            company_exposures=company_exposures,
            sector_exposures=sector_exposures,
            factor_exposures=sensitivity["portfolio_factor_betas"],
            sensitivity_scores={"sensitivity_score": sensitivity["sensitivity_score"]},
        )
        db.add(db_row)
        db.commit()
        result["exposure_id"] = db_row.id
    except Exception as exc:
        logger.warning("Could not persist exposure to DB: %s", exc)
        db.rollback()

    return result


def _score_to_level(score: float) -> str:
    for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
        if score >= RISK_SCORE_THRESHOLDS[level]:
            return level.value
    return RiskLevel.LOW.value
