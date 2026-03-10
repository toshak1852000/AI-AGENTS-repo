# PortfolioQ — End-to-End Project Documentation

**Document purpose:** Record of all work done on the PortfolioQ project from initial state to current production-ready system.

---

## 1. Project Overview

**PortfolioQ** is an **Autonomous Market & Portfolio Scenario Analyst** — an enterprise-grade system that:

- Evaluates portfolio exposure to market events, commodity fluctuations, and regulatory changes
- Identifies how scenarios affect individual holdings and sectors
- Detects emerging risks and strategic opportunities using ML
- Generates automated, board-ready scenario reports
- Tracks scenario triggers and provides real-time alerts
- Provides portfolio sensitivity modeling, risk scoring, and scenario-based rebalancing recommendations

**Tech stack:** FastAPI, PostgreSQL, Redis, Celery, LangGraph, SQLAlchemy, scikit-learn, XGBoost, MLflow, Prometheus, Grafana. All services run via Docker Compose.

---

## 2. Initial State (Before Full Implementation)

At the start of the work, the project had:

- **API structure:** FastAPI with routes for portfolios, scenarios, exposure, reports, alerts
- **Workflow:** LangGraph pipeline (data_collection → exposure_calculation → risk_assessment → report_generation) with **stub nodes** returning placeholder data
- **Schemas:** Pydantic + SQLAlchemy models **commented out** (no DB persistence)
- **Docker Compose:** Postgres, Redis, backend, Celery worker/beat — but services used `localhost` for DB/Redis (broken in containers)
- **No** real market data integrations, exposure logic, risk scoring, report generation, or alerts
- **No** ML models, MLflow, or monitoring dashboards

A **Resume Gap Analysis** (`docs/RESUME_GAP_ANALYSIS_AND_ML.md`) was created to map resume claims to the codebase and list what remained.

---

## 3. Work Done End-to-End

### 3.1 Environment & Prerequisites

