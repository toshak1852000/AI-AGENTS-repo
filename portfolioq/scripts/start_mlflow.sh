#!/usr/bin/env bash
# Start MLflow server (and PostgreSQL dependency) via Docker Compose.
# MLflow UI: http://localhost:5003
# Uses same PostgreSQL database as the app (single DB end-to-end).
# Run from repo root: bash scripts/start_mlflow.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env" ]; then
  echo "Warning: .env not found. Copy .env.example to .env and set POSTGRES_PASSWORD (and POSTGRES_USER/POSTGRES_DB if needed)."
fi

echo "Starting PostgreSQL and MLflow (port 5003)..."
docker compose up -d postgres mlflow

echo ""
echo "MLflow UI: http://localhost:5003"
echo "Experiments: http://localhost:5003/#/experiments"
echo "Models:      http://localhost:5003/#/models"
echo ""
echo "To view logs: docker compose logs -f mlflow"
