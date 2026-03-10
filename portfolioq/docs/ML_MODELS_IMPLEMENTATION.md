# PortfolioQ — End-to-End ML Models Implementation

This document describes the **end-to-end machine learning implementation** in PortfolioQ: the three ML models, their significance, how they are trained and consumed, and the **architectural flow** from data to APIs and workflows.

---

## 1. Overview

PortfolioQ implements **three production ML models** that power portfolio exposure, risk scoring, and opportunity/anomaly detection:

| Model | Purpose | Algorithm | Registered name |
|-------|---------|-----------|-----------------|
| **Factor model** | Per-symbol factor betas (market, size, value, momentum, oil, gold, bonds, USD) for exposure and scenario P&L | Ridge regression (sklearn) + StandardScaler | `portfolioq_factor_scaler` |
| **Risk model** | Portfolio/holding risk score (0–1) and risk level (low / medium / high / critical) | XGBoost classifier | `portfolioq_risk_model` |
| **Opportunity model** | Anomaly detection and opportunity signals (strong_buy, buy, hold, reduce, sell) per holding | Isolation Forest (sklearn) | `portfolioq_opportunity_model` |

All models are **trained**, **logged to MLflow** (experiments, metrics, artifacts, model registry), **saved to disk** for fast load, and **used in services and workflows**. Optional **weekly retraining** runs via Celery.

---

## 2. Significance of the ML Implementation

- **Factor model**  
  - Provides **interpretable factor exposures** (betas) per symbol and at portfolio level.  
  - Drives **scenario stress-testing**: apply factor shocks (e.g. market_shock, commodity_fluctuation) to compute P&L impact.  
  - Used by **exposure service** and **reporting** for sensitivity and portfolio factor betas.

- **Risk model**  
  - Produces a **single risk score and level** per portfolio under a scenario, and supports **prioritized holdings** by impact.  
  - Feeds **alerts** (critical/high risk), **rebalancing recommendations**, **reports**, and **Grafana/Prometheus** metrics.  
  - Trained with **stratified CV** and **Optuna tuning** (optional) for robust risk classification.

- **Opportunity model**  
  - Flags **anomalous** risk/return profiles (unusual opportunities or hidden risks).  
  - Outputs **per-holding signals** (strong_buy → sell) used in risk assessment and reporting.  
  - Complements the risk model by highlighting positions that are “different” in a useful way.

Together, these models enable **automated, data-driven** exposure analysis, risk assessment, and opportunity detection without manual rule maintenance.

---

## 3. End-to-End Implementation Summary

### 3.1 Training pipeline

- **Entry point:** `train_all_models(force_retrain: bool)` in `backend/src/ml/training.py`.  
- **Flow:**  
  1. `setup_mlflow()` — set tracking URI (e.g. `http://mlflow:5003`), create experiments if missing.  
  2. For each model: if `force_retrain` then `train_*_model()`, else `get_*_model()` (load from disk or train once).  
  3. Results returned as `{ "factor_model": {...}, "risk_model": {...}, "opportunity_model": {...} }`.

### 3.2 Factor model

- **Training:** `train_factor_model(alpha=0.1)` in `factor_model.py`.  
  - Fetches factor returns (Yahoo/FRED or synthetic) and equity returns.  
  - Fits `StandardScaler` on factor returns, then one **Ridge regression per symbol** on scaled factor returns → symbol return.  
  - Logs to MLflow: params (`alpha`, `n_factors`, `equity_universe_size`), metrics (`training_duration_seconds`, `avg_r2`, `avg_rmse`, `n_models_trained`, per-symbol `r2_*`, `rmse_*`), system metrics, **artifacts**: `plots/factor_r2_per_symbol.png`, `plots/factor_metrics_per_symbol.csv`.  
  - Logs **scaler** with **signature** and **input_example** (factor returns), **registers** as `portfolioq_factor_scaler`, then **transitions** latest version to **Production** and sets **model description**.  
  - Saves to disk: `factor_model.pkl`, `factor_scaler.pkl`.

