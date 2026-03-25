#!/usr/bin/env python3
"""
Training pipeline — single-command automated model retraining.
Runs data ingestion (optional), training for factor, risk, opportunity models, MLflow logging.
"""
import logging
import os
import sys

# Ensure backend src is on path
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def run_training_pipeline(force_retrain: bool = True) -> dict:
    """Run full training pipeline: setup MLflow, train all models."""
    from src.ml.training import train_all_models
    from src.ml.mlflow_tracker import setup_mlflow

    setup_mlflow()
    results = train_all_models(force_retrain=force_retrain)
    logger.info("Training pipeline complete: %s", results)
    return results


if __name__ == "__main__":
    force = os.getenv("FORCE_RETRAIN", "true").lower() == "true"
    run_training_pipeline(force_retrain=force)
