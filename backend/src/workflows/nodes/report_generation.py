"""Report generation node: generate report and persist; update scenario run."""
import logging
from datetime import datetime, timezone
from typing import Any

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def _generate_report(
    run_id: str,
    scenario_id: str,
    portfolio_ids: list[str],
    market_data: dict[str, Any] | None,
    exposure_result: dict[str, Any] | None,
    risk_result: dict[str, Any] | None,
) -> str:
    """
    Stub: build report from run data, save to storage, create DB record.
    TODO: Replace with report_service.generate_report(...).
    Returns report_id.
    """
    # Placeholder ID until report service is implemented
    return f"report-{run_id}"


def report_generation_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """
    Generate final report and persist; set report_id, status=completed, completed_at.
    On failure sets status and error.
    """
    run_id = state.get("run_id", "")
    scenario_id = state.get("scenario_id", "")
    portfolio_ids = state.get("portfolio_ids") or []
    market_data = state.get("market_data")
    exposure_result = state.get("exposure_result")
    risk_result = state.get("risk_result")
    logger.info("report_generation node started", extra={"run_id": run_id})

    if state.get("status") == "failed":
        return {}

    completed_at = datetime.now(timezone.utc).isoformat()

    try:
        report_id = _generate_report(
            run_id, scenario_id, portfolio_ids,
            market_data, exposure_result, risk_result,
        )
        return {
            "status": "completed",
            "current_node": "report_generation",
            "report_id": report_id,
            "completed_at": completed_at,
        }
    except Exception as e:
        logger.exception("report_generation node failed", extra={"run_id": run_id})
        return {
            "status": "failed",
            "current_node": "report_generation",
            "error": str(e),
            "completed_at": completed_at,
        }
