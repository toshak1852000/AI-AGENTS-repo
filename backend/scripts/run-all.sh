#!/usr/bin/env bash
# PortfolioQ — run all project validations (services, ML APIs, ML e2e).
# For full 18-step system validation (structure, deps, config, Docker, security): use validate-system-e2e.sh
# Usage: run from anywhere:
#   bash portfolioq/scripts/run-all.sh
#   bash scripts/run-all.sh   (when already inside portfolioq)
# Optional: pass BASE_URL for API checks, e.g. http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
if [ -f "$(cd "$SCRIPT_DIR/.." && pwd)/docker-compose.yml" ]; then
  ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
else
  ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
fi
cd "$ROOT_DIR"

echo ""
echo "##############################################################"
echo "  PortfolioQ — Full project validation"
echo "  Project root: $ROOT_DIR"
echo "  API base:     $BASE_URL"
echo "##############################################################"
echo ""

# 1. Services & credentials
echo ">>> 1. Services & access info"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/show-services.sh" 2>/dev/null || true
echo ""

# 2. Full API validation (portfolios, scenarios, exposure, reports, alerts, ML)
echo ">>> 2. Validate all APIs"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/validate-all-apis.sh" "$BASE_URL" 2>/dev/null || true
echo ""

# 3. ML API checks
echo ">>> 3. ML models API check"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/check-ml-models.sh" "$BASE_URL" 2>/dev/null || true
echo ""

# 4. ML end-to-end (scenario run + report validation)
echo ">>> 4. ML models end-to-end validation"
echo "--------------------------------------------------------------"
bash "$SCRIPT_DIR/validate-ml-models-e2e.sh" "$BASE_URL" 2>/dev/null || true
echo ""

echo "##############################################################"
echo "  Done. Review any FAIL lines above."
echo "##############################################################"
echo ""
