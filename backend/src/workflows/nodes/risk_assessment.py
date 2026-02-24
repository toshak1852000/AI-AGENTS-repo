"""Risk assessment node: compute risk scores and P&L impact from exposure."""
import logging
from datetime import datetime, timezone
from typing import Any

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def _assess_risk(
    scenario_id: str,
    portfolio_ids: list[str],
    exposure_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Stub: compute risk scores from exposure and scenario.
    TODO: Replace with risk_service.assess_risk(...).
    """
    return {
        "scenario_id": scenario_id,
        "portfolio_ids": portfolio_ids,
        "scores": [],
        "prioritized_holdings": [],
        "pl_impact": None,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }


def risk_assessment_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """
    Compute risk scores and optional P&L impact from exposure and scenario.
    Sets risk_result and current_node; on failure sets status and error.
    """
    run_id = state.get("run_id", "")
    scenario_id = state.get("scenario_id", "")
    portfolio_ids = state.get("portfolio_ids") or []
    exposure_result = state.get("exposure_result")
    logger.info("risk_assessment node started", extra={"run_id": run_id})

    if state.get("status") == "failed":
        return {}

    try:
        risk_result = _assess_risk(scenario_id, portfolio_ids, exposure_result)
        return {
            "current_node": "risk_assessment",
            "risk_result": risk_result,
        }
    except Exception as e:
        logger.exception("risk_assessment node failed", extra={"run_id": run_id})
        return {
            "status": "failed",
            "current_node": "risk_assessment",
            "error": str(e),
        }
