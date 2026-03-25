"""ML model training / retraining Celery tasks."""
import logging
from src.tasks.celery_tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.ml_tasks.retrain_all_models", bind=True, max_retries=2)
def retrain_all_models(self):
    """Weekly retraining of all ML models."""
    from src.ml.training import train_all_models
    from src.ml.mlflow_tracker import setup_mlflow
    setup_mlflow()
    results = train_all_models(force_retrain=True)
    logger.info("Weekly ML retraining done: %s", results)
    return results
