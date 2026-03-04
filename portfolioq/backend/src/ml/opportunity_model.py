"""
Opportunity / anomaly detection model using Isolation Forest.
Flags unusual exposure/risk combinations as potential opportunities or hidden risks.
"""
import logging
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.sklearn

from src.ml.mlflow_tracker import MLFLOW_EXPERIMENT_OPPORTUNITY, log_system_metrics, run_context

logger = logging.getLogger(__name__)

MODEL_DIR = Path(os.getenv("MODEL_STORE", "/app/ml_models"))
OPP_MODEL_PATH = MODEL_DIR / "opportunity_model.pkl"

OPPORTUNITY_FEATURES = [
    "risk_score", "total_exposure_pct", "market_beta",
    "sector_concentration", "pl_impact_pct", "volatility",
    "momentum_signal", "value_signal",
]

SIGNAL_TYPES = {
    "strong_buy": "Risk-adjusted opportunity: unusually low risk with above-average potential return",
    "buy": "Moderate opportunity detected under current scenario",
    "hold": "Portfolio position within expected risk/return range",
    "reduce": "Elevated risk signal — consider reducing exposure",
    "sell": "Critical risk signal — high exposure with significant downside",
}


class OpportunityModel:
    """Isolation Forest for detecting anomalous portfolio positions."""

    def __init__(self, contamination: float = 0.1, n_estimators: int = 200):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=42,
        )
        self.scaler = StandardScaler()
        self._is_fitted = False

    def fit(self, X: pd.DataFrame) -> dict[str, float]:
        X_feat = self._prepare_features(X)
        X_scaled = self.scaler.fit_transform(X_feat)
        self.model.fit(X_scaled)
        scores = self.model.score_samples(X_scaled)
        self._is_fitted = True
        return {
            "mean_anomaly_score": float(scores.mean()),
            "std_anomaly_score": float(scores.std()),
            "anomaly_fraction": float((self.model.predict(X_scaled) == -1).mean()),
        }

    def _prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        available = [f for f in OPPORTUNITY_FEATURES if f in X.columns]
        if not available:
            return X
        return X[available].fillna(0)

    def score_holding(self, features: dict[str, float]) -> dict[str, Any]:
        """Score a single holding's opportunity/risk profile."""
        if not self._is_fitted:
            return self._rule_based_signal(features)

        X = pd.DataFrame([{f: features.get(f, 0.0) for f in OPPORTUNITY_FEATURES}])
        X_scaled = self.scaler.transform(X)
        raw_score = float(self.model.score_samples(X_scaled)[0])
        pred = int(self.model.predict(X_scaled)[0])

        normalized = (raw_score - (-0.5)) / 0.5  # approx range
        normalized = max(0.0, min(1.0, normalized))

        risk_score = features.get("risk_score", 0.5)
        pl_pct = features.get("pl_impact_pct", 0.0)

        if pred == -1 and pl_pct > 0.01:
            signal = "strong_buy"
        elif pred == -1 and pl_pct < -0.05:
            signal = "sell"
        elif risk_score > 0.7:
            signal = "reduce"
        elif risk_score > 0.4:
            signal = "hold"
        else:
            signal = "buy" if pl_pct > 0 else "hold"

        return {
            "anomaly_score": round(raw_score, 4),
            "is_anomaly": pred == -1,
            "signal": signal,
            "signal_description": SIGNAL_TYPES[signal],
            "opportunity_score": round(normalized, 4),
        }

    def _rule_based_signal(self, features: dict[str, float]) -> dict[str, Any]:
        risk = features.get("risk_score", 0.5)
        pl = features.get("pl_impact_pct", 0.0)
        if risk < 0.3 and pl > 0.02:
            signal = "strong_buy"
        elif risk < 0.4:
            signal = "buy"
        elif risk > 0.7:
            signal = "sell"
        elif risk > 0.55:
            signal = "reduce"
        else:
            signal = "hold"
        return {
            "anomaly_score": 0.0, "is_anomaly": False,
            "signal": signal, "signal_description": SIGNAL_TYPES[signal],
            "opportunity_score": round(1 - risk, 4),
        }

    def save(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "scaler": self.scaler,
                     "contamination": self.contamination, "n_estimators": self.n_estimators},
                    OPP_MODEL_PATH)

    @classmethod
    def load(cls) -> "OpportunityModel":
        if OPP_MODEL_PATH.exists():
            data = joblib.load(OPP_MODEL_PATH)
            m = cls(contamination=data["contamination"], n_estimators=data["n_estimators"])
            m.model = data["model"]
            m.scaler = data["scaler"]
            m._is_fitted = True
            return m
        return cls()

    def is_fitted(self) -> bool:
        return self._is_fitted


def train_opportunity_model() -> OpportunityModel:
    """Train the opportunity model on synthetic portfolio data and log to MLflow."""
    import time
    np.random.seed(42)
    n = 2000
    data = pd.DataFrame({
        "risk_score": np.random.beta(2, 4, n),
        "total_exposure_pct": np.random.beta(2, 3, n),
        "market_beta": np.clip(np.random.normal(1.0, 0.4, n), 0.1, 2.5),
        "sector_concentration": np.random.beta(2, 5, n),
        "pl_impact_pct": np.random.normal(0, 0.05, n),
        "volatility": np.abs(np.random.normal(0.015, 0.007, n)),
        "momentum_signal": np.random.uniform(-1, 1, n),
        "value_signal": np.random.uniform(-1, 1, n),
    })

    model = OpportunityModel(contamination=0.08, n_estimators=200)

    with run_context(MLFLOW_EXPERIMENT_OPPORTUNITY, "opportunity_isolation_forest",
                     tags={"model_type": "isolation_forest", "task": "anomaly_detection"}) as run:
        if run:
            mlflow.log_param("contamination", model.contamination)
            mlflow.log_param("n_estimators", model.n_estimators)
            mlflow.log_param("n_training_samples", n)

        t0 = time.perf_counter()
        metrics = model.fit(data)
        duration = time.perf_counter() - t0

        if run:
            mlflow.log_metric("training_duration_seconds", round(duration, 3))
            for k, v in metrics.items():
                mlflow.log_metric(k, v)
            log_system_metrics()
            mlflow.sklearn.log_model(model.model, artifact_path="opportunity_detector",
                                     registered_model_name="portfolioq_opportunity_model")

    model.save()
    return model


_opportunity_model_instance: OpportunityModel | None = None


def get_opportunity_model() -> OpportunityModel:
    global _opportunity_model_instance
    if _opportunity_model_instance is None:
        _opportunity_model_instance = OpportunityModel.load()
        if not _opportunity_model_instance.is_fitted():
            _opportunity_model_instance = train_opportunity_model()
    return _opportunity_model_instance
