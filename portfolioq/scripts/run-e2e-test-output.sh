#!/usr/bin/env bash
# Run full E2E validation and write all output to a text file.
# Usage: bash scripts/run-e2e-test-output.sh [BASE_URL]
# Output: e2e_test_results.txt in project root

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_URL="${1:-http://localhost:8000}"
OUTPUT_FILE="$ROOT_DIR/e2e_test_results.txt"

cd "$ROOT_DIR"
: > "$OUTPUT_FILE"

exec 1> >(tee -a "$OUTPUT_FILE") 2>&1

echo "=============================================="
echo "  PortfolioQ — End-to-End Test Run"
echo "  $(date -Iseconds)"
echo "  BASE_URL: $BASE_URL"
echo "  Output file: $OUTPUT_FILE"
echo "=============================================="
echo ""

echo ">>> 1. Health and readiness"
echo "--------------------------------------------------------------"
if curl -sf "$BASE_URL/health" >/dev/null 2>&1; then
  echo "  OK Backend health"
  curl -s "$BASE_URL/health" | head -5
else
  echo "  FAIL Backend unreachable at $BASE_URL"
fi
echo ""

echo ">>> 2. Validate all APIs (portfolios, scenarios, exposure, reports, alerts, ML)"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/validate-all-apis.sh" "$BASE_URL" || true
echo ""

echo ">>> 3. ML models API check"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/check-ml-models.sh" "$BASE_URL" || true
echo ""

echo ">>> 4. ML models end-to-end (scenario run + report)"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/validate-ml-models-e2e.sh" "$BASE_URL" || true
echo ""

echo ">>> 5. Full system validation (18 steps)"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/validate-system-e2e.sh" "$BASE_URL" --no-docker || true
echo ""

echo ">>> 6. Backend import verification (Docker)"
echo "--------------------------------------------------------------"
if docker compose exec -T backend python scripts/verify_imports.py 2>/dev/null; then
  echo "  OK All imports succeeded"
else
  echo "  SKIP or FAIL (backend container may not be running)"
fi
echo ""

echo ">>> 7. Backend unit tests (Docker)"
echo "--------------------------------------------------------------"
if docker compose exec -T backend python -m pytest tests/ -q --tb=short 2>/dev/null; then
  echo "  OK Tests passed"
else
  echo "  SKIP or FAIL (backend container may not be running)"
fi
echo ""

echo "=============================================="
echo "  E2E test run finished at $(date -Iseconds)"
echo "  Full output saved to: $OUTPUT_FILE"
echo "=============================================="
