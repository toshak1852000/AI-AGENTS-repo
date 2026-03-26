#!/usr/bin/env bash
# PortfolioQ — ML models end-to-end validation.
# 1. ML status & API predictions  2. Run scenario (uses factor + risk + opportunity models)
# 3. Validate report contains ML outputs (risk_score, factor exposures, signals).
# Usage: bash scripts/validate-ml-models-e2e.sh [BASE_URL]

BASE_URL="${1:-http://localhost:8000}"
API_ML="$BASE_URL/api/v1/ml"
API_PF="$BASE_URL/api/v1/portfolios"
API_SC="$BASE_URL/api/v1/scenarios"
API_REP="$BASE_URL/api/v1/reports"
# Workflow pulls market data + runs ML; 120s is often too short. Override: SCENARIO_RUN_CURL_MAXTIME=0 (curl: no limit)
SCENARIO_RUN_CURL_MAXTIME="${SCENARIO_RUN_CURL_MAXTIME:-600}"
PASS=0
FAIL=0

red='\033[0;31m'
green='\033[0;32m'
nc='\033[0m'
ok()  { echo -e "${green}  OK${nc} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${red}  FAIL${nc} $1"; FAIL=$((FAIL+1)); }

echo "=============================================="
echo "  PortfolioQ — ML Models End-to-End Validation"
echo "  BASE_URL: $BASE_URL"
echo "=============================================="
echo ""

# --- Phase 1: ML status & direct predictions ---
echo "=== Phase 1: ML status & predictions ==="
echo ""

echo "--- 1.1 GET /api/v1/ml/status ---"
STATUS=$(curl -sf "$API_ML/status" 2>/dev/null) || STATUS=""
if [ -z "$STATUS" ]; then
  fail "cannot reach ML status"
else
  if echo "$STATUS" | python3 -c "
import sys,json
d=json.load(sys.stdin)
f=d.get('factor_model',{}).get('fitted')
r=d.get('risk_model',{}).get('fitted')
o=d.get('opportunity_model',{}).get('fitted')
sys.exit(0 if (f and r and o) else 1)
" 2>/dev/null; then
    ok "all models fitted (factor, risk, opportunity)"
  else
    fail "one or more models not fitted"
  fi
fi

echo "--- 1.2 POST /api/v1/ml/score ---"
SCORE_RES=$(curl -sf -X POST "$API_ML/score" -H "Content-Type: application/json" \
  -d '{"portfolio_id":"e2e","scenario_type":"market_shock"}' 2>/dev/null)
if echo "$SCORE_RES" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('risk_score'); l=d.get('risk_level')
levels=('low','medium','high','critical')
sys.exit(0 if s is not None and 0<=float(s)<=1 and l in levels else 1)
" 2>/dev/null; then
  ok "risk model prediction valid (score in [0,1], level in levels)"
else
  fail "risk score API invalid or missing"
fi

