# PortfolioQ — All Links

Use these after running the project (e.g. `bash scripts/run-project-e2e.sh`).

---

## Grafana (dashboards: portfolios, risk scores, reports, ML metrics)

| What        | URL |
|------------|-----|
| Login      | http://localhost:3001 |
| Dashboard  | http://localhost:3001/d/portfolioq-main |

- **Username:** `admin` (or `GRAFANA_USER` from `.env`)
- **Password:** `portfolioq_admin` (or `GRAFANA_PASSWORD` from `.env`)

---

## MLflow (experiments, runs, model registry)

| What         | URL |
|-------------|-----|
| MLflow UI   | http://localhost:5003 |
| Experiments | http://localhost:5003/#/experiments |
| Models      | http://localhost:5003/#/models |

---

## Backend API

| What     | URL |
|----------|-----|
| Health   | http://localhost:8000/health |
| Swagger  | http://localhost:8000/api/docs |
| ReDoc    | http://localhost:8000/api/redoc |
| Metrics  | http://localhost:8000/metrics |

---

## Prometheus

| What    | URL |
|---------|-----|
| UI      | http://localhost:9090 |
| Targets | http://localhost:9090/targets |

---

## API examples (Backend)

| Resource   | URL |
|------------|-----|
| Portfolios | http://localhost:8000/api/v1/portfolios/ |
| Scenarios  | http://localhost:8000/api/v1/scenarios/ |
| Reports   | http://localhost:8000/api/v1/reports/ |
| Alerts    | http://localhost:8000/api/v1/alerts/ |
| ML status | http://localhost:8000/api/v1/ml/status |

---

## Database (PostgreSQL)

- **Host:** localhost  
- **Port:** 5432  
- **Database:** portfolioq  
- **User:** portfolioq  
- **Password:** from `.env` (`POSTGRES_PASSWORD`, default `portfolioq_secure_2025`)

---

## Quick start

From the `portfolioq` directory:

```bash
bash scripts/run-project-e2e.sh
```

This starts the stack, seeds a portfolio and scenario if needed, runs one scenario (data → Grafana), triggers ML retrain (runs → MLflow), and prints these links.

Options:

- `--no-docker` — assume services are already running
- `--skip-seed` — do not create portfolio/scenario
- `--skip-retrain` — do not trigger ML retrain
