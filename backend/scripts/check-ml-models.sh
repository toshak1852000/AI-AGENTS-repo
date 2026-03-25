#!/usr/bin/env bash
# PortfolioQ — ML models and ML API check.
# Usage (from project root, the folder with docker-compose.yml):
#   bash scripts/check-ml-models.sh [BASE_URL]
#   ./bin/check-ml-models.sh [BASE_URL]   # after: export PATH="$PWD/bin:$PATH"
# Default BASE_URL: http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# Project root = directory with docker-compose.yml (works from backend/scripts or top-level scripts/)
if [ -f "$(cd "$SCRIPT_DIR/.." && pwd)/docker-compose.yml" ]; then
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
else
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
fi
API="$BASE_URL/api/v1/ml"

if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required (install curl)." >&2
  exit 1
fi
PASS=0
FAIL=0

red='\033[0;31m'
green='\033[0;32m'
nc='\033[0m'
ok()  { echo -e "${green}  OK${nc} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${red}  FAIL${nc} $1"; FAIL=$((FAIL+1)); }

echo "=============================================="
echo "  PortfolioQ — ML Models & API Check"
echo "  BASE_URL: $BASE_URL"
echo "=============================================="
echo ""

# --- 1. ML Status ---
echo "--- 1. GET /api/v1/ml/status ---"
RES=$(curl -sf "$API/status" 2>/dev/null) || { fail "request failed"; RES=""; }
if [ -z "$RES" ]; then
  echo "" >&2
  echo "  Hint: Is the API up at $BASE_URL ? From project root run:" >&2
  echo "    cd $PROJECT_ROOT && docker compose up -d" >&2
  echo "  Then re-run: bash scripts/check-ml-models.sh   or   export PATH=\"$PROJECT_ROOT/bin:\$PATH\" && check-ml-models.sh" >&2
fi
if [ -n "$RES" ]; then
  FITTED=$(echo "$RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
fm = d.get('factor_model', {}); rm = d.get('risk_model', {}); om = d.get('opportunity_model', {})
print('factor=%s risk=%s opp=%s n_symbols=%s' % (
  fm.get('fitted'), rm.get('fitted'), om.get('fitted'), fm.get('n_symbols', 0)))
" 2>/dev/null)
  if echo "$RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
exit(0 if d.get('factor_model',{}).get('fitted') and d.get('risk_model',{}).get('fitted') and d.get('opportunity_model',{}).get('fitted') else 1)
" 2>/dev/null; then
    ok "all models fitted ($FITTED)"
  else
    fail "one or more models not fitted ($FITTED)"
  fi
fi
echo ""

# --- 2. Risk Score (predictions) ---
echo "--- 2. POST /api/v1/ml/score ---"
SCORE_RES=$(curl -sf -X POST "$API/score" -H "Content-Type: application/json" \
  -d '{"portfolio_id":"check","scenario_type":"market_shock"}' 2>/dev/null) || SCORE_RES=""
if [ -n "$SCORE_RES" ]; then
  SCORE=$(echo "$SCORE_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d.get('risk_score'); l = d.get('risk_level')
print('score=%s level=%s' % (s, l))
" 2>/dev/null)
  VALID=$(echo "$SCORE_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d.get('risk_score')
l = d.get('risk_level')
levels = ('low', 'medium', 'high', 'critical')
ok = s is not None and 0 <= float(s) <= 1 and l in levels
print('valid' if ok else 'invalid')
" 2>/dev/null) || VALID="invalid"
  if [ "$VALID" = "valid" ]; then
    ok "risk_score in [0,1], risk_level valid ($SCORE)"
  else
    fail "unexpected response: risk_score=$SCORE (expected 0<=score<=1, level in low/medium/high/critical)"
  fi
else
  fail "request failed or empty response"
fi
echo ""

# --- 3. Factor Betas (predictions) ---
echo "--- 3. POST /api/v1/ml/factor-betas ---"
BETAS_RES=$(curl -sf -X POST "$API/factor-betas" -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL","MSFT","XOM"],"scenario_type":"market_shock"}' 2>/dev/null) || BETAS_RES=""
if [ -n "$BETAS_RES" ]; then
  VALID=$(echo "$BETAS_RES" | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  sym = d.get('symbols', {})
  if not sym or not isinstance(sym, dict):
    print('invalid'); sys.exit(0)
  factors = ('market', 'small_cap', 'value', 'momentum', 'oil', 'gold', 'bonds', 'usd')
  for s, betas in sym.items():
    if not isinstance(betas, dict):
      print('invalid'); sys.exit(0)
    for f in factors:
      if f not in betas or not isinstance(betas[f], (int, float)):
        print('invalid'); sys.exit(0)
  print('valid')
except Exception:
  print('invalid')
" 2>/dev/null) || VALID="invalid"
  if [ "$VALID" = "valid" ]; then
    ok "factor betas returned for all symbols with expected factor keys"
  else
    fail "factor-betas response missing keys or non-numeric betas"
  fi
else
  fail "request failed or empty response"
fi
echo ""

# --- 4. MLflow URL ---
echo "--- 4. GET /api/v1/ml/mlflow-url ---"
MLF=$(curl -sf "$API/mlflow-url" 2>/dev/null) || MLF=""
if echo "$MLF" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('mlflow_url') else 1)" 2>/dev/null; then
  ok "mlflow_url returned"
else
  fail "request failed or no mlflow_url"
fi
echo ""

# --- 5. Train (sync) — optional, only check response ---
echo "--- 5. POST /api/v1/ml/train (check response) ---"
TRAIN_RES=$(curl -sf -X POST "$API/train?force_retrain=false" 2>/dev/null) || TRAIN_RES=""
if echo "$TRAIN_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
exit(0 if d.get('status') in ('training_started', 'training_complete') else 1)
" 2>/dev/null; then
  ok "train endpoint responds with status"
else
  fail "train endpoint failed or unexpected status"
fi
echo ""

# --- 6. Retrain (async) ---
echo "--- 6. POST /api/v1/ml/retrain ---"
RETRAIN_RES=$(curl -sf -X POST "$API/retrain" 2>/dev/null) || RETRAIN_RES=""
if echo "$RETRAIN_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
exit(0 if d.get('status') == 'retraining_started' else 1)
" 2>/dev/null; then
  ok "retrain endpoint responds"
else
  fail "retrain endpoint failed"
fi
echo ""

# --- 7. Tune ---
echo "--- 7. POST /api/v1/ml/tune ---"
TUNE_RES=$(curl -sf -X POST "$API/tune" -H "Content-Type: application/json" \
  -d '{"n_trials":2}' 2>/dev/null) || TUNE_RES=""
if echo "$TUNE_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
exit(0 if d.get('status') == 'tuning_started' else 1)
" 2>/dev/null; then
  ok "tune endpoint responds"
else
  fail "tune endpoint failed"
fi
echo ""

# --- Summary ---
echo "=============================================="
echo "  Result: $PASS passed, $FAIL failed"
echo "=============================================="
[ "$FAIL" -eq 0 ]
