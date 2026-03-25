#!/usr/bin/env bash
# PortfolioQ — Retrain ML models (force full retrain).
# Usage:
#   bash scripts/retrain-ml-models.sh [BASE_URL]           # trigger via API (async)
#   bash scripts/retrain-ml-models.sh [BASE_URL] --sync     # run inside backend container (sync)

BASE_URL="${1:-http://localhost:8000}"
SYNC=""
[ "${2:-}" = "--sync" ] && SYNC=1
[ "${1:-}" = "--sync" ] && BASE_URL="http://localhost:8000" && SYNC=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
API="$BASE_URL/api/v1/ml"

echo "=============================================="
echo "  PortfolioQ — Retrain ML Models"
echo "  BASE_URL: $BASE_URL"
echo "=============================================="
echo ""

if [ -n "$SYNC" ]; then
  echo ">>> Sync retraining (inside backend container)..."
  CONTAINER="${PORTFOLIOQ_BACKEND_CONTAINER:-portfolioq_backend}"
  if ! docker exec "$CONTAINER" python -c "
from src.ml.training import train_all_models
train_all_models(force_retrain=True)
print('Retraining complete.')
" 2>/dev/null; then
    echo "  FAIL: Could not run retraining in container '$CONTAINER'. Is it running?"
    exit 1
  fi
  echo ""
  echo "  Done. Run: bash scripts/test-ml-models.sh $BASE_URL"
  exit 0
fi

echo ">>> Triggering retrain via API (async)..."
RES=$(curl -sf -X POST "$API/retrain" 2>/dev/null) || RES=""
if [ -z "$RES" ]; then
  echo "  FAIL: Could not reach $API/retrain"
  exit 1
fi
echo "$RES" | python3 -m json.tool 2>/dev/null || echo "$RES"
echo ""
echo "  Retraining started in background. Wait 2–3 minutes then run:"
echo "  bash scripts/test-ml-models.sh $BASE_URL"
echo "=============================================="
