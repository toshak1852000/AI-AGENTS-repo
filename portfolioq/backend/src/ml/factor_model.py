"""
Factor model for portfolio exposure and sensitivity analysis.
Uses Ridge regression to estimate factor loadings (betas).
Factor returns: market, size, value, momentum, oil, gold, bonds, usd.
"""
import logging
import os
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import mlflow
import mlflow.sklearn

from src.ml.mlflow_tracker import (
    MLFLOW_EXPERIMENT_FACTOR, MLFLOW_TRACKING_URI, log_system_metrics, run_context
)

logger = logging.getLogger(__name__)

MODEL_DIR = Path(os.getenv("MODEL_STORE", "/app/ml_models"))
FACTOR_MODEL_PATH = MODEL_DIR / "factor_model.pkl"
SCALER_PATH = MODEL_DIR / "factor_scaler.pkl"

FACTOR_NAMES = ["market", "small_cap", "value", "momentum", "oil", "gold", "bonds", "usd"]

SCENARIO_SHOCKS: dict[str, dict[str, float]] = {
    "market_shock": {"market": -0.10, "small_cap": -0.12, "value": -0.08, "momentum": -0.05,
                     "oil": -0.05, "gold": 0.03, "bonds": 0.04, "usd": 0.02},
    "commodity_fluctuation": {"market": -0.02, "small_cap": -0.01, "value": 0.01, "momentum": -0.01,
                               "oil": 0.20, "gold": 0.10, "bonds": -0.01, "usd": -0.02},
    "regulatory_change": {"market": -0.03, "small_cap": -0.04, "value": -0.02, "momentum": -0.01,
                           "oil": -0.01, "gold": 0.01, "bonds": 0.02, "usd": 0.00},
    "geopolitical_event": {"market": -0.07, "small_cap": -0.08, "value": -0.04, "momentum": -0.03,
                            "oil": 0.10, "gold": 0.07, "bonds": 0.03, "usd": 0.01},
    "interest_rate_change": {"market": -0.05, "small_cap": -0.03, "value": 0.02, "momentum": -0.02,
                              "oil": -0.02, "gold": -0.03, "bonds": -0.08, "usd": 0.03},
    "currency_fluctuation": {"market": -0.02, "small_cap": -0.01, "value": 0.01, "momentum": -0.01,
                              "oil": 0.03, "gold": 0.02, "bonds": 0.01, "usd": 0.05},
    "sector_decline": {"market": -0.06, "small_cap": -0.07, "value": -0.05, "momentum": -0.04,
                       "oil": -0.02, "gold": 0.01, "bonds": 0.02, "usd": 0.01},
    "company_specific": {"market": -0.01, "small_cap": -0.01, "value": -0.01, "momentum": -0.01,
                          "oil": 0.00, "gold": 0.00, "bonds": 0.00, "usd": 0.00},
}


