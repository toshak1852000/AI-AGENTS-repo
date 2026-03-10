#!/usr/bin/env bash
# PortfolioQ — Run project end-to-end: start stack, seed data, run scenario, capture in Grafana & MLflow.
# Usage: bash scripts/run-project-e2e.sh [--no-docker] [--skip-seed] [--skip-retrain]
#   --no-docker   : do not start/ensure Docker stack (assume already running)
#   --skip-seed   : do not create portfolio/scenario if missing
#   --skip-retrain: do not trigger ML retrain (no new MLflow runs)
# Run from repo root or from portfolioq: bash portfolioq/scripts/run-project-e2e.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
BASE_URL="${BASE_URL:-http://localhost:8000}"
BACKEND_PORT="8000"

# Parse args
NO_DOCKER=false
SKIP_SEED=false
SKIP_RETRAIN=false
for arg in "$@"; do
  case "$arg" in
    --no-docker)    NO_DOCKER=true ;;
    --skip-seed)    SKIP_SEED=true ;;
    --skip-retrain) SKIP_RETRAIN=true ;;
  esac
done

if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE" 2>/dev/null || true
  set +a
fi

GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-portfolioq_admin}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-portfolioq_secure_2025}"

echo ""
echo "=============================================="
echo "  PortfolioQ — Run Project End-to-End"
echo "  Root: $ROOT_DIR"
echo "  API:  $BASE_URL"
echo "=============================================="
echo ""

# --- 1. Start Docker stack (unless --no-docker) ---
if [ "$NO_DOCKER" = false ]; then
  echo ">>> 1. Starting Docker stack..."
  cd "$ROOT_DIR"
  docker compose up -d
  echo "    Waiting for backend to be healthy..."
  for i in {1..60}; do
    if curl -sf "$BASE_URL/health" >/dev/null 2>&1; then
      echo "    Backend is up."
      break
    fi
    if [ "$i" -eq 60 ]; then
      echo "    WARNING: Backend did not become healthy in time. Continuing anyway."
    fi
    sleep 2
  done
  echo ""
else
  echo ">>> 1. Skipping Docker (--no-docker). Assuming stack is running."
  echo ""
fi

