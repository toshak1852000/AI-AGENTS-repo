#!/usr/bin/env bash
# PortfolioQ — show all service URLs, Grafana password, and quick status.
# Run from repo root: bash scripts/show-services.sh  (or from portfolioq: bash scripts/show-services.sh)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

# Defaults (override from .env if present)
GRAFANA_USER="admin"
GRAFANA_PASSWORD="portfolioq_admin"
BACKEND_PORT="8000"
POSTGRES_PASSWORD="portfolioq_secure_2025"

if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

echo "=============================================="
echo "  PortfolioQ — Services & Access"
echo "=============================================="
echo ""

echo "--- Grafana ---"
echo "  URL:      http://localhost:3001"
echo "  Username: ${GRAFANA_USER:-admin}"
echo "  Password: ${GRAFANA_PASSWORD:-portfolioq_admin}"
echo ""

echo "--- Backend API ---"
echo "  URL:      http://localhost:${BACKEND_PORT:-8000}"
echo "  Health:   http://localhost:${BACKEND_PORT:-8000}/health"
echo "  Swagger:  http://localhost:${BACKEND_PORT:-8000}/api/docs"
echo "  ReDoc:    http://localhost:${BACKEND_PORT:-8000}/api/redoc"
echo "  Metrics:  http://localhost:${BACKEND_PORT:-8000}/metrics"
echo ""

echo "--- MLflow ---"
echo "  URL:      http://localhost:5001"
echo "  Experiments: http://localhost:5001/#/experiments"
echo ""

echo "--- Prometheus ---"
echo "  URL:      http://localhost:9090"
echo "  Targets:  http://localhost:9090/targets"
echo ""

echo "--- Database (PostgreSQL) ---"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: portfolioq"
echo "  User:     portfolioq"
echo "  Password: ${POSTGRES_PASSWORD:-portfolioq_secure_2025}"
echo ""

echo "--- API examples ---"
echo "  Portfolios:  http://localhost:${BACKEND_PORT:-8000}/api/v1/portfolios/"
echo "  Scenarios:   http://localhost:${BACKEND_PORT:-8000}/api/v1/scenarios/"
echo "  Reports:     http://localhost:${BACKEND_PORT:-8000}/api/v1/reports/"
echo "  Alerts:      http://localhost:${BACKEND_PORT:-8000}/api/v1/alerts/"
echo "  ML status:   http://localhost:${BACKEND_PORT:-8000}/api/v1/ml/status"
echo ""

echo "--- Quick status (optional) ---"
if command -v curl &>/dev/null; then
  curl -sf "http://localhost:${BACKEND_PORT:-8000}/health" >/dev/null 2>&1 && echo "  Backend:   OK" || echo "  Backend:   not reachable"
  curl -sf "http://localhost:5001/health" >/dev/null 2>&1 && echo "  MLflow:    OK" || echo "  MLflow:    not reachable"
  curl -sf "http://localhost:3001/api/health" >/dev/null 2>&1 && echo "  Grafana:   OK" || echo "  Grafana:   not reachable"
  curl -sf "http://localhost:9090/-/healthy" >/dev/null 2>&1 && echo "  Prometheus: OK" || echo "  Prometheus: not reachable"
else
  echo "  (install curl to auto-check status)"
fi
echo ""
echo "=============================================="
