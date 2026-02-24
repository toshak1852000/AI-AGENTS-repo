"""Data collection node: gather market/commodity data for scenario and portfolios."""
import logging
from datetime import datetime, timezone
from typing import Any

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def _collect_market_data(scenario_id: str, portfolio_ids: list[str]) -> dict[str, Any]:
    """
    Stub: gather market data for the given scenario and portfolios.
    TODO: Replace with market data service call (resolve holdings, fetch from providers, normalize).
    """
    # Placeholder until market_data_service is implemented
    return {
        "scenario_id": scenario_id,
        "portfolio_ids": portfolio_ids,
        "symbols": [],
        "data": {},
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def data_collection_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """
    Gather all market/commodity data required for the scenario and portfolios.
    Sets market_data and current_node; on failure sets status and error.
    """
    run_id = state.get("run_id", "")
    scenario_id = state.get("scenario_id", "")
    portfolio_ids = state.get("portfolio_ids") or []
    logger.info("data_collection node started", extra={"run_id": run_id})

    try:
        market_data = _collect_market_data(scenario_id, portfolio_ids)
        return {
            "status": "running",
            "current_node": "data_collection",
            "market_data": market_data,
        }
    except Exception as e:
        logger.exception("data_collection node failed", extra={"run_id": run_id})
        return {
            "status": "failed",
            "current_node": "data_collection",
            "error": str(e),
        }
