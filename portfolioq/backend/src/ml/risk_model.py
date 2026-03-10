"""
XGBoost risk scoring model.
Predicts risk_score (0–1) and risk_level from portfolio / exposure features.
"""
import logging
import os
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import mlflow
import mlflow.xgboost

from src.ml.mlflow_tracker import (
    MLFLOW_EXPERIMENT_RISK,
    log_run_summary,
    log_system_metrics,
    run_context,
    transition_registered_model_to_production,
)

logger = logging.getLogger(__name__)

MODEL_DIR = Path(os.getenv("MODEL_STORE", "/app/ml_models"))
RISK_MODEL_PATH = MODEL_DIR / "risk_model.json"
RISK_LABEL_ENC_PATH = MODEL_DIR / "risk_label_encoder.pkl"

RISK_LEVELS = ["low", "medium", "high", "critical"]
FEATURES = [
    "total_exposure_pct",
    "market_beta",
    "scenario_severity",
    "sector_concentration",
    "top_holding_weight",
    "n_holdings",
    "market_volatility",
    "oil_exposure",
    "bond_exposure",
    "regulatory_factor",
]


class RiskScoringModel:
    """XGBoost model for risk scoring and classification."""

    def __init__(self, **params):
        default_params = {
            "max_depth": 5,
            "learning_rate": 0.05,
            "n_estimators": 200,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "use_label_encoder": False,
            "eval_metric": "mlogloss",
            "random_state": 42,
        }
        default_params.update(params)
        self.params = default_params
        self.clf = xgb.XGBClassifier(**{k: v for k, v in default_params.items() if k != "random_state"},
                                      random_state=default_params.get("random_state", 42))
        self.le = LabelEncoder()
        self.le.classes_ = np.array(RISK_LEVELS)
        self._is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> dict[str, float]:
        """Train the risk classification model."""
        y_enc = self.le.transform(y)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.clf, X, y_enc, cv=cv, scoring="accuracy")

        self.clf.fit(X, y_enc)
        y_pred = self.clf.predict(X)

        metrics = {
            "train_accuracy": float(accuracy_score(y_enc, y_pred)),
            "cv_mean_accuracy": float(cv_scores.mean()),
            "cv_std_accuracy": float(cv_scores.std()),
        }
        self._is_fitted = True
        return metrics

    def predict_risk(self, features: dict[str, float]) -> dict[str, Any]:
        """Predict risk score and level for a set of features."""
        if not self._is_fitted:
            return self._fallback_risk(features)

        # Build row with defaults for missing keys so partial feature dicts don't raise KeyError
        row = {f: float(features.get(f, 0.0)) for f in FEATURES}
        X = pd.DataFrame([row], columns=FEATURES)
        proba = self.clf.predict_proba(X)[0]
        class_idx = int(np.argmax(proba))
        risk_level = str(self.le.classes_[class_idx])

        # Continuous risk score: weighted sum of class indices / (n_classes-1)
        n = len(self.le.classes_)
        risk_score = float(np.sum(proba * np.arange(n)) / (n - 1))

        return {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "probabilities": {cls: round(float(p), 4) for cls, p in zip(self.le.classes_, proba)},
        }

    def _fallback_risk(self, features: dict[str, float]) -> dict[str, Any]:
        """Rule-based fallback when model is not fitted."""
        score = (
            features.get("total_exposure_pct", 0.5) * 0.3
            + features.get("market_beta", 1.0) * 0.2
            + features.get("scenario_severity", 0.5) * 0.3
            + features.get("sector_concentration", 0.5) * 0.2
        )
        score = min(1.0, max(0.0, score))
        if score >= 0.8:
            level = "critical"
        elif score >= 0.6:
            level = "high"
        elif score >= 0.3:
            level = "medium"
        else:
            level = "low"
        return {"risk_score": round(score, 4), "risk_level": level, "probabilities": {}}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.clf.save_model(str(RISK_MODEL_PATH))
        joblib.dump(self.le, RISK_LABEL_ENC_PATH)
        logger.info("Risk model saved to %s", RISK_MODEL_PATH)

    @classmethod
    def load(cls) -> "RiskScoringModel":
        if RISK_MODEL_PATH.exists():
            m = cls()
            m.clf.load_model(str(RISK_MODEL_PATH))
            if RISK_LABEL_ENC_PATH.exists():
                m.le = joblib.load(RISK_LABEL_ENC_PATH)
            m._is_fitted = True
            logger.info("Risk model loaded from %s", RISK_MODEL_PATH)
            return m
        logger.info("No saved risk model found; using untrained instance")
        return cls()

    def is_fitted(self) -> bool:
        return self._is_fitted