# --- 2. Seed portfolio and scenario if none exist ---
if [ "$SKIP_SEED" = false ]; then
  echo ">>> 2. Ensuring seed data (portfolio + scenario)..."
  PF_COUNT=$(curl -sf "$BASE_URL/api/v1/portfolios/" 2>/dev/null | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  print(len(d) if isinstance(d, list) else 0)
except Exception:
  print(0)
" 2>/dev/null || echo "0")
  SC_COUNT=$(curl -sf "$BASE_URL/api/v1/scenarios/" 2>/dev/null | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  print(len(d) if isinstance(d, list) else 0)
except Exception:
  print(0)
" 2>/dev/null || echo "0")

  if [ "${PF_COUNT:-0}" -eq 0 ]; then
    curl -sf -X POST "$BASE_URL/api/v1/portfolios/" -H "Content-Type: application/json" \
      -d '{"name":"E2E Portfolio","description":"Created by run-project-e2e"}' >/dev/null 2>&1 && echo "    Created portfolio." || echo "    Could not create portfolio."
    # Add a holding so scenario run has data
    PID=$(curl -sf "$BASE_URL/api/v1/portfolios/" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d[0]['id'] if d else '')
" 2>/dev/null)
    if [ -n "$PID" ]; then
      curl -sf -X POST "$BASE_URL/api/v1/portfolios/$PID/holdings" -H "Content-Type: application/json" \
        -d '{"symbol":"AAPL","company_name":"Apple Inc","quantity":100,"average_price":150,"sector":"Technology"}' >/dev/null 2>&1 && echo "    Added holding AAPL." || true
    fi
  else
    echo "    Portfolios exist ($PF_COUNT), skipping create."
  fi

  if [ "${SC_COUNT:-0}" -eq 0 ]; then
    curl -sf -X POST "$BASE_URL/api/v1/scenarios/" -H "Content-Type: application/json" \
      -d '{"name":"E2E Market Shock","description":"Created by run-project-e2e","type":"market_shock","parameters":{"shock_pct":-0.05}}' >/dev/null 2>&1 && echo "    Created scenario." || echo "    Could not create scenario."
  else
    echo "    Scenarios exist ($SC_COUNT), skipping create."
  fi
  echo ""
else
  echo ">>> 2. Skipping seed (--skip-seed)."
  echo ""
fi

# --- 3. Run a scenario (workflow: exposure, risk, report, alerts → Grafana) ---
echo ">>> 3. Running scenario (data → Grafana)..."
PID=$(curl -sf "$BASE_URL/api/v1/portfolios/" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d[0]['id'] if d else '')
" 2>/dev/null)
SCID=$(curl -sf "$BASE_URL/api/v1/scenarios/" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d[0]['id'] if d else '')
" 2>/dev/null)

if [ -n "$PID" ] && [ -n "$SCID" ]; then
  RUN=$(curl -sf -X POST "$BASE_URL/api/v1/scenarios/$SCID/run" -H "Content-Type: application/json" \
    -d "{\"portfolio_ids\":[\"$PID\"]}" 2>/dev/null)
  STATUS=$(echo "$RUN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('status',''))
" 2>/dev/null)
  REPORT_ID=$(echo "$RUN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('report_id',''))
" 2>/dev/null)
  if [ "$STATUS" = "completed" ] && [ -n "$REPORT_ID" ]; then
    echo "    Scenario run completed. report_id=$REPORT_ID (visible in Grafana)."
  else
    echo "    Scenario run status=$STATUS report_id=$REPORT_ID"
  fi
else
  echo "    No portfolio or scenario found. Create one via API or run without --skip-seed."
fi
echo ""

# --- 4. Trigger ML retrain (new runs → MLflow) ---
if [ "$SKIP_RETRAIN" = false ]; then
  echo ">>> 4. Triggering ML retrain (runs → MLflow)..."
  curl -sf -X POST "$BASE_URL/api/v1/ml/retrain" -H "Content-Type: application/json" >/dev/null 2>&1 && \
    echo "    Retrain started (Celery). New runs will appear in MLflow when done." || echo "    Could not trigger retrain."
  echo ""
else
  echo ">>> 4. Skipping ML retrain (--skip-retrain)."
  echo ""
fi

# --- 5. Print all links ---
echo "=============================================="
echo "  PortfolioQ — All Links"
echo "=============================================="
echo ""
echo "  Grafana (dashboards: portfolios, risk, reports, ML metrics)"
echo "    URL:      http://localhost:3001"
echo "    Login:    $GRAFANA_USER / $GRAFANA_PASSWORD"
echo "    Dashboard: http://localhost:3001/d/portfolioq-main"
echo ""
echo "  MLflow (experiments, runs, model registry)"
echo "    URL:         http://localhost:5003"
echo "    Experiments: http://localhost:5003/#/experiments"
echo "    Models:      http://localhost:5003/#/models"
echo ""
echo "  Backend API"
echo "    Health:   http://localhost:${BACKEND_PORT}/health"
echo "    Swagger:  http://localhost:${BACKEND_PORT}/api/docs"
echo "    ReDoc:    http://localhost:${BACKEND_PORT}/api/redoc"
echo "    Metrics:  http://localhost:${BACKEND_PORT}/metrics"
echo ""
echo "  Prometheus"
echo "    URL:     http://localhost:9090"
echo "    Targets: http://localhost:9090/targets"
echo ""
echo "  API (examples)"
echo "    Portfolios: http://localhost:${BACKEND_PORT}/api/v1/portfolios/"
echo "    Scenarios:  http://localhost:${BACKEND_PORT}/api/v1/scenarios/"
echo "    Reports:    http://localhost:${BACKEND_PORT}/api/v1/reports/"
echo "    Alerts:     http://localhost:${BACKEND_PORT}/api/v1/alerts/"
echo "    ML status:  http://localhost:${BACKEND_PORT}/api/v1/ml/status"
echo ""
echo "  Database (PostgreSQL)"
echo "    Host: localhost  Port: 5432  DB: portfolioq  User: portfolioq"
echo "    Password: $POSTGRES_PASSWORD"
echo ""
echo "=============================================="
echo "  End-to-end run complete. Check Grafana and MLflow for captured data."
echo "=============================================="
echo ""
