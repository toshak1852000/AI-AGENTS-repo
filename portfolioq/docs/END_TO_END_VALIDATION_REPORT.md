# PortfolioQ — End-to-End Validation Report

**Purpose:** Complete QA/MLOps validation of the platform: pipelines, services, APIs, monitoring, ML, and infrastructure.  
**Constraints:** PostgreSQL used end-to-end (app + MLflow); Docker ports unchanged.

---

## Quick validation commands

Run the full 18-step validation (starts Docker, runs all checks, writes report):

```bash
cd portfolioq
bash scripts/validate-system-e2e.sh --report
```

Run with stack already up:

```bash
bash scripts/validate-system-e2e.sh http://localhost:8000 --no-docker --report
```

Validate APIs only (backend must be running):

```bash
bash scripts/validate-all-apis.sh
```

Validate ML models E2E:

```bash
bash scripts/validate-ml-models-e2e.sh
```

---

## Step-by-step verification

### STEP 1 — Project structure

| Check | Command / location |
|-------|--------------------|
| Required dirs | `backend/`, `configs/`, `scripts/`, `docs/`, `monitoring/` |
| Config files | `configs/config.yaml`, `configs/model_params.yaml`, `configs/mlflow_config.yaml` |
| Env | `.env` (from `.env.example`), `backend/requirements.txt` |
| Scripts | `scripts/validate-all-apis.sh`, `scripts/validate-ml-models-e2e.sh`, `scripts/validate-system-e2e.sh`, `scripts/check-ml-models.sh` |

```bash
[ -d backend ] && [ -d configs ] && [ -f docker-compose.yml ] && [ -f .env ] && echo "Structure OK"
```

---

### STEP 2 — Dependencies

| Check | Command |
|-------|---------|
| Python deps | `cd backend && pip install -r requirements.txt && python -c "import fastapi, sqlalchemy, mlflow, xgboost, sklearn"` |
| Docker | `docker --version && docker compose version` |
| Backend deps | Installed via `requirements.txt` in image; for local pytest use venv |

---

### STEP 3 — Configuration

| Check | Verified |
|-------|----------|
| `config.yaml` | Present; project, data, ml_models, api, mlflow experiments |
| `database.py` | Enforces `DATABASE_URL` must start with `postgresql` |
| Docker Compose | PostgreSQL 5432, MLflow 5003, Backend 8000; `MLFLOW_BACKEND_STORE_URI=postgresql://...` (same DB) |
| `.env` | `POSTGRES_*`, `DATABASE_URL`, `MLFLOW_TRACKING_URI`, `MLFLOW_BACKEND_STORE_URI` (optional, silences config warning) |

```bash
grep -q "postgresql" docker-compose.yml && grep -q "postgresql" backend/src/core/database.py && echo "PostgreSQL config OK"
```

---

### STEP 4 — Data pipeline

| Check | Location |
|-------|----------|
| Services | `backend/src/services/` (market_data, exposure, risk, report, alert) |
| Ingestion | `backend/src/integrations/` (yahoo_finance, alpha_vantage, fred) |
| Validation | `backend/src/data_validation/` (schema, clean, drift) |
| Feature eng | `backend/src/feature_engineering/` |

Data loading and schema validation are exercised when running scenario runs and ML training (steps 5 and 9).

---

### STEP 5 — ML training pipeline

| Check | How |
|-------|-----|
| Train | `POST /api/v1/ml/train?force_retrain=false` → status `training_started` or `training_complete` |
| Retrain | `POST /api/v1/ml/retrain` → status `retraining_started` |
| Script | `cd backend && python pipelines/training_pipeline.py` (with venv deps) |

---

### STEP 6 — Model performance

| Check | How |
|-------|-----|
| All fitted | `GET /api/v1/ml/status` → factor_model.fitted, risk_model.fitted, opportunity_model.fitted all true |
| Risk score | `POST /api/v1/ml/score` with body `{"portfolio_id":"","scenario_type":"market_shock"}` → risk_score in [0,1], risk_level in low/medium/high/critical |

---

### STEP 7 — Experiment tracking (MLflow)

| Check | Command |
|-------|---------|
| Health | `curl -s http://localhost:5003/health` |
| Experiments | `curl -s http://localhost:5003/api/2.0/mlflow/experiments/list` → has `experiments` (after at least one run) |
| UI | Open http://localhost:5003 |

---

### STEP 8 — Model registry

| Check | Command |
|-------|---------|
| Registry API | `curl -s http://localhost:5003/api/2.0/mlflow/registered-models/list` |
| Models | After training: `portfolioq_risk_model`, `portfolioq_factor_scaler`, `portfolioq_opportunity_model` |

---

### STEP 9 — API and inference

| Check | Script |
|-------|--------|
| Portfolios, scenarios, exposure, reports, alerts, ML | `bash scripts/validate-all-apis.sh` |
| ML E2E | `bash scripts/validate-ml-models-e2e.sh` |

Inference: `POST /api/v1/ml/score`, `POST /api/v1/ml/score/batch`, `POST /api/v1/ml/factor-betas`, `POST /api/v1/ml/scenario-simulation`.

