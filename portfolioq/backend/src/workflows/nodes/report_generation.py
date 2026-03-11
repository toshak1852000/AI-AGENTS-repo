"""Report generation node: create board-ready PDF/Excel/JSON report."""
import logging
from datetime import datetime, timezone

from src.workflows.state import ScenarioAnalysisStateTypedDict

logger = logging.getLogger(__name__)


def report_generation_node(state: ScenarioAnalysisStateTypedDict) -> ScenarioAnalysisStateTypedDict:
    """Generate full board-ready report and create alerts."""
    from src.core.database import SessionLocal
    from src.models.portfolio import Portfolio
    from src.services.report_service import generate_report
    from src.services.alert_service import evaluate_and_create_alerts
    from src.services.rebalancing_service import generate_rebalancing_recommendations
    from src.analytics.metrics import SCENARIO_RUNS_TOTAL, PORTFOLIO_RISK_SCORE, PORTFOLIO_PL_IMPACT, ALERTS_CREATED, REPORTS_GENERATED

    if state.get("status") == "failed":
        return {}

    run_id = state.get("run_id", "")
    market_data = state.get("market_data") or {}
    exposure_result = state.get("exposure_result") or {}
    risk_result = state.get("risk_result") or {}
    portfolio_ids = state.get("portfolio_ids") or []
    scenario = market_data.get("scenario", {"id": state.get("scenario_id"), "type": "market_shock"})
    scenario["run_id"] = run_id

    logger.info("report_generation node started run_id=%s", run_id)

    db = SessionLocal()
    try:
        portfolio_id = portfolio_ids[0] if portfolio_ids else "default"
        port_row = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        portfolio = {"id": portfolio_id, "name": port_row.name if port_row else "Portfolio"}

        # Generate rebalancing recommendations and attach to risk_result
        rebal = generate_rebalancing_recommendations(portfolio, exposure_result, risk_result)
        risk_result["rebalancing_recommendations"] = rebal

        # Generate report
        report_summary = generate_report(
            db, scenario, portfolio, exposure_result, risk_result, run_id, report_format="json"
        )
        report_id = report_summary.get("report_id")

        # Create alerts
        alerts = evaluate_and_create_alerts(
            db, portfolio_id, scenario, exposure_result, risk_result, run_id
        )

        # Update Prometheus metrics
        scenario_type = scenario.get("type", "unknown")
        SCENARIO_RUNS_TOTAL.labels(scenario_type=scenario_type, status="completed").inc()
        PORTFOLIO_RISK_SCORE.labels(portfolio_id=portfolio_id, scenario_type=scenario_type).set(
            risk_result.get("risk_score", 0)
        )
        PORTFOLIO_PL_IMPACT.labels(portfolio_id=portfolio_id, scenario_type=scenario_type).set(
            risk_result.get("pl_impact", 0) or 0
        )
        for alert in alerts:
            ALERTS_CREATED.labels(severity=alert.severity).inc()
        REPORTS_GENERATED.labels(format="json").inc()

        return {
            "status": "completed",
            "current_node": "report_generation",
            "report_id": report_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.exception("report_generation failed run_id=%s", run_id)
        try:
            from src.analytics.metrics import SCENARIO_RUNS_TOTAL
            SCENARIO_RUNS_TOTAL.labels(scenario_type="unknown", status="failed").inc()
        except Exception:
            pass
        return {
            "status": "failed",
            "current_node": "report_generation",
            "error": str(e),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()