- **Virtual environment:** Python `venv` created at project root; user guided to install `python3-venv` where needed
- **Docker & Docker Compose:** Install script added at `scripts/install-docker.sh` for Ubuntu (run with `sudo`); deprecated `version` key removed from Compose files
- **Node.js 18+:** Documented use of `nvm` for install without `sudo`
- **Docker connectivity:** `docker-compose.yml` and `docker-compose.example.yml` updated so backend and Celery use service hostnames `postgres` and `redis` instead of `localhost` for `DATABASE_URL`, `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- **Backend `.dockerignore`:** Added to keep builds fast and exclude venv, cache, env files

### 3.2 Database Layer

- **Core module:** `backend/src/core/database.py` — SQLAlchemy engine, `SessionLocal`, `get_db()`, `Base`, `create_tables()`
- **Models uncommented and implemented:**
  - `models/portfolio.py` — Portfolio, Holding
  - `models/scenario.py` — Scenario, ScenarioRun
  - `models/market_data.py` — MarketData, CommodityPrice
  - `models/exposure.py` — Exposure, RiskScore
  - `models/report.py` — Report
  - `models/alert.py` — Alert
- **Alembic:** `alembic/env.py` updated to import `Base` and all models; migrations can be run with `DATABASE_URL` from environment
- **Startup:** `main.py` lifespan calls `create_tables()` so tables exist on first run

**Database:** PostgreSQL only; no port changes (5432).

### 3.3 Market Data Integrations

- **Yahoo Finance** (`integrations/yahoo_finance.py`): `fetch_price_history`, `fetch_current_price`, `fetch_factor_returns`, `fetch_multiple_symbols`, `get_symbol_info`; retries via tenacity
- **FRED** (`integrations/fred.py`): `fetch_series`, `fetch_macro_indicators` (fed funds, CPI, unemployment, Treasury, oil, etc.) using `FRED_API_KEY`
- **Alpha Vantage** (`integrations/alpha_vantage.py`): `fetch_daily_adjusted`, `fetch_sector_performance` using `ALPHA_VANTAGE_API_KEY`

When external APIs are unreachable (e.g. in isolated Docker), the factor model falls back to **synthetic training data** so the pipeline still runs.

### 3.4 Machine Learning Models

- **Factor model** (`ml/factor_model.py`): Ridge regression per symbol for 8 factors (market, small_cap, value, momentum, oil, gold, bonds, usd). Sector default betas for symbols not in training set. Scenario shock definitions per scenario type. Training on yfinance or synthetic data; persisted under `MODEL_STORE`; logged to MLflow (experiment `portfolioq_factor_model`).
- **Risk model** (`ml/risk_model.py`): XGBoost classifier for risk level (low/medium/high/critical) from exposure/portfolio features. Synthetic training data generator; cross-validation; feature importance and metrics logged to MLflow (`portfolioq_risk_scoring`). Model registered as `portfolioq_risk_model`.
- **Opportunity model** (`ml/opportunity_model.py`): Isolation Forest for anomaly detection; produces opportunity signals (strong_buy, buy, hold, reduce, sell). Trained on synthetic portfolio features; logged to MLflow (`portfolioq_opportunity_detection`).
- **LLM service** (`ml/llm_service.py`): Board-ready narrative generation via OpenAI (when `OPENAI_API_KEY` set) or template fallback. Used in report generation.
- **MLflow tracker** (`ml/mlflow_tracker.py`): `setup_mlflow`, run context, system metrics (CPU, memory), model logging (sklearn, xgboost), experiments for factor/risk/opportunity.
- **Training pipeline** (`ml/training.py`): `train_all_models(force_retrain)` trains all three models and saves to disk.
- **Hyperparameter tuning:** Optuna in `risk_model.tune_risk_model(n_trials)`; exposed via `POST /api/v1/ml/tune`.

All models are loaded or trained on backend startup so the API and workflow use fitted models.

### 3.5 Business Logic Services

- **Market data service** (`services/market_data_service.py`): `fetch_and_store_prices`, `get_latest_prices`, `get_price_history`, `collect_scenario_market_data` for workflow
- **Exposure service** (`services/exposure_service.py`): `calculate_exposure` — uses factor model for portfolio/holding sensitivity, company- and sector-level exposure, risk score; persists Exposure to DB
- **Risk service** (`services/risk_service.py`): `assess_risk` — builds feature vector, calls risk model and opportunity model, prioritizes holdings, persists RiskScore; creates per-holding signals
- **Report service** (`services/report_service.py`): `generate_report` — narrative via LLM/template, summary JSON; exports JSON, PDF (reportlab), Excel (openpyxl); persists Report
- **Alert service** (`services/alert_service.py`): `create_alert`, `evaluate_and_create_alerts` (risk level, sector concentration, P&L impact, high-risk holdings), `list_alerts`, `mark_alert_read`
- **Rebalancing service** (`services/rebalancing_service.py`): `generate_rebalancing_recommendations` — holding- and sector-level actions (buy/sell/reduce) and rationale

### 3.6 Workflow Implementation (LangGraph)

Stub nodes replaced with real implementations:

- **data_collection_node:** Loads scenario and portfolio holdings from DB; calls `collect_scenario_market_data`; passes market_data + holdings to next node
- **exposure_calculation_node:** Calls `calculate_exposure` per portfolio; merges company/sector exposures and factor betas; returns exposure_result
- **risk_assessment_node:** Calls `assess_risk` with exposure_result and market_data; returns risk_result (scores, prioritized_holdings with signals)
- **report_generation_node:** Generates rebalancing recommendations; calls `generate_report` (report format from scenario parameters: json/pdf/excel, default json); calls `evaluate_and_create_alerts`; updates Prometheus metrics; returns report_id and status completed/failed

Workflow invoked from `POST /api/v1/scenarios/{id}/run`; state and report_id persisted via ScenarioRun and Report.

### 3.7 API Endpoints

All endpoints implemented with DB and error handling:

- **Portfolios:** GET/POST /portfolios, GET/PUT/DELETE /portfolios/{id}, GET/POST/DELETE holdings, GET /portfolios/{id}/rebalancing-recommendations, POST refresh-prices
- **Scenarios:** GET/POST /scenarios, GET/PUT/DELETE /scenarios/{id}, POST /scenarios/{id}/run, GET /scenarios/{id}/runs
- **Exposure:** GET exposure by portfolio/scenario, POST /exposure/calculate, GET risk-scores by portfolio
- **Reports:** GET list (filter by portfolio/scenario), GET report by id, GET download, POST generate
- **Alerts:** GET list (portfolio, unread), GET by id, PUT read, GET summary/counts
- **ML:** GET status, POST train, POST retrain, POST tune, POST score, POST factor-betas, GET mlflow-url

Root: `/`, `/health`, `/metrics` (Prometheus). OpenAPI at `/api/docs`, `/api/redoc`.

### 3.8 Celery Tasks

- **celery_tasks.py:** App and beat schedule
- **market_data_tasks.py:** `refresh_all_prices` — refresh holding prices (cron hourly)
- **scenario_tasks.py:** `run_all_scheduled_scenarios` (daily), `run_single_scenario` (on-demand)
- **alert_tasks.py:** `check_alert_thresholds` (every 30 min)
- **ml_tasks.py:** `retrain_all_models` (weekly)

### 3.9 Monitoring & Observability

- **Prometheus** (`analytics/metrics.py`): Counters/histograms/gauges for API requests, scenario runs, portfolio risk/PL, alerts, reports, ML predictions/inference, market data fetches. Exposed at `/metrics`.
- **Prometheus config:** `monitoring/prometheus/prometheus.yml` — scrape backend metrics.
- **Grafana:** Service in docker-compose (port 3001). Provisioned datasources (Prometheus, PostgreSQL) and dashboard `portfolioq.json` — portfolios/holdings counts, alerts, scenario runs, risk scores table, sector exposure, API latency, ML metrics, top holdings. **For accurate dashboard data,** the PostgreSQL password in `monitoring/grafana/provisioning/datasources/datasources.yml` must match `POSTGRES_PASSWORD` in `.env` (default `portfolioq_secure_2025`).
- **MLflow:** Service in docker-compose (port 5003); PostgreSQL backend (same DB as application, end-to-end). Experiments: portfolioq_factor_model, portfolioq_risk_scoring, portfolioq_opportunity_detection. Runs log params, metrics, `training_duration_seconds`, system metrics, and artifacts (factor_scaler, risk_clf, opportunity_detector, classification report, feature importance plot). Model Registry: `portfolioq_risk_model`, `portfolioq_factor_scaler`, `portfolioq_opportunity_model`. Risk model runs include signature and input example.

Docker ports kept as requested (e.g. 8000, 5432, 6379, 5003, 3001, 9090).

### 3.10 Docker Stack

- **docker-compose.yml:** postgres, redis, mlflow, prometheus, grafana, backend, celery_worker, celery_beat. Volumes for postgres_data, redis_data, mlflow_artifacts, mlflow_db, prometheus_data, grafana_data, ml_models, reports. Backend/Celery env: DATABASE_URL, REDIS_URL, MLFLOW_TRACKING_URI, MODEL_STORE, REPORTS_DIR, API keys. No port changes from original design.
- **Backend Dockerfile:** Python 3.11, system deps, pip install from requirements.txt, /app/ml_models and /app/reports created.

### 3.11 Scripts

- **show-services.sh:** Prints Grafana URL and password, Backend/MLflow/Prometheus/PostgreSQL URLs and credentials, API examples, optional health check. Reads from `portfolioq/.env`.
- **validate-all-apis.sh:** Full API validation — portfolios (list, create, get, holdings), scenarios (list, create, get), scenario run (workflow), reports (list, get, download), exposure (by portfolio, calculate, risk-scores), alerts (list, summary/counts), ML (status, score, factor-betas), rebalancing-recommendations. Run: `bash scripts/validate-all-apis.sh [BASE_URL]`.
- **check-ml-models.sh:** Validates GET /ml/status, POST /ml/score, POST /ml/factor-betas, GET mlflow-url, POST train/retrain/tune; checks response shape and value ranges.
- **validate-ml-models-e2e.sh:** Phase 1 — ML status and score/factor-betas APIs; Phase 2 — run one scenario (full pipeline); Phase 3 — fetch report and validate risk_assessment, exposure_summary, top_holdings_at_risk.
- **run-all.sh:** Runs show-services.sh, validate-all-apis.sh, check-ml-models.sh, validate-ml-models-e2e.sh in sequence (from portfolioq root). Optional BASE_URL argument. Full API and workflow validation in one command.

### 3.12 Configuration & Dependencies

- **requirements.txt:** FastAPI, uvicorn, SQLAlchemy, psycopg2-binary, alembic, redis, celery, pandas, numpy, scipy, scikit-learn, xgboost, lightgbm, optuna, mlflow, yfinance, alpha-vantage, requests, langgraph, langchain, reportlab, openpyxl, prometheus-client, psutil, tenacity, pytest, etc.
- **.env:** POSTGRES_*, REDIS_*, CELERY_*, SECRET_KEY, GRAFANA_USER/PASSWORD, MLFLOW_TRACKING_URI, MODEL_STORE, REPORTS_DIR, optional API keys (ALPHA_VANTAGE, FRED, OPENAI).

---

## 4. Resume / Capability Alignment

The following resume points are now implemented end-to-end:

| Capability | Implementation |
|------------|----------------|
| Evaluate portfolio exposure to market, commodity, regulatory changes | Factor model + exposure_service; scenario types and shocks in factor_model; company/sector exposure in report |
| Identify how scenarios affect individual holdings and sectors | exposure_calculation_node → company_exposures, sector_exposures; report and exposure API |
| Detect emerging risks and strategic opportunities | risk_service + risk model + opportunity model; prioritized_holdings with signals |
| Generate automated, actionable insights | report_service (PDF/Excel/JSON), executive summary, recommendations |
| Track scenario triggers and real-time notifications | Alerts created in report_generation_node; alert API and Celery check_alert_thresholds |
| Automated portfolio sensitivity modeling | Factor betas and scenario shocks; portfolio_sensitivity in factor_model |
| Market factor and regulatory impact assessment | Factor model + scenario types (e.g. regulatory_change); risk_service features |
| Quantitative and qualitative data integration | Yahoo/FRED/Alpha Vantage; LLM narrative (qualitative) in reports |
| Scenario-driven risk scoring and prioritization | risk_model + risk_service; prioritized_holdings; risk_scores table |
| Scalable, repeatable, audit-ready pipelines | LangGraph workflow; DB persistence of runs, exposures, reports, alerts |
| Board-ready scenario reports | report_service + LLM/template; PDF/Excel/JSON |
| Continuous monitoring workflows | Celery beat: refresh prices, scheduled scenarios, alert thresholds, weekly ML retrain |
| Portfolio Sensitivity Scores | exposure_result.sensitivity_score, factor betas; exposure API |
| Company-Level Exposure Analysis | company_exposures in exposure_result and report |
| Stress-Tested P&L Impact | scenario_pl_impact per holding and portfolio; risk_result.pl_impact |
| Risk & Opportunity Signal Frequency | Alerts; opportunity model signals (strong_buy, buy, hold, reduce, sell) |
| Scenario-Based Rebalancing Recommendations | rebalancing_service; holding_recommendations, sector_recommendations in report; GET /portfolios/{id}/rebalancing-recommendations |

---

## 5. How to Run and Validate

- **Start stack:** From `portfolioq`: `docker compose up -d`
- **Services:** Backend http://localhost:8000, MLflow http://localhost:5003, Grafana http://localhost:3001 (admin / portfolioq_admin), Prometheus http://localhost:9090
- **Run all validations:** From `portfolioq`: `bash scripts/run-all.sh` — runs show-services, validate-all-apis (all REST endpoints + workflow), check-ml-models, and validate-ml-models-e2e. Ensures every component and API is operational.
- **Full API validation only:** `bash scripts/validate-all-apis.sh [BASE_URL]` — portfolios, scenarios, exposure, reports, alerts, ML, rebalancing; 20 checks.
- **ML only:** `bash scripts/check-ml-models.sh`, `bash scripts/validate-ml-models-e2e.sh`
- **Show credentials/URLs:** `bash scripts/show-services.sh`
- **Validation summary:** See [VALIDATION_SUMMARY.md](VALIDATION_SUMMARY.md) for resume-point-to-implementation mapping and latest validation results (all 35 checks passing).

---

## 6. Summary

Work carried out on PortfolioQ from start to current state includes: fixing Docker and DB connectivity; implementing the full database layer with PostgreSQL; adding market data integrations (Yahoo, FRED, Alpha Vantage); implementing three ML models (factor, risk, opportunity) with MLflow and optional hyperparameter tuning; implementing all business services (market data, exposure, risk, report, alert, rebalancing); replacing all workflow stubs with real logic; implementing all API endpoints with persistence; adding Celery tasks for monitoring and retraining; adding Prometheus metrics and Grafana dashboards; and adding scripts for services info and ML/project-wide validation. The system is operational end-to-end, uses PostgreSQL throughout, keeps Docker ports unchanged, and fulfils the resume capabilities listed above.
