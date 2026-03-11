"""Celery task definitions."""
from celery import Celery
from src.config.settings import settings

# Create Celery app
celery_app = Celery(
    "portfolioq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)


@celery_app.task(name="portfolioq.tasks.health_check")
def health_check():
    """Health check task."""
    return {"status": "healthy"}


# TODO: Add actual tasks for market data updates, scenario analysis, etc.
# These will be implemented in market_data_tasks.py, scenario_tasks.py, etc.
