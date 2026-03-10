# Model Methodology

## Overview

PortfolioQ uses three production ML models: **Factor** (Ridge + scaler), **Risk** (XGBoost classifier), and **Opportunity** (Isolation Forest). Training uses cross-validation, hyperparameter tuning (risk), reproducible seeds, and MLflow for versioning.

---

## 1. Factor Model

- **Purpose:** Per-symbol factor loadings (betas) for market, small_cap, value, momentum, oil, gold, bonds, usd.
- **Algorithm:** Ridge regression per symbol on scaled factor returns; `StandardScaler` on factor returns.
- **Training data:** Yahoo Finance factor returns + equity returns (or synthetic).
- **Metrics:** R² and RMSE per symbol; avg_r2, avg_rmse, n_models_trained; MLflow artifacts: R² bar chart, CSV symbol/r2/rmse.
- **Output:** Factor betas per symbol/portfolio; used by scenario engine and exposure service.

---

## 2. Risk Model

- **Purpose:** Portfolio risk score (0–1) and risk level (low, medium, high, critical).
- **Algorithm:** XGBoost classifier; Stratified 5-fold CV; Optuna tuning (optional).
- **Features:** total_exposure_pct, market_beta, scenario_severity, sector_concentration, top_holding_weight, n_holdings, market_volatility, oil_exposure, bond_exposure, regulatory_factor.
- **Metrics:** train_accuracy, cv_mean_accuracy, cv_std_accuracy; artifacts: classification report, feature importance, confusion matrix.
- **Evaluation:** Accuracy, F1 weighted, ROC-AUC (evaluation module); overfitting check via train/val ratio.

---

## 3. Opportunity Model

- **Purpose:** Anomaly detection and opportunity signals (strong_buy, buy, hold, reduce, sell) per holding.
- **Algorithm:** Isolation Forest + StandardScaler on holding features.
- **Features:** risk_score, total_exposure_pct, market_beta, sector_concentration, pl_impact_pct, volatility, momentum_signal, value_signal.
- **Metrics:** mean_anomaly_score, std_anomaly_score, anomaly_fraction; artifact: anomaly score histogram.

---

## 4. Model Versioning and Reproducibility

- **MLflow:** Experiments `portfolioq_factor_model`, `portfolioq_risk_scoring`, `portfolioq_opportunity_detection`; params, metrics, system metrics, plot artifacts; model registry with signature and input_example; latest version auto-transitioned to Production.
- **Seeds:** Random state 42 in training and evaluation (config: `configs/model_params.yaml`).
- **Artifacts:** Models saved to disk (`MODEL_STORE`); MLflow stores logged models and artifacts for reproducibility.

---

## 5. Evaluation and Reliability

- **Forecasting:** RMSE, MAE, MAPE (`evaluation.metrics.forecasting_metrics`).
- **Classification:** Accuracy, F1, ROC-AUC (`evaluation.metrics.classification_metrics`).
- **Risk:** VaR/ES error vs historical (`evaluation.metrics.risk_metrics_var_es`).
- **Reliability:** Overfitting ratio (train vs val), train/test drift (PSI), prediction stability (`evaluation.reliability`). Unreliable outputs can be flagged for review.
