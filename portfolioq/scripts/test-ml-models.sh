#!/usr/bin/env bash
# PortfolioQ — Test ML models (API checks + end-to-end validation).
# Usage: bash scripts/test-ml-models.sh [BASE_URL]
# Exit: 0 if all tests pass, 1 otherwise.

BASE_URL="${1:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

PASS=0
FAIL=0

echo "=============================================="
echo "  PortfolioQ — Test ML Models"
echo "  BASE_URL: $BASE_URL"
echo "=============================================="
echo ""

echo ">>> 1. ML API check"
echo "--------------------------------------------------------------"
if bash "$SCRIPT_DIR/check-ml-models.sh" "$BASE_URL" 2>/dev/null; then
  PASS=$((PASS+1))
else
  FAIL=$((FAIL+1))
fi
echo ""

echo ">>> 2. ML end-to-end validation"
echo "--------------------------------------------------------------"
if bash "$SCRIPT_DIR/validate-ml-models-e2e.sh" "$BASE_URL" 2>/dev/null; then
  PASS=$((PASS+1))
else
  FAIL=$((FAIL+1))
fi
echo ""

echo "=============================================="
echo "  Test result: $PASS passed, $FAIL failed"
echo "=============================================="
[ "$FAIL" -eq 0 ]
