"""Celery application setup and task definitions."""
import logging
from celery import Celery
from celery.schedules import crontab
from src.config.settings import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "portfolioq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.tasks.celery_tasks",
        "src.tasks.market_data_tasks",
        "src.tasks.scenario_tasks",
        "src.tasks.alert_tasks",
        "src.tasks.ml_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "refresh-market-prices-every-hour": {
            "task": "src.tasks.market_data_tasks.refresh_all_prices",
            "schedule": crontab(minute=0),
        },
        "run-scheduled-scenarios-daily": {
            "task": "src.tasks.scenario_tasks.run_all_scheduled_scenarios",
            "schedule": crontab(hour=6, minute=0),
        },
        "check-alert-thresholds-every-30min": {
            "task": "src.tasks.alert_tasks.check_alert_thresholds",
            "schedule": crontab(minute="*/30"),
        },
        "retrain-models-weekly": {
            "task": "src.tasks.ml_tasks.retrain_all_models",
            "schedule": crontab(hour=2, minute=0, day_of_week=0),
        },
    },
)


@celery_app.task(name="portfolioq.tasks.health_check")
def health_check():
    """Celery worker health check."""
    return {"status": "healthy", "worker": "portfolioq"}
