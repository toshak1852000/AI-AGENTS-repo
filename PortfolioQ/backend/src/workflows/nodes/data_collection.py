"""Data collection node: fetch real market data for scenario and portfolios."""
import logging
from typing import Any

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def data_collection_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """Fetch current prices, factor returns, and macro data for the scenario and portfolios."""
    from src.core.database import SessionLocal
    from src.models.scenario import Scenario
    from src.models.portfolio import Portfolio
    from src.services.market_data_service import collect_scenario_market_data

    run_id = state.get("run_id", "")
    scenario_id = state.get("scenario_id", "")
    portfolio_ids = state.get("portfolio_ids") or []
    logger.info("data_collection node started run_id=%s scenario_id=%s", run_id, scenario_id)

    db = SessionLocal()
    try:
        # Load scenario from DB
        scenario_row = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if scenario_row:
            scenario = {
                "id": scenario_row.id,
                "name": scenario_row.name,
                "type": scenario_row.type,
                "parameters": scenario_row.parameters or {},
                "run_id": run_id,
            }
        else:
            scenario = {"id": scenario_id, "name": "Unknown", "type": "market_shock",
                        "parameters": {}, "run_id": run_id}

        # Collect holdings across all portfolios
        all_holdings: list[dict[str, Any]] = []
        for pid in portfolio_ids:
            port = db.query(Portfolio).filter(Portfolio.id == pid).first()
            if port:
                for h in port.holdings:
                    all_holdings.append({
                        "id": h.id,
                        "portfolio_id": pid,
                        "symbol": h.symbol,
                        "company_name": h.company_name,
                        "quantity": float(h.quantity),
                        "average_price": float(h.average_price),
                        "current_price": float(h.current_price) if h.current_price else None,
                        "sector": h.sector,
                    })

        market_data = collect_scenario_market_data(db, scenario, all_holdings)
        market_data["scenario"] = scenario
        market_data["holdings"] = all_holdings

        return {"status": "running", "current_node": "data_collection", "market_data": market_data}

    except Exception as e:
        logger.exception("data_collection failed run_id=%s", run_id)
        return {"status": "failed", "current_node": "data_collection", "error": str(e)}
    finally:
        db.close()
