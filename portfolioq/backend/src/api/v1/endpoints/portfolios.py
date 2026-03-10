"""Portfolio CRUD endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.core.database import get_db
from src.models.portfolio import Portfolio, Holding
from src.models.scenario import ScenarioRun
from src.models.exposure import Exposure, RiskScore
from src.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, Portfolio as PortfolioSchema,
    PortfolioWithHoldings, HoldingCreate, Holding as HoldingSchema,
)
from src.analytics.metrics import PORTFOLIOS_COUNT, HOLDINGS_COUNT

router = APIRouter()


@router.get("/", response_model=List[PortfolioSchema])
def list_portfolios(db: Session = Depends(get_db)):
    rows = db.query(Portfolio).order_by(Portfolio.created_at.desc()).all()
    return rows


@router.post("/", response_model=PortfolioSchema, status_code=status.HTTP_201_CREATED)
def create_portfolio(body: PortfolioCreate, db: Session = Depends(get_db)):
    port = Portfolio(id=str(uuid.uuid4()), name=body.name, description=body.description)
    db.add(port)
    db.commit()
    db.refresh(port)
    PORTFOLIOS_COUNT.set(db.query(Portfolio).count())
    return port


@router.get("/{portfolio_id}", response_model=PortfolioWithHoldings)
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port


@router.put("/{portfolio_id}", response_model=PortfolioSchema)
def update_portfolio(portfolio_id: str, body: PortfolioUpdate, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if body.name is not None:
        port.name = body.name
    if body.description is not None:
        port.description = body.description
    db.commit()
    db.refresh(port)
    return port


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(port)
    db.commit()
    PORTFOLIOS_COUNT.set(db.query(Portfolio).count())


# ---- Holdings ----

@router.get("/{portfolio_id}/holdings", response_model=List[HoldingSchema])
def list_holdings(portfolio_id: str, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port.holdings


@router.post("/{portfolio_id}/holdings", response_model=HoldingSchema, status_code=status.HTTP_201_CREATED)
def add_holding(portfolio_id: str, body: HoldingCreate, db: Session = Depends(get_db)):
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # Fetch live price
    current_price = None
    try:
        from src.integrations.yahoo_finance import fetch_current_price
        current_price = fetch_current_price(body.symbol)
    except Exception:
        pass

    h = Holding(
        id=str(uuid.uuid4()),
        portfolio_id=portfolio_id,
        symbol=body.symbol.upper(),
        company_name=body.company_name,
        quantity=body.quantity,
        average_price=body.average_price,
        current_price=current_price,
        sector=body.sector,
    )
    db.add(h)
    db.commit()
    db.refresh(h)
    HOLDINGS_COUNT.set(db.query(Holding).count())
    return h


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(portfolio_id: str, holding_id: str, db: Session = Depends(get_db)):
    h = db.query(Holding).filter(Holding.id == holding_id, Holding.portfolio_id == portfolio_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Holding not found")
    db.delete(h)
    db.commit()
    HOLDINGS_COUNT.set(db.query(Holding).count())


@router.get("/{portfolio_id}/rebalancing-recommendations")
def get_rebalancing_recommendations(
    portfolio_id: str,
    scenario_id: Optional[str] = Query(None, description="Optional scenario ID; uses latest run for exposure/risk"),
    db: Session = Depends(get_db),
):
    """Scenario-based rebalancing recommendations for a portfolio. Uses latest run if scenario_id given, else latest exposure/risk."""
    from src.services.rebalancing_service import generate_rebalancing_recommendations

    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    portfolio = {"id": port.id, "name": port.name}

    exposure_result = {}
    risk_result = {"risk_level": "low", "risk_score": 0.5, "prioritized_holdings": []}

    if scenario_id:
        runs = (
            db.query(ScenarioRun)
            .filter(ScenarioRun.scenario_id == scenario_id, ScenarioRun.status == "completed")
            .order_by(ScenarioRun.completed_at.desc().nullslast(), ScenarioRun.created_at.desc())
            .all()
        )
        run = None
        for r in runs:
            if r.portfolio_ids and portfolio_id in r.portfolio_ids and r.exposure_result and r.risk_result:
                run = r
                break
        if run:
            exposure_result = run.exposure_result or {}
            risk_result = run.risk_result or risk_result
    if not exposure_result:
        exp = (
            db.query(Exposure)
            .filter(Exposure.portfolio_id == portfolio_id)
            .order_by(Exposure.created_at.desc())
            .first()
        )
        if exp:
            exposure_result = {
                "total_exposure": float(exp.total_exposure or 0),
                "sector_exposures": exp.sector_exposures or [],
                "company_exposures": exp.company_exposures or [],
            }
        rs = (
            db.query(RiskScore)
            .filter(RiskScore.portfolio_id == portfolio_id)
            .order_by(RiskScore.created_at.desc())
            .first()
        )
        if rs:
            risk_result["risk_level"] = rs.risk_level or "low"
            risk_result["risk_score"] = float(rs.score or 0.5)
            risk_result["pl_impact"] = float(rs.pl_impact or 0)
            risk_result["prioritized_holdings"] = risk_result.get("prioritized_holdings") or []

    recs = generate_rebalancing_recommendations(portfolio, exposure_result, risk_result)
    return recs


@router.post("/{portfolio_id}/refresh-prices", response_model=dict)
def refresh_prices(portfolio_id: str, db: Session = Depends(get_db)):
    """Refresh current prices for all holdings in a portfolio."""
    from src.integrations.yahoo_finance import fetch_current_price
    port = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    updated = 0
    for h in port.holdings:
        price = fetch_current_price(h.symbol)
        if price:
            h.current_price = price
            updated += 1
    db.commit()
    return {"portfolio_id": portfolio_id, "updated_holdings": updated}
