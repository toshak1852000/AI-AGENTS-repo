"""Exposure calculation node: compute portfolio exposure for the scenario."""
import logging
from datetime import datetime, timezone
from typing import Any

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def _calculate_exposure(
    portfolio_ids: list[str],
    scenario_id: str,
    market_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Stub: compute exposure from market data and scenario.
    TODO: Replace with exposure_service.calculate_exposure(...).
    """
    return {
        "portfolio_ids": portfolio_ids,
        "scenario_id": scenario_id,
        "company_exposures": [],
        "sector_exposures": [],
        "total_exposure": 0.0,
        "risk_score": 0.0,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }


def exposure_calculation_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """
    Compute portfolio exposure using collected market data.
    Sets exposure_result and current_node; on failure sets status and error.
    """
    run_id = state.get("run_id", "")
    scenario_id = state.get("scenario_id", "")
    portfolio_ids = state.get("portfolio_ids") or []
    market_data = state.get("market_data")
    logger.info("exposure_calculation node started", extra={"run_id": run_id})

    if state.get("status") == "failed":
        return {}

    try:
        exposure_result = _calculate_exposure(portfolio_ids, scenario_id, market_data)
        return {
            "current_node": "exposure_calculation",
            "exposure_result": exposure_result,
        }
    except Exception as e:
        logger.exception("exposure_calculation node failed", extra={"run_id": run_id})
        return {
            "status": "failed",
            "current_node": "exposure_calculation",
            "error": str(e),
        }
