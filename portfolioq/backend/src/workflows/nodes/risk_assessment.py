"""Risk assessment node: real XGBoost risk scoring and opportunity signals."""
import logging

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def risk_assessment_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """Compute real risk scores using the XGBoost model."""
    from src.core.database import SessionLocal
    from src.services.risk_service import assess_risk

    if state.get("status") == "failed":
        return {}

    run_id = state.get("run_id", "")
    market_data = state.get("market_data") or {}
    exposure_result = state.get("exposure_result") or {}
    portfolio_ids = state.get("portfolio_ids") or []
    scenario = market_data.get("scenario", {"id": state.get("scenario_id"), "type": "market_shock"})
    scenario["run_id"] = run_id

    logger.info("risk_assessment node started run_id=%s", run_id)

    db = SessionLocal()
    try:
        portfolio_id = portfolio_ids[0] if portfolio_ids else "default"
        risk_result = assess_risk(db, portfolio_id, scenario, exposure_result, market_data)
        return {"current_node": "risk_assessment", "risk_result": risk_result}
    except Exception as e:
        logger.exception("risk_assessment failed run_id=%s", run_id)
        return {"status": "failed", "current_node": "risk_assessment", "error": str(e)}
    finally:
        db.close()
