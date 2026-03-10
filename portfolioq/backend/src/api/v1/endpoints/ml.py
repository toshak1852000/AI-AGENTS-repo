"""ML model management endpoints."""
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter()


@router.get("/status")
def ml_status():
    """Return current ML model status."""
    from src.ml.factor_model import get_factor_model
    from src.ml.risk_model import get_risk_model
    from src.ml.opportunity_model import get_opportunity_model
    return {
        "factor_model": {
            "fitted": get_factor_model().is_fitted(),
            "n_symbols": len(get_factor_model().models),
        },
        "risk_model": {"fitted": get_risk_model().is_fitted()},
        "opportunity_model": {"fitted": get_opportunity_model().is_fitted()},
    }


@router.post("/train")
def train_models(force_retrain: bool = False, background_tasks: BackgroundTasks = None):
    """Trigger training of all ML models."""
    from src.ml.training import train_all_models

    if background_tasks:
        background_tasks.add_task(train_all_models, force_retrain=force_retrain)
        return {"status": "training_started", "force_retrain": force_retrain}
    result = train_all_models(force_retrain=force_retrain)
    return {"status": "training_complete", "results": result}


@router.post("/retrain")
def retrain_models(background_tasks: BackgroundTasks):
    """Force retrain all ML models."""
    from src.ml.training import train_all_models
    background_tasks.add_task(train_all_models, force_retrain=True)
    return {"status": "retraining_started"}


class TuningRequest(BaseModel):
    n_trials: int = 30


@router.post("/tune")
def tune_risk_model(body: TuningRequest, background_tasks: BackgroundTasks):
    """Run hyperparameter tuning for the risk model."""
    from src.ml.risk_model import tune_risk_model
    background_tasks.add_task(tune_risk_model, n_trials=body.n_trials)
    return {"status": "tuning_started", "n_trials": body.n_trials}


class ScoreRequest(BaseModel):
    portfolio_id: str
    scenario_type: str = "market_shock"


@router.post("/score")
def score_portfolio(body: ScoreRequest):
    """Score a portfolio's risk under a given scenario."""
    from src.ml.risk_model import get_risk_model, FEATURES
    return get_risk_model().predict_risk({f: 0.5 for f in FEATURES})


class BatchScoreRequest(BaseModel):
    """Batch risk score: list of feature dicts (same keys as FEATURES)."""
    features_list: list[dict[str, float]]
    max_size: int = 100


@router.post("/score/batch")
def score_portfolio_batch(body: BatchScoreRequest):
    """Batch prediction for risk scores (production endpoint)."""
    from src.ml.risk_model import get_risk_model, FEATURES
    model = get_risk_model()
    size = min(len(body.features_list), body.max_size)
    results = []
    for i in range(size):
        feats = body.features_list[i]
        vec = {f: feats.get(f, 0.5) for f in FEATURES}
        results.append(model.predict_risk(vec))
    return {"predictions": results, "count": len(results)}


class ScenarioSimulationRequest(BaseModel):
    """Scenario simulation request (holdings + scenario type)."""
    holdings: list[dict]
    scenario_type: str = "market_shock"
    scale: float = 1.0


@router.post("/scenario-simulation")
def run_scenario_simulation_endpoint(body: ScenarioSimulationRequest):
    """Run scenario simulation engine: P&L impact, exposure, sector vulnerability."""
    from src.scenario_engine import run_scenario_simulation
    return run_scenario_simulation(body.holdings, body.scenario_type, scale=body.scale)


class FactorBetasRequest(BaseModel):
    symbols: list[str]
    scenario_type: str = "market_shock"


@router.post("/factor-betas")
def get_factor_betas(body: FactorBetasRequest):
    """Return factor betas for a list of symbols."""
    from src.ml.factor_model import get_factor_model
    fm = get_factor_model()
    result = {}
    for sym in body.symbols:
        result[sym] = fm.get_factor_betas(sym)
    return {"symbols": result, "scenario_type": body.scenario_type}


@router.get("/mlflow-url")
def get_mlflow_url():
    """Return the MLflow tracking UI URL."""
    import os
    return {"mlflow_url": os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5003")}