### 3.3 Risk model

- **Training:** `train_risk_model(**params)` in `risk_model.py`.  
  - Uses **synthetic** or real portfolio-style data; labels from binned risk score → `low` / `medium` / `high` / `critical`.  
  - **XGBClassifier** with Stratified 5-fold CV; metrics: `train_accuracy`, `cv_mean_accuracy`, `cv_std_accuracy`, `training_duration_seconds`, `feature_importance_*`.  
  - Logs **artifacts**: `evaluation/classification_report.txt`, `plots/feature_importance.png`, `plots/confusion_matrix.png`, system metrics.  
  - Logs **model** with **signature** and **input_example**, **registers** as `portfolioq_risk_model`, **transitions** to Production and sets **description**.  
  - Saves to disk: `risk_model.json`, `risk_label_encoder.pkl`.  
  - **Tuning:** `tune_risk_model(n_trials)` (Optuna) exposed via `POST /api/v1/ml/tune`.

### 3.4 Opportunity model

- **Training:** `train_opportunity_model()` in `opportunity_model.py`.  
  - Trains on **synthetic** portfolio-feature DataFrame (risk_score, exposure, beta, sector concentration, P&L impact, volatility, momentum/value signals).  
  - **Isolation Forest** + **StandardScaler**; metrics: `mean_anomaly_score`, `std_anomaly_score`, `anomaly_fraction`, `training_duration_seconds`.  
  - Logs **artifacts**: `plots/opportunity_anomaly_scores.png` (histogram of anomaly scores), system metrics.  
  - Logs **model** with **signature** and **input_example** (prepared features), **registers** as `portfolioq_opportunity_model`, **transitions** to Production and **description**.  
  - Saves to disk: `opportunity_model.pkl`.

### 3.5 MLflow integration

- **Experiments:** `portfolioq_factor_model`, `portfolioq_risk_scoring`, `portfolioq_opportunity_detection`.  
- **Per run:** params, performance metrics, **system metrics** (CPU %, memory used GB, memory %), **plot artifacts** (R² bar chart, anomaly histogram, feature importance, confusion matrix), **evaluation** artifacts (classification report, CSV).  
- **Model registry:** all three models registered with **signature** and **input_example**; latest version **auto-transitioned to Production**; **descriptions** set for discoverability in the Models UI.  
- **Tracking URI:** configurable via `MLFLOW_TRACKING_URI` (default `http://mlflow:5003`).  
- **Helpers:** `mlflow_tracker.run_context`, `log_system_metrics`, `transition_registered_model_to_production`, `load_registered_model` (for loading by name/stage).

---

## 4. Architectural Flow

### 4.1 High-level flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA & TRAINING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Yahoo/FRED / Synthetic  →  Factor model (Ridge + scaler)                    │
│  Synthetic portfolio     →  Risk model (XGBoost)                              │
│  Synthetic portfolio     →  Opportunity model (Isolation Forest)               │
│                                                                               │
│  Each training run → MLflow (params, metrics, system metrics, artifacts)      │
│                   → Model Registry (signature, input_example, Production)    │
│                   → Disk (joblib/XGB for fast load)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RUNTIME: LOAD & SERVE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  get_factor_model() / get_risk_model() / get_opportunity_model()              │
│  → Load from disk if present; else train once (and optionally log to MLflow) │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          ▼                             ▼                             ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│ Exposure service │         │ Risk service     │         │ API endpoints    │
│ (exposure_       │         │ (risk_service.   │         │ /ml/status,      │
│  service.py)     │         │  assess_risk)     │         │ /score,           │
│                  │         │                  │         │ /factor-betas,    │
│ Factor model     │         │ Risk model       │         │ /train, /retrain,│
│ → portfolio_     │         │ → risk_score,    │         │ /tune, /mlflow-url│
│   sensitivity,   │         │   risk_level,    │         │                  │
│   factor_betas   │         │   prioritized   │         │                  │
│                  │         │   holdings       │         │                  │
│                  │         │ Opportunity model│         │                  │
│                  │         │ → per-holding    │         │                  │
│                  │         │   signals        │         │                  │
└────────┬─────────┘         └────────┬─────────┘         └──────────────────┘
         │                            │
         ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     WORKFLOWS & DOWNSTREAM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Scenario run:                                                                │