---

### STEP 10 — Monitoring

| Check | Command |
|-------|---------|
| Prometheus | `curl -s http://localhost:9090/-/healthy` |
| Grafana | `curl -s http://localhost:3001/api/health` |
| Backend metrics | `curl -s http://localhost:8000/metrics` → Prometheus format (e.g. `api_requests_total`, `request_duration_seconds`) |

---

### STEP 11 — Dashboards

| Check | How |
|-------|-----|
| Grafana | http://localhost:3001 (admin / portfolioq_admin) |
| Dashboard | Provisioned `portfolioq.json` (uid: portfolioq-main); datasources: Prometheus, PostgreSQL (password must match `POSTGRES_PASSWORD` in `.env`) |

---

### STEP 12 — Docker and infrastructure

| Check | Command |
|-------|---------|
| Config | `docker compose config` (no port changes) |
| Up | `docker compose up -d` |
| Services | `docker compose ps` → postgres, redis, mlflow, backend, celery_worker, celery_beat, prometheus, grafana |
| Ports | 5432 (Postgres), 6379 (Redis), 5003 (MLflow), 8000 (Backend), 9090 (Prometheus), 3001 (Grafana) |

---

### STEP 13 — Alerting

| Check | How |
|-------|-----|
| List | `GET /api/v1/alerts/` → list |
| Summary | `GET /api/v1/alerts/summary/counts` → dict |
| Model | `backend/src/models/alert.py`, `backend/src/services/alert_service.py`, `backend/src/tasks/alert_tasks.py` |

---

### STEP 14 — Output validation

| Check | How |
|-------|-----|
| Report | After scenario run: `GET /api/v1/reports/{report_id}` → summary with risk_assessment, exposure_summary, top_holdings_at_risk |
| Predictions | ML score and factor-betas responses match expected schema (risk_score, risk_level, symbols with factor betas) |

---

### STEP 15 — Edge cases

| Check | How |
|-------|-----|
| Invalid scenario run | `POST /api/v1/scenarios/nonexistent-id/run` → 404/422/500 |
| ML score edge | `POST /api/v1/ml/score` with empty portfolio_id → no crash; valid or error response |

---

### STEP 16 — Load (light)

| Check | How |
|-------|-----|
| Multiple health | `for i in 1 2 3; do curl -s http://localhost:8000/health; done` |
| ML status | `curl -s http://localhost:8000/api/v1/ml/status` under normal load |

---

### STEP 17 — Security

| Check | Verified |
|-------|----------|
| `.env` | Not commit placeholder secrets; SECRET_KEY and POSTGRES_PASSWORD set |
| `.gitignore` | `.env` should be ignored |
| API | No auth in default setup; add auth for production |

---

### STEP 18 — Final system health

Run the full script and ensure **0 failures**:

```bash
bash scripts/validate-system-e2e.sh --report
# Expect: Result: N passed, 0 failed, M warnings
```

Report path: `docs/SYSTEM_VALIDATION_REPORT.md` (when run with `--report`).

---

## Summary table

| Step | Area | Status (when stack is up) |
|------|------|---------------------------|
| 1 | Project structure | All required dirs and files present |
| 2 | Dependencies | requirements.txt; Docker; venv for local pytest |
| 3 | Configuration | config.yaml, PostgreSQL enforced, ports and MLflow backend correct |
| 4 | Data pipeline | Services, ingestion, validation, feature code present; exercised by training and scenario run |
| 5 | ML training | /ml/train, /ml/retrain respond; training_pipeline.py runs in container |
| 6 | Model performance | All models fitted; risk score and level valid |
| 7 | Experiment tracking | MLflow health OK; experiments list after runs |
| 8 | Model registry | Registry API; models appear after training |
| 9 | API and inference | validate-all-apis.sh + validate-ml-models-e2e.sh |
| 10 | Monitoring | Prometheus, Grafana, /metrics |
| 11 | Dashboards | Grafana + portfolioq dashboard |
| 12 | Docker | compose config valid; all services up; ports unchanged |
| 13 | Alerting | /alerts/, /alerts/summary/counts |
| 14 | Outputs | Report schema; ML response schema |
| 15 | Edge cases | Invalid scenario and edge ML input handled |
| 16 | Load | Health and ML status under light load |
| 17 | Security | .env and secrets; production auth recommended |
| 18 | Final report | 0 failures; report generated with --report |

---

## Detected risks and recommendations

1. **MLflow experiments/registry empty** until at least one training run has completed (backend startup or `POST /api/v1/ml/retrain`). Run retrain once after stack is up, then re-check steps 7 and 8.
2. **Grafana PostgreSQL datasource** password in `monitoring/grafana/provisioning/datasources/datasources.yml` is hardcoded; must match `POSTGRES_PASSWORD` in `.env` for dashboard queries to work.
3. **Local pytest** requires a venv with `pip install -r backend/requirements.txt`; in CI/Docker, tests run inside the backend image.
4. **API auth** is not implemented; add authentication/authorization for production.

---

*Generated for PortfolioQ end-to-end validation. Re-run: `bash scripts/validate-system-e2e.sh --no-docker --report`*
