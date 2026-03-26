"""Scenario Celery tasks — scheduled and on-demand analysis."""
import logging
import uuid
from datetime import datetime, timezone
from src.tasks.celery_tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.scenario_tasks.run_all_scheduled_scenarios", bind=True, max_retries=2)
def run_all_scheduled_scenarios(self):
    """Run all scenarios against all portfolios (daily scheduled task)."""
    from src.core.database import SessionLocal
    from src.models.scenario import Scenario, ScenarioRun
    from src.models.portfolio import Portfolio
    from src.workflows import run_workflow
    from src.analytics.metrics import SCENARIO_RUNS_TOTAL

    db = SessionLocal()
    completed = failed = 0
    try:
        scenarios = db.query(Scenario).all()
        portfolios = db.query(Portfolio).all()
        if not scenarios or not portfolios:
            return {"completed": 0, "failed": 0, "message": "No scenarios or portfolios found"}

        portfolio_ids = [p.id for p in portfolios]

        for sc in scenarios:
            run_id = str(uuid.uuid4())
            run_record = ScenarioRun(
                id=run_id, scenario_id=sc.id, portfolio_ids=portfolio_ids,
                status="running", started_at=datetime.now(timezone.utc),
            )
            db.add(run_record)
            db.commit()

            SCENARIO_RUNS_TOTAL.labels(scenario_type=sc.type, status="started").inc()
            try:
                state = run_workflow(run_id=run_id, scenario_id=sc.id, portfolio_ids=portfolio_ids)
                run_record.status = state.get("status", "unknown")
                run_record.report_id = state.get("report_id")
                run_record.error = state.get("error")
                db.commit()
                completed += 1
            except Exception as exc:
                run_record.status = "failed"
                run_record.error = str(exc)
                db.commit()
                failed += 1
                logger.error("Scheduled scenario %s failed: %s", sc.name, exc)

        return {"completed": completed, "failed": failed}
    finally:
        from src.analytics.pushgateway import push_worker_metrics

        push_worker_metrics()
        db.close()


@celery_app.task(name="src.tasks.scenario_tasks.run_single_scenario")
def run_single_scenario(scenario_id: str, portfolio_ids: list):
    """Run a single scenario analysis (called on-demand)."""
    from src.workflows import run_workflow
    from src.analytics.pushgateway import push_worker_metrics

    run_id = str(uuid.uuid4())
    try:
        state = run_workflow(run_id=run_id, scenario_id=scenario_id, portfolio_ids=portfolio_ids)
        return {"run_id": run_id, "status": state.get("status"), "report_id": state.get("report_id")}
    finally:
        push_worker_metrics()