class FactorModel:
    """Ridge-regression factor model: fits per-symbol factor betas."""

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha
        self.models: dict[str, Ridge] = {}
        self.scaler = StandardScaler()
        self.factor_names = FACTOR_NAMES
        self._is_fitted = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def fit(self, factor_returns: pd.DataFrame, symbol_returns: pd.DataFrame) -> dict[str, float]:
        """Train one Ridge model per symbol."""
        common_idx = factor_returns.index.intersection(symbol_returns.index)
        X = factor_returns.loc[common_idx][self.factor_names].values
        X_scaled = self.scaler.fit_transform(X)

        metrics: dict[str, float] = {}
        for sym in symbol_returns.columns:
            y = symbol_returns.loc[common_idx, sym].values
            mask = ~np.isnan(y)
            if mask.sum() < 30:
                continue
            model = Ridge(alpha=self.alpha)
            model.fit(X_scaled[mask], y[mask])
            self.models[sym] = model
            y_pred = model.predict(X_scaled[mask])
            metrics[f"r2_{sym}"] = float(r2_score(y[mask], y_pred))
            metrics[f"rmse_{sym}"] = float(mean_squared_error(y[mask], y_pred) ** 0.5)

        self._is_fitted = True
        return metrics

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    # Default sector betas when symbol not in trained model
    SECTOR_DEFAULT_BETAS: dict[str, dict[str, float]] = {
        "Technology": {"market": 1.25, "small_cap": 0.8, "value": -0.3, "momentum": 0.5, "oil": -0.1, "gold": -0.05, "bonds": -0.15, "usd": -0.1},
        "Financials": {"market": 1.1, "small_cap": 0.6, "value": 0.4, "momentum": 0.2, "oil": 0.05, "gold": -0.1, "bonds": -0.3, "usd": 0.2},
        "Energy": {"market": 0.9, "small_cap": 0.4, "value": 0.5, "momentum": 0.3, "oil": 0.7, "gold": 0.1, "bonds": -0.1, "usd": -0.3},
        "Healthcare": {"market": 0.75, "small_cap": 0.3, "value": 0.2, "momentum": 0.1, "oil": -0.05, "gold": 0.1, "bonds": 0.05, "usd": -0.05},
        "Consumer Staples": {"market": 0.65, "small_cap": 0.2, "value": 0.3, "momentum": -0.05, "oil": 0.1, "gold": 0.15, "bonds": 0.1, "usd": -0.05},
        "Consumer Discretionary": {"market": 1.15, "small_cap": 0.7, "value": -0.1, "momentum": 0.4, "oil": -0.2, "gold": -0.05, "bonds": -0.1, "usd": -0.1},
        "Industrials": {"market": 1.05, "small_cap": 0.6, "value": 0.2, "momentum": 0.3, "oil": 0.2, "gold": 0.0, "bonds": -0.1, "usd": -0.15},
        "Materials": {"market": 1.0, "small_cap": 0.5, "value": 0.3, "momentum": 0.2, "oil": 0.3, "gold": 0.4, "bonds": -0.05, "usd": -0.2},
        "Utilities": {"market": 0.55, "small_cap": 0.2, "value": 0.4, "momentum": -0.1, "oil": 0.1, "gold": 0.1, "bonds": 0.2, "usd": -0.05},
        "Real Estate": {"market": 0.8, "small_cap": 0.5, "value": 0.3, "momentum": -0.05, "oil": 0.0, "gold": 0.1, "bonds": 0.3, "usd": -0.1},
        "Communication Services": {"market": 1.1, "small_cap": 0.6, "value": -0.1, "momentum": 0.4, "oil": -0.05, "gold": -0.05, "bonds": -0.1, "usd": -0.05},
        "Unknown": {"market": 1.0, "small_cap": 0.5, "value": 0.1, "momentum": 0.1, "oil": 0.05, "gold": 0.05, "bonds": -0.05, "usd": -0.05},
    }

    def get_factor_betas(self, symbol: str, sector: str = "Unknown") -> dict[str, float]:
        """Return factor betas (loadings) for a symbol; fall back to sector defaults."""
        if symbol not in self.models:
            defaults = self.SECTOR_DEFAULT_BETAS.get(sector) or self.SECTOR_DEFAULT_BETAS["Unknown"]
            return {f: float(defaults.get(f, 0.0)) for f in self.factor_names}
        model = self.models[symbol]
        betas = model.coef_
        return {f: float(b) for f, b in zip(self.factor_names, betas)}

    def scenario_pl_impact(
        self,
        symbol: str,
        quantity: float,
        current_price: float,
        scenario_type: str,
        sector: str = "Unknown",
    ) -> float:
        """Compute estimated P&L for a holding under a scenario shock."""
        shocks = SCENARIO_SHOCKS.get(scenario_type, SCENARIO_SHOCKS["market_shock"])
        betas = self.get_factor_betas(symbol, sector)
        return_est = sum(betas.get(f, 0.0) * shocks.get(f, 0.0) for f in self.factor_names)
        market_value = quantity * current_price
        return round(return_est * market_value, 2)

    def portfolio_sensitivity(
        self, holdings: list[dict[str, Any]], scenario_type: str
    ) -> dict[str, Any]:
        """Compute portfolio-level sensitivity to a scenario."""
        shocks = SCENARIO_SHOCKS.get(scenario_type, SCENARIO_SHOCKS["market_shock"])
        total_mv = sum(h.get("quantity", 0) * h.get("current_price", h.get("average_price", 0)) for h in holdings)
        if total_mv == 0:
            total_mv = 1.0

        holding_results = []
        portfolio_pl = 0.0
        agg_betas: dict[str, float] = {f: 0.0 for f in self.factor_names}

        for h in holdings:
            sym = h["symbol"]
            qty = float(h.get("quantity", 0))
            price = float(h.get("current_price") or h.get("average_price", 0))
            sector = h.get("sector", "Unknown") or "Unknown"
            mv = qty * price
            weight = mv / total_mv
            betas = self.get_factor_betas(sym, sector)
            pl = self.scenario_pl_impact(sym, qty, price, scenario_type, sector)
            portfolio_pl += pl
            for f, b in betas.items():
                agg_betas[f] += weight * b
            holding_results.append({
                "symbol": sym,
                "market_value": round(mv, 2),
                "weight": round(weight, 4),
                "factor_betas": betas,
                "scenario_pl_impact": pl,
            })

        sensitivity_score = min(1.0, max(0.0, abs(portfolio_pl / total_mv) * 5))
        return {
            "scenario_type": scenario_type,
            "total_market_value": round(total_mv, 2),
            "portfolio_pl_impact": round(portfolio_pl, 2),
            "portfolio_return_pct": round(portfolio_pl / total_mv * 100, 4) if total_mv else 0,
            "portfolio_factor_betas": {f: round(b, 4) for f, b in agg_betas.items()},
            "sensitivity_score": round(sensitivity_score, 4),
            "holdings": holding_results,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump({"models": self.models, "scaler": self.scaler, "alpha": self.alpha}, FACTOR_MODEL_PATH)
        logger.info("Factor model saved to %s", FACTOR_MODEL_PATH)

    @classmethod
    def load(cls) -> "FactorModel":
        if FACTOR_MODEL_PATH.exists():
            data = joblib.load(FACTOR_MODEL_PATH)
            m = cls(alpha=data["alpha"])
            m.models = data["models"]
            m.scaler = data["scaler"]
            m._is_fitted = True
            logger.info("Factor model loaded from %s", FACTOR_MODEL_PATH)
            return m
        logger.info("No saved factor model found; using untrained instance")
        return cls()

    def is_fitted(self) -> bool:
        return self._is_fitted and len(self.models) > 0


# -----------------------------------------------------------------------
# Training pipeline
# -----------------------------------------------------------------------
def train_factor_model(alpha: float = 0.1) -> FactorModel:
    """Train the factor model on real (yfinance) or synthetic data and log to MLflow."""
    from src.integrations.yahoo_finance import fetch_factor_returns, fetch_multiple_symbols

    logger.info("Starting factor model training (alpha=%.3f)", alpha)

    # Fetch factor returns
    factor_rets = fetch_factor_returns(period="2y")

    # Define equity universe for training
    equity_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM",
                      "JNJ", "XOM", "V", "PG", "UNH", "HD", "BAC", "MA",
                      "CVX", "LLY", "PFE", "MRK", "ABBV"]
    eq_data = fetch_multiple_symbols(equity_symbols, period="2y")

    if factor_rets.empty or not eq_data:
        logger.warning("No real data; generating synthetic training data")
        factor_rets, eq_returns = _generate_synthetic_data()
    else:
        # Compute equity returns
        eq_prices = pd.DataFrame({sym: df["close_price"] for sym, df in eq_data.items() if not df.empty})
        eq_returns = eq_prices.pct_change().dropna()

    factor_model = FactorModel(alpha=alpha)

    with run_context(MLFLOW_EXPERIMENT_FACTOR, f"factor_model_alpha_{alpha}",
                     tags={"model_type": "factor", "framework": "sklearn"}) as run:
        if run:
            mlflow.log_param("alpha", alpha)
            mlflow.log_param("n_factors", len(FACTOR_NAMES))
            mlflow.log_param("equity_universe_size", len(eq_returns.columns) if not eq_returns.empty else 0)

        t0 = time.perf_counter()
        metrics = factor_model.fit(factor_rets, eq_returns)
        duration = time.perf_counter() - t0

        if run and metrics:
            mlflow.log_metric("training_duration_seconds", round(duration, 3))
            avg_r2 = np.mean([v for k, v in metrics.items() if "r2_" in k])
            avg_rmse = np.mean([v for k, v in metrics.items() if "rmse_" in k])
            mlflow.log_metric("avg_r2", float(avg_r2))
            mlflow.log_metric("avg_rmse", float(avg_rmse))
            mlflow.log_metric("n_models_trained", len(factor_model.models))
            for k, v in metrics.items():
                mlflow.log_metric(k, v)
            log_system_metrics()
            mlflow.sklearn.log_model(factor_model.scaler, artifact_path="factor_scaler",
                                     registered_model_name="portfolioq_factor_scaler")
            logger.info("Factor model training done: avg_r2=%.4f n_models=%d duration=%.2fs", avg_r2, len(factor_model.models), duration)

    factor_model.save()
    return factor_model


