"""Model training pipeline — trains all PortfolioQ ML models."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def train_all_models(force_retrain: bool = False) -> dict[str, Any]:
    """Train (or retrain if force=True) all ML models."""
    from src.ml.mlflow_tracker import setup_mlflow
    from src.ml.factor_model import get_factor_model, train_factor_model
    from src.ml.risk_model import get_risk_model, train_risk_model
    from src.ml.opportunity_model import get_opportunity_model, train_opportunity_model

    setup_mlflow()
    results: dict[str, Any] = {}

    logger.info("=== Training Factor Model ===")
    try:
        if force_retrain:
            fm = train_factor_model()
        else:
            fm = get_factor_model()
        results["factor_model"] = {"status": "ok", "n_symbols": len(fm.models)}
    except Exception as exc:
        logger.error("Factor model training failed: %s", exc)
        results["factor_model"] = {"status": "error", "error": str(exc)}

    logger.info("=== Training Risk Model ===")
    try:
        if force_retrain:
            rm = train_risk_model()
        else:
            rm = get_risk_model()
        results["risk_model"] = {"status": "ok", "fitted": rm.is_fitted()}
    except Exception as exc:
        logger.error("Risk model training failed: %s", exc)
        results["risk_model"] = {"status": "error", "error": str(exc)}

    logger.info("=== Training Opportunity Model ===")
    try:
        if force_retrain:
            om = train_opportunity_model()
        else:
            om = get_opportunity_model()
        results["opportunity_model"] = {"status": "ok", "fitted": om.is_fitted()}
    except Exception as exc:
        logger.error("Opportunity model training failed: %s", exc)
        results["opportunity_model"] = {"status": "error", "error": str(exc)}

    logger.info("All model training complete: %s", results)
    return results