# -----------------------------------------------------------------------
# Training pipeline
# -----------------------------------------------------------------------
def generate_training_data(n_samples: int = 2000) -> tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic training data for the risk scoring model."""
    np.random.seed(42)
    data = {
        "total_exposure_pct": np.random.beta(2, 3, n_samples),
        "market_beta": np.random.normal(1.0, 0.4, n_samples),
        "scenario_severity": np.random.uniform(0, 1, n_samples),
        "sector_concentration": np.random.beta(2, 4, n_samples),
        "top_holding_weight": np.random.beta(1.5, 3, n_samples),
        "n_holdings": np.random.randint(1, 50, n_samples).astype(float),
        "market_volatility": np.abs(np.random.normal(0.015, 0.008, n_samples)),
        "oil_exposure": np.random.uniform(-0.3, 0.3, n_samples),
        "bond_exposure": np.random.uniform(-0.2, 0.2, n_samples),
        "regulatory_factor": np.random.uniform(0, 0.5, n_samples),
    }
    X = pd.DataFrame(data)

    # Label based on heuristic combination
    score = (
        X["total_exposure_pct"] * 0.25
        + np.clip(X["market_beta"], 0, 2) / 2 * 0.20
        + X["scenario_severity"] * 0.25
        + X["sector_concentration"] * 0.15
        + X["market_volatility"] / 0.03 * 0.10
        + X["regulatory_factor"] * 0.05
    )
    labels = pd.cut(
        score, bins=[0, 0.3, 0.55, 0.75, 1.01], labels=["low", "medium", "high", "critical"]
    ).astype(str)
    return X, pd.Series(labels, name="risk_level")


def train_risk_model(**params) -> RiskScoringModel:
    """Train the risk scoring model and log to MLflow."""
    logger.info("Starting risk model training with params: %s", params)
    X, y = generate_training_data(n_samples=3000)

    model = RiskScoringModel(**params)

    with run_context(MLFLOW_EXPERIMENT_RISK, "risk_model_xgboost",
                     tags={"model_type": "xgboost", "task": "risk_classification"}) as run:
        if run:
            for k, v in model.params.items():
                mlflow.log_param(k, v)
            mlflow.log_param("n_training_samples", len(X))

        t0 = time.perf_counter()
        metrics = model.fit(X, y)
        duration = time.perf_counter() - t0

        if run:
            mlflow.log_metric("training_duration_seconds", round(duration, 3))
            for k, v in metrics.items():
                mlflow.log_metric(k, v)
            log_system_metrics()
            log_run_summary(
                {"training_duration_seconds": round(duration, 3), **metrics},
                "risk_model",
            )
            # Feature importance
            fi = dict(zip(FEATURES, model.clf.feature_importances_))
            for f, imp in fi.items():
                mlflow.log_metric(f"feature_importance_{f}", float(imp))
            # Classification report as artifact for readability in MLflow
            y_pred = model.clf.predict(X)
            y_pred_labels = model.le.inverse_transform(y_pred)
            report = classification_report(y, y_pred_labels, zero_division=0)
            with open("/tmp/classification_report.txt", "w") as f:
                f.write(report)
            mlflow.log_artifact("/tmp/classification_report.txt", artifact_path="evaluation")
            # Feature importance plot for readable graphs in MLflow
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(10, 6))
                imp = model.clf.feature_importances_
                ax.barh(range(len(FEATURES)), imp, color="steelblue")
                ax.set_yticks(range(len(FEATURES)))
                ax.set_yticklabels(FEATURES, fontsize=9)
                ax.set_xlabel("Importance")
                ax.set_title("Risk Model Feature Importance")
                fig.tight_layout()
                fig.savefig("/tmp/feature_importance.png", dpi=100, bbox_inches="tight")
                plt.close(fig)
                mlflow.log_artifact("/tmp/feature_importance.png", artifact_path="plots")
            except Exception as e:
                logger.warning("Could not log feature importance plot: %s", e)
            # Confusion matrix plot for at-a-glance performance in MLflow
            try:
                from sklearn.metrics import ConfusionMatrixDisplay
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(8, 6))
                ConfusionMatrixDisplay.from_predictions(y, y_pred_labels, ax=ax)
                fig.tight_layout()
                fig.savefig("/tmp/confusion_matrix.png", dpi=100, bbox_inches="tight")
                plt.close(fig)
                mlflow.log_artifact("/tmp/confusion_matrix.png", artifact_path="plots")
            except Exception as e:
                logger.warning("Could not log confusion matrix plot: %s", e)
            # Model with signature and input example for registry
            input_example = X.head(5)
            signature = mlflow.models.infer_signature(input_example, model.le.inverse_transform(model.clf.predict(input_example)))
            mlflow.xgboost.log_model(model.clf, artifact_path="risk_clf",
                                     registered_model_name="portfolioq_risk_model",
                                     signature=signature, input_example=input_example)
            transition_registered_model_to_production(
                "portfolioq_risk_model",
                description="XGBoost risk classification (low/medium/high/critical) from exposure and scenario features.",
            )
            logger.info("Risk model training done: cv_acc=%.4f duration=%.2fs", metrics["cv_mean_accuracy"], duration)

    model.save()
    return model


# -----------------------------------------------------------------------
# Hyperparameter tuning
# -----------------------------------------------------------------------
def tune_risk_model(n_trials: int = 30) -> dict[str, Any]:
    """Use Optuna to tune XGBoost hyperparameters."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    X, y = generate_training_data(n_samples=3000)
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    def objective(trial):
        params = {
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0.0, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 0.1, 5.0),
        }
        clf = xgb.XGBClassifier(**params, use_label_encoder=False, eval_metric="mlogloss",
                                 random_state=42, verbosity=0)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(clf, X, y_enc, cv=cv, scoring="accuracy")
        return scores.mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best = study.best_params

    with run_context(MLFLOW_EXPERIMENT_RISK, "hyperparameter_tuning",
                     tags={"model_type": "xgboost", "task": "hyperparam_tuning"}) as run:
        if run:
            for k, v in best.items():
                mlflow.log_param(k, v)
            mlflow.log_metric("best_cv_accuracy", study.best_value)
            mlflow.log_metric("n_trials", n_trials)

    logger.info("Hyperparameter tuning done: best_acc=%.4f params=%s", study.best_value, best)
    return {"best_params": best, "best_accuracy": study.best_value}


_risk_model_instance: RiskScoringModel | None = None


def get_risk_model() -> RiskScoringModel:
    global _risk_model_instance
    if _risk_model_instance is None:
        _risk_model_instance = RiskScoringModel.load()
        if not _risk_model_instance.is_fitted():
            logger.info("Training risk model on startup...")
            _risk_model_instance = train_risk_model()
    return _risk_model_instance