def _generate_synthetic_data(n_days: int = 504, n_equities: int = 20):
    """Generate synthetic factor and equity returns for bootstrapping."""
    np.random.seed(42)
    dates = pd.date_range("2022-01-01", periods=n_days, freq="B")
    factor_cov = np.eye(len(FACTOR_NAMES)) * 0.0002
    factor_rets = pd.DataFrame(
        np.random.multivariate_normal(np.zeros(len(FACTOR_NAMES)), factor_cov, n_days),
        columns=FACTOR_NAMES, index=dates
    )
    eq_symbols = [f"SYM{i:02d}" for i in range(n_equities)]
    true_betas = np.random.uniform(0.3, 1.5, (n_equities, len(FACTOR_NAMES)))
    alpha_returns = np.random.normal(0, 0.001, (n_days, n_equities))
    eq_rets = factor_rets.values @ true_betas.T + alpha_returns
    eq_returns = pd.DataFrame(eq_rets, columns=eq_symbols, index=dates)
    return factor_rets, eq_returns


# Singleton instance (loaded or fresh)
_factor_model_instance: FactorModel | None = None


def get_factor_model() -> FactorModel:
    global _factor_model_instance
    if _factor_model_instance is None:
        _factor_model_instance = FactorModel.load()
        if not _factor_model_instance.is_fitted():
            logger.info("Training factor model on startup...")
            _factor_model_instance = train_factor_model()
    return _factor_model_instance
