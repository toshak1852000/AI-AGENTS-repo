"""
Opportunity / anomaly detection model using Isolation Forest.
Flags unusual exposure/risk combinations as potential opportunities or hidden risks.
"""
import logging
import os
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.sklearn

from src.ml.mlflow_tracker import (
    MLFLOW_EXPERIMENT_OPPORTUNITY,
    log_run_summary,
    log_system_metrics,
    run_context,
    transition_registered_model_to_production,
)

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
        if len(X_feat) < 2:
            raise ValueError(
                "Opportunity model requires at least 2 samples to fit; "
                "got %d" % len(X_feat)
            )
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
        """Return DataFrame with OPPORTUNITY_FEATURES columns only; missing filled with 0."""
        available = [f for f in OPPORTUNITY_FEATURES if f in X.columns]
        if not available:
            return pd.DataFrame(0.0, index=X.index, columns=OPPORTUNITY_FEATURES)
        out = X.reindex(columns=OPPORTUNITY_FEATURES).fillna(0.0)
        return out

    def score_holding(self, features: dict[str, float]) -> dict[str, Any]:
        """Score a single holding's opportunity/risk profile."""
        if not self._is_fitted:
            return self._rule_based_signal(features)

        # Coerce to float so API/callers passing int or None don't break
        row = {}
        for f in OPPORTUNITY_FEATURES:
            v = features.get(f, 0.0)
            try:
                row[f] = float(v) if v is not None else 0.0
            except (TypeError, ValueError):
                row[f] = 0.0
        X = pd.DataFrame([row], columns=OPPORTUNITY_FEATURES)
        X_scaled = self.scaler.transform(X)
        raw_score = float(self.model.score_samples(X_scaled)[0])
        pred = int(self.model.predict(X_scaled)[0])

        normalized = (raw_score - (-0.5)) / 0.5  # approx range
        normalized = max(0.0, min(1.0, normalized))

        try:
            risk_score = float(features.get("risk_score", 0.5) or 0.5)
        except (TypeError, ValueError):
            risk_score = 0.5
        try:
            pl_pct = float(features.get("pl_impact_pct", 0.0) or 0.0)
        except (TypeError, ValueError):
            pl_pct = 0.0

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
        try:
            risk = float(features.get("risk_score", 0.5) or 0.5)
        except (TypeError, ValueError):
            risk = 0.5
        try:
            pl = float(features.get("pl_impact_pct", 0.0) or 0.0)
        except (TypeError, ValueError):
            pl = 0.0
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
        if not OPP_MODEL_PATH.exists():
            return cls()
        try:
            data = joblib.load(OPP_MODEL_PATH)
        except Exception as e:
            logger.warning("Could not load opportunity model from %s: %s", OPP_MODEL_PATH, e)
            return cls()
        required = ("contamination", "n_estimators", "model", "scaler")
        if not all(k in data for k in required):
            logger.warning(
                "Opportunity model pickle missing keys (have %s); using fresh instance",
                list(data.keys()),
            )
            return cls()
        m = cls(contamination=data["contamination"], n_estimators=data["n_estimators"])
        m.model = data["model"]
        m.scaler = data["scaler"]
        m._is_fitted = True
        return m

    def is_fitted(self) -> bool:
        return self._is_fitted


def train_opportunity_model() -> OpportunityModel:
    """Train the opportunity model on synthetic portfolio data and log to MLflow.
    Hyperparams align with configs/config.yaml ml_models.opportunity (contamination=0.08, n_estimators=200).
    """
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
            log_run_summary(
                {"training_duration_seconds": round(duration, 3), **metrics},
                "opportunity_model",
            )

            # Anomaly score distribution plot for MLflow
            X_feat = model._prepare_features(data)
            X_scaled = model.scaler.transform(X_feat)
            scores = model.model.score_samples(X_scaled)
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.hist(scores, bins=30, color="steelblue", edgecolor="white")
                ax.set_xlabel("Anomaly score")
                ax.set_ylabel("Count")
                ax.set_title("Anomaly score distribution (training)")
                fig.tight_layout()
                fig.savefig("/tmp/opportunity_anomaly_scores.png", dpi=100, bbox_inches="tight")
                plt.close(fig)
                mlflow.log_artifact("/tmp/opportunity_anomaly_scores.png", artifact_path="plots")
            except Exception as e:
                logger.warning("Could not log opportunity score histogram: %s", e)

            # Signature and input_example for registry
            input_example = X_feat.head(5)
            try:
                out = model.model.score_samples(model.scaler.transform(input_example))
                signature = mlflow.models.infer_signature(input_example, out)
                mlflow.sklearn.log_model(
                    model.model,
                    artifact_path="opportunity_detector",
                    registered_model_name="portfolioq_opportunity_model",
                    signature=signature,
                    input_example=input_example,
                )
            except Exception as e:
                logger.warning("Log opportunity model with signature failed, logging without: %s", e)
                mlflow.sklearn.log_model(
                    model.model,
                    artifact_path="opportunity_detector",
                    registered_model_name="portfolioq_opportunity_model",
                )
            transition_registered_model_to_production(
                "portfolioq_opportunity_model",
                description="Isolation Forest for portfolio opportunity/anomaly detection (risk_score, exposure, beta, etc.).",
            )

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
