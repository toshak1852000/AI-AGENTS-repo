"""Exposure calculation endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.exposure import Exposure, RiskScore

router = APIRouter()


@router.get("/portfolio/{portfolio_id}")
def get_portfolio_exposure(portfolio_id: str, scenario_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get latest exposure for a portfolio (optionally filtered by scenario)."""
    q = db.query(Exposure).filter(Exposure.portfolio_id == portfolio_id)
    if scenario_id:
        q = q.filter(Exposure.scenario_id == scenario_id)
    rows = q.order_by(Exposure.created_at.desc()).limit(10).all()
    return [
        {
            "id": r.id, "portfolio_id": r.portfolio_id, "scenario_id": r.scenario_id,
            "total_exposure": float(r.total_exposure or 0),
            "risk_score": float(r.risk_score or 0),
            "company_exposures": r.company_exposures,
            "sector_exposures": r.sector_exposures,
            "factor_exposures": r.factor_exposures,
            "sensitivity_scores": r.sensitivity_scores,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/scenario/{scenario_id}")
def get_scenario_exposure(scenario_id: str, db: Session = Depends(get_db)):
    rows = db.query(Exposure).filter(Exposure.scenario_id == scenario_id).order_by(
        Exposure.created_at.desc()
    ).limit(20).all()
    return [
        {
            "id": r.id, "portfolio_id": r.portfolio_id,
            "total_exposure": float(r.total_exposure or 0),
            "risk_score": float(r.risk_score or 0),
            "company_exposures": r.company_exposures,
            "sector_exposures": r.sector_exposures,
            "created_at": r.created_at,
        }
        for r in rows
    ]


class ExposureCalcRequest(BaseModel):
    portfolio_id: str
    scenario_id: str
    portfolio_ids: Optional[List[str]] = None


@router.post("/calculate")
def calculate_exposure_endpoint(body: ExposureCalcRequest, db: Session = Depends(get_db)):
    """Manually trigger exposure calculation."""
    from src.models.scenario import Scenario
    from src.models.portfolio import Portfolio
    from src.services.market_data_service import collect_scenario_market_data
    from src.services.exposure_service import calculate_exposure

    sc = db.query(Scenario).filter(Scenario.id == body.scenario_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    port = db.query(Portfolio).filter(Portfolio.id == body.portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    holdings = [
        {"id": h.id, "symbol": h.symbol, "company_name": h.company_name,
         "quantity": float(h.quantity), "average_price": float(h.average_price),
         "current_price": float(h.current_price) if h.current_price else None,
         "sector": h.sector, "portfolio_id": body.portfolio_id}
        for h in port.holdings
    ]

    scenario_dict = {"id": sc.id, "name": sc.name, "type": sc.type, "parameters": sc.parameters}
    market_data = collect_scenario_market_data(db, scenario_dict, holdings)
    result = calculate_exposure(db, body.portfolio_id, port.name, holdings, scenario_dict, market_data)
    return result


@router.get("/risk-scores/portfolio/{portfolio_id}")
def get_risk_scores(portfolio_id: str, db: Session = Depends(get_db)):
    rows = db.query(RiskScore).filter(RiskScore.portfolio_id == portfolio_id).order_by(
        RiskScore.created_at.desc()
    ).limit(20).all()
    return [
        {
            "id": r.id, "portfolio_id": r.portfolio_id, "scenario_id": r.scenario_id,
            "score": float(r.score or 0), "risk_level": r.risk_level,
            "pl_impact": float(r.pl_impact or 0), "model_version": r.model_version,
            "created_at": r.created_at,
        }
        for r in rows
    ]