echo "--- 1.3 POST /api/v1/ml/factor-betas ---"
BETAS_RES=$(curl -sf -X POST "$API_ML/factor-betas" -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL","XOM"],"scenario_type":"market_shock"}' 2>/dev/null)
if echo "$BETAS_RES" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('symbols',{})
factors=('market','small_cap','value','momentum','oil','gold','bonds','usd')
for sym,b in s.items():
  if not b or not all(f in b and isinstance(b[f],(int,float)) for f in factors):
    sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
  ok "factor model returns valid betas per symbol"
else
  fail "factor-betas API invalid or missing keys"
fi
echo ""

# --- Phase 2: Run scenario (workflow uses all 3 models) ---
echo "=== Phase 2: Scenario run (factor + risk + opportunity in pipeline) ==="
echo ""

# Match validate-all-apis: ensure portfolio + at least one holding, and a scenario (workflow needs data)
echo "--- 2.0 Ensure portfolio with holdings + scenario exist ---"
PF_LIST=$(curl -sf "$API_PF/" 2>/dev/null) || PF_LIST="[]"
PF_COUNT=$(echo "$PF_LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "${PF_COUNT:-0}" -eq 0 ]; then
  CREATE_PF=$(curl -sf -X POST "$API_PF/" -H "Content-Type: application/json" \
    -d '{"name":"ML E2E Portfolio","description":"validate-ml-models-e2e seed"}' 2>/dev/null)
  PID=$(echo "$CREATE_PF" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
  [ -n "$PID" ] && ok "created portfolio $PID" || fail "could not create portfolio"
else
  PID=$(echo "$PF_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null)
  ok "using existing portfolio (first in list)"
fi
if [ -n "$PID" ]; then
  N_HOLD=$(curl -sf "$API_PF/$PID/holdings" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)" 2>/dev/null || echo "0")
  if [ "${N_HOLD:-0}" -eq 0 ]; then
    if curl -sf -X POST "$API_PF/$PID/holdings" -H "Content-Type: application/json" \
      -d '{"symbol":"AAPL","company_name":"Apple Inc","quantity":50,"average_price":150,"sector":"Technology"}' >/dev/null 2>&1; then
      ok "added default holding (AAPL) to portfolio"
    else
      fail "could not add holding to portfolio $PID"
    fi
  else
    ok "portfolio has holdings ($N_HOLD)"
  fi
fi

SC_LIST=$(curl -sf "$API_SC/" 2>/dev/null) || SC_LIST="[]"
SC_COUNT=$(echo "$SC_LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "${SC_COUNT:-0}" -eq 0 ]; then
  CREATE_SC=$(curl -sf -X POST "$API_SC/" -H "Content-Type: application/json" \
    -d '{"name":"ML E2E Scenario","description":"validate-ml-models-e2e","type":"market_shock","parameters":{"shock_pct":-0.05}}' 2>/dev/null)
  SCID=$(echo "$CREATE_SC" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
  [ -n "$SCID" ] && ok "created scenario $SCID" || fail "could not create scenario"
else
  SCID=$(echo "$SC_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null)
  ok "using existing scenario (first in list)"
fi
echo ""

if [ -z "$PID" ] || [ -z "$SCID" ]; then
  fail "no portfolio or scenario available after seed step"
  REPORT_ID=""
else
  echo "--- 2.1 POST /scenarios/{id}/run (curl max-time=${SCENARIO_RUN_CURL_MAXTIME}s; set SCENARIO_RUN_CURL_MAXTIME=0 for no limit) ---"
  _tmp_run="$(mktemp)"
  # First attempt (no -f: capture error JSON body on 4xx/5xx)
  HTTP_CODE=$(curl -sS -o "$_tmp_run" -w "%{http_code}" ${SCENARIO_RUN_CURL_MAXTIME:+"--max-time" "$SCENARIO_RUN_CURL_MAXTIME"} \
    -X POST "$API_SC/$SCID/run" -H "Content-Type: application/json" \
    -d "{\"portfolio_ids\":[\"$PID\"]}" 2>/dev/null) || HTTP_CODE="000"
  RUN=$(cat "$_tmp_run" 2>/dev/null || true)
  rm -f "$_tmp_run"
  HTTP_CODE="${HTTP_CODE:-000}"
  # Retry once on empty body or non-2xx (transient market-data / load)
  if [ -z "$RUN" ] || [ "$HTTP_CODE" != "200" ]; then
    sleep 4
    _tmp_run="$(mktemp)"
    HTTP_CODE=$(curl -sS -o "$_tmp_run" -w "%{http_code}" ${SCENARIO_RUN_CURL_MAXTIME:+"--max-time" "$SCENARIO_RUN_CURL_MAXTIME"} \
      -X POST "$API_SC/$SCID/run" -H "Content-Type: application/json" \
      -d "{\"portfolio_ids\":[\"$PID\"]}" 2>/dev/null) || HTTP_CODE="000"
    RUN=$(cat "$_tmp_run" 2>/dev/null || true)
    rm -f "$_tmp_run"
    HTTP_CODE="${HTTP_CODE:-000}"
  fi

  RUN_STATUS=$(echo "$RUN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('status',''))
" 2>/dev/null)
  REPORT_ID=$(echo "$RUN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('report_id') or '')
" 2>/dev/null)
  DETAIL=$(echo "$RUN" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  print(d.get('detail', d.get('error', '')) or '')
except Exception:
  print('')
" 2>/dev/null)

  if [ "$RUN_STATUS" = "completed" ] && [ -n "$REPORT_ID" ]; then
    ok "scenario run completed, report_id=$REPORT_ID"
  else
    if [ -z "$RUN" ]; then
      fail "scenario run: empty response (http=$HTTP_CODE; timeout or unreachable). Try SCENARIO_RUN_CURL_MAXTIME=0 or a larger value."
    elif [ "$RUN_STATUS" = "failed" ] || [ "$RUN_STATUS" = "unknown" ]; then
      fail "scenario run status=$RUN_STATUS report_id=$REPORT_ID detail=${DETAIL:-none} http=$HTTP_CODE"
    else
      fail "scenario run status=$RUN_STATUS report_id=$REPORT_ID detail=${DETAIL:-none} http=$HTTP_CODE"
    fi
  fi
fi
echo ""

# --- Phase 3: Validate report has ML-derived outputs ---
echo "=== Phase 3: Report ML outputs validation ==="
echo ""

if [ -z "$REPORT_ID" ]; then
  fail "skip report checks (no report_id)"
else
  echo "--- 3.1 GET /reports/{id} ---"
  REPORT=$(curl -sf "$API_REP/$REPORT_ID" 2>/dev/null) || REPORT=""
  if [ -z "$REPORT" ]; then
    fail "could not fetch report"
  else
    ok "report fetched"

    echo "--- 3.2 Risk assessment (risk model) in report ---"
    if echo "$REPORT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('summary',{}) or {}
ra=s.get('risk_assessment',{}) or {}
score=ra.get('risk_score'); level=ra.get('risk_level')
ok=score is not None and level in ('low','medium','high','critical')
sys.exit(0 if ok else 1)
" 2>/dev/null; then
      ok "report contains risk_assessment (risk_score, risk_level)"
    else
      fail "report missing or invalid risk_assessment"
    fi

    echo "--- 3.3 Exposure summary (factor model) in report ---"
    if echo "$REPORT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('summary',{}) or {}
es=s.get('exposure_summary',{}) or {}
sens=es.get('sensitivity_score'); mv=es.get('total_market_value')
ok=sens is not None or mv is not None
sys.exit(0 if ok else 1)
" 2>/dev/null; then
      ok "report contains exposure_summary (factor/sensitivity)"
    else
      fail "report missing exposure_summary"
    fi

    echo "--- 3.4 Top holdings at risk (opportunity signals) ---"
    if echo "$REPORT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('summary',{}) or {}
top=s.get('top_holdings_at_risk',[])
# At least structure present; may have signal/risk_score from opportunity model
ok=isinstance(top,list)
sys.exit(0 if ok else 1)
" 2>/dev/null; then
      ok "report contains top_holdings_at_risk list"
    else
      fail "report missing top_holdings_at_risk"
    fi
  fi
fi
echo ""

# --- Summary ---
echo "=============================================="
echo "  Result: $PASS passed, $FAIL failed"
echo "=============================================="
[ "$FAIL" -eq 0 ]
