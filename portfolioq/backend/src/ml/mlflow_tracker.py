"""MLflow tracking utilities for PortfolioQ ML models."""
import logging
import os
import time
from contextlib import contextmanager
from typing import Any

import mlflow
import mlflow.sklearn
import mlflow.xgboost
import psutil

logger = logging.getLogger(__name__)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5001")
MLFLOW_EXPERIMENT_FACTOR = "portfolioq_factor_model"
MLFLOW_EXPERIMENT_RISK = "portfolioq_risk_scoring"
MLFLOW_EXPERIMENT_OPPORTUNITY = "portfolioq_opportunity_detection"


def setup_mlflow():
    """Configure MLflow tracking URI and create default experiments."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    for exp_name in [MLFLOW_EXPERIMENT_FACTOR, MLFLOW_EXPERIMENT_RISK, MLFLOW_EXPERIMENT_OPPORTUNITY]:
        try:
            if mlflow.get_experiment_by_name(exp_name) is None:
                mlflow.create_experiment(exp_name)
        except Exception as exc:
            logger.warning("Could not create MLflow experiment %s: %s", exp_name, exc)


@contextmanager
def run_context(experiment_name: str, run_name: str, tags: dict[str, str] | None = None):
    """Context manager for a single MLflow run."""
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(experiment_name)
        with mlflow.start_run(run_name=run_name, tags=tags or {}) as run:
            yield run
    except Exception as exc:
        logger.error("MLflow run_context failed: %s", exc)
        yield None


def log_system_metrics():
    """Log system metrics (CPU, memory) to current MLflow run."""
    try:
        mlflow.log_metric("system_cpu_percent", psutil.cpu_percent(interval=1))
        mem = psutil.virtual_memory()
        mlflow.log_metric("system_memory_used_gb", round(mem.used / 1e9, 3))
        mlflow.log_metric("system_memory_percent", mem.percent)
    except Exception as exc:
        logger.warning("Could not log system metrics: %s", exc)


def log_model_sklearn(model: Any, artifact_path: str, registered_name: str | None = None):
    """Log a scikit-learn model to MLflow."""
    try:
        mlflow.sklearn.log_model(model, artifact_path=artifact_path, registered_model_name=registered_name)
    except Exception as exc:
        logger.warning("Could not log sklearn model: %s", exc)


def log_model_xgboost(model: Any, artifact_path: str, registered_name: str | None = None):
    """Log an XGBoost model to MLflow."""
    try:
        mlflow.xgboost.log_model(model, artifact_path=artifact_path, registered_model_name=registered_name)
    except Exception as exc:
        logger.warning("Could not log xgboost model: %s", exc)


def load_registered_model(model_name: str, stage: str = "Production"):
    """Load a registered model from MLflow Model Registry."""
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        model_uri = f"models:/{model_name}/{stage}"
        return mlflow.pyfunc.load_model(model_uri)
    except Exception as exc:
        logger.warning("Could not load registered model %s/%s: %s", model_name, stage, exc)
        return None
