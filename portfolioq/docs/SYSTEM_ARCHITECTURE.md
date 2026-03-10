# PortfolioQ — System Architecture

Production-grade **Autonomous Market & Portfolio Scenario Analysis Platform** with clear separation of layers.

---

## 1. Architecture Overview

The system is designed as **modular components** aligned with enterprise and hedge-fund best practices:

| Layer | Description | Location |
|-------|-------------|----------|
| **1. Data Layer** | Raw and processed market data; ingestion from financial APIs, macro, commodity, portfolio holdings | `data/`, `backend/src/ingestion/`, `backend/src/integrations/` |
| **2. Feature Engineering** | Volatility, sector exposure, factor features, rolling statistics, correlation | `backend/src/feature_engineering/` |
| **3. ML Model Layer** | Factor (Ridge), Risk (XGBoost), Opportunity (Isolation Forest); training, versioning, registry | `backend/src/ml/` |
| **4. Scenario Simulation Engine** | Market shocks, commodity/rate/geopolitical/regulatory scenarios; P&L impact, exposure, sector vulnerability | `backend/src/scenario_engine/` |
| **5. Risk Analytics Engine** | Portfolio and holding risk scores; ML + rule-based logic; confidence intervals | `backend/src/risk_scoring/`, `backend/src/services/risk_service.py` |
| **6. Insight Generation** | Reports (PDF/Excel/JSON), alerts, rebalancing recommendations, board-ready output | `backend/src/services/report_service.py`, `alert_service.py`, `rebalancing_service.py`, `llm_service.py` |
| **7. Monitoring & Governance** | Data/model drift, prediction anomalies, risk threshold breaches, alerts | `backend/src/monitoring/`, `backend/src/analytics/`, Grafana/Prometheus |
| **8. Deployment APIs** | REST (FastAPI), batch prediction, scenario simulation, workflow trigger | `backend/src/api/`, `POST /scenarios/{id}/run` |

---

## 2. Data Flow

```
Data sources (Yahoo, FRED, Alpha Vantage)
    → Ingestion (ingestion/connectors, market_data_service)
    → Validation (data_validation: schema, clean, drift)
    → Feature engineering (volatility, factors, portfolio features)
    → ML models (factor, risk, opportunity) & Scenario engine
    → Risk engine + Insight generation (reports, alerts)
    → Monitoring (drift, thresholds) → Alerts
```

- **Scenario run (full workflow):** `POST /scenarios/{id}/run` → data_collection → exposure_calculation → risk_assessment → report_generation (persisted to DB, report downloadable).
- **Batch and scenario-only:** `POST /ml/score/batch`, `POST /ml/scenario-simulation` for API-driven analytics without DB.

---

## 3. Project Structure (Aligned with Spec)

```
portfolioq/
├── data/
│   ├── raw_market_data/
│   └── processed_data/
├── configs/
│   ├── config.yaml
│   └── model_params.yaml
├── backend/
│   ├── src/
│   │   ├── ingestion/          # Data ingestion facade
│   │   ├── data_validation/    # Schema, clean, drift
│   │   ├── feature_engineering/
│   │   ├── portfolio_modeling/ # (exposure_service + factor model)
│   │   ├── scenario_engine/
│   │   ├── risk_scoring/
│   │   ├── ml_models/          # (ml/: factor, risk, opportunity)
│   │   ├── evaluation/
│   │   ├── monitoring/
│   │   ├── api/, services/, workflows/, integrations/
│   ├── pipelines/
│   │   ├── training_pipeline.py
│   │   ├── scenario_pipeline.py
│   │   └── monitoring_pipeline.py
│   └── tests/
├── artifacts/
├── monitoring/                 # Prometheus, Grafana dashboards
├── docker-compose.yml
├── README.md
```

---

## 4. Key Design Decisions

- **Single codebase:** New modules (ingestion, data_validation, feature_engineering, scenario_engine, risk_scoring, evaluation, monitoring) live alongside existing services; workflows and APIs call existing logic so nothing is duplicated and everything stays operational.
- **Config:** `configs/config.yaml` and `configs/model_params.yaml` drive pipelines and model params; backend still uses `.env` for secrets and URLs.
- **Reproducibility:** MLflow for experiment tracking, dataset/model versioning, and model registry; reproducible seeds in training and evaluation.
- **Automation:** Training pipeline (single command), scenario pipeline (engine-only or full workflow via API), monitoring pipeline (drift and risk breach); Celery for scheduled ingestion, retrain, and alerts.

---

## 5. Dashboards

Outputs are prepared for dashboards (Grafana provisioning under `monitoring/grafana/`):

- **Portfolio exposure maps:** Company and sector exposures from exposure_result and scenario_engine `company_exposures` / `sector_vulnerability`.
- **Scenario impact charts:** `portfolio_pl_impact`, `portfolio_return_pct`, and per-holding `scenario_pl_impact` from scenario runs and reports.
- **Risk heatmaps:** Risk score and risk level from risk_service; Prometheus metric `portfolioq_portfolio_risk_score`.
- **Sector vulnerability:** `sector_vulnerability` from scenario_engine (P&L % by sector) for sector vulnerability analysis.

---

See **DATA_PIPELINES.md**, **MODEL_METHODOLOGY.md**, **SCENARIO_ENGINE_DESIGN.md**, and **RISK_SCORING_METHODOLOGY.md** for detailed documentation.