│    market_data → exposure_calculation_node (factor model)                      │
│                → risk_assessment_node (risk + opportunity models)             │
│                → report_generation_node (risk_score, etc.)                     │
│  Alerts: risk_service + alert_service (critical/high risk_score)               │
│  Rebalancing: rebalancing_service (risk_score, risk_level)                    │
│  Reports/Excel: report_service (risk_score, sensitivity_score, signals)       │
│  Prometheus: portfolioq_portfolio_risk_score                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Training triggers

- **On-demand:** `POST /api/v1/ml/train` (optional `force_retrain=true`), `POST /api/v1/ml/retrain` (always force).  
- **Scheduled:** Celery Beat task `retrain_all_models` (weekly) calls `train_all_models(force_retrain=True)`.  
- **Startup:** Backend can run `train_all_models(force_retrain=False)` to load or train once.

### 4.3 Inference flow (scenario analysis)

1. **Market data** (prices, scenario) and **holdings** are prepared.  
2. **Exposure:** `exposure_service.calculate_exposure()` uses **factor model** → `portfolio_sensitivity()` → company/sector exposures, **portfolio_factor_betas**, **sensitivity_score**, per-holding **factor_betas** and scenario P&L.  
3. **Risk:** `risk_service.assess_risk()` builds a **feature vector** from exposure + scenario (total_exposure_pct, market_beta, scenario_severity, sector_concentration, etc.) → **risk model** → **risk_score**, **risk_level**.  
4. **Opportunity:** For each prioritized holding, **opportunity model** `score_holding()` is called with risk_score, exposure, beta, P&L impact, etc. → **anomaly_score**, **signal** (strong_buy … sell), **opportunity_score**.  
5. Results are **persisted** (e.g. `RiskScore` table), and flow into **reports**, **alerts**, and **rebalancing**.

### 4.4 Key files

| Layer | Files |
|-------|--------|
| Training pipeline | `backend/src/ml/training.py` |
| Factor model | `backend/src/ml/factor_model.py` |
| Risk model | `backend/src/ml/risk_model.py` |
| Opportunity model | `backend/src/ml/opportunity_model.py` |
| MLflow utilities | `backend/src/ml/mlflow_tracker.py` |
| API | `backend/src/api/v1/endpoints/ml.py` |
| Exposure (factor) | `backend/src/services/exposure_service.py` |
| Risk + opportunity | `backend/src/services/risk_service.py` |
| Workflow nodes | `backend/src/workflows/nodes/exposure_calculation.py`, `risk_assessment.py` |
| Celery retrain | `backend/src/tasks/ml_tasks.py` |

---

## 5. Summary

- **Three models** are implemented end-to-end: **factor** (Ridge + scaler), **risk** (XGBoost), **opportunity** (Isolation Forest).  
- They provide **exposure/sensitivity**, **risk score/level**, and **opportunity/anomaly signals** used across exposure, risk, alerts, rebalancing, and reporting.  
- **MLflow** is used for experiments, metrics, system metrics, plot and evaluation artifacts, and a **complete model registry** (signature, input example, Production stage, descriptions).  
- **Architectural flow** is: data → training → MLflow + disk → singleton getters → exposure/risk services and API → scenario workflows, alerts, and reports.

For links (MLflow UI, API docs, Grafana, etc.), see [LINKS.md](LINKS.md).
