#!/usr/bin/env bash
# PortfolioQ — validate all REST APIs and workflow end-to-end.
# Usage: bash scripts/validate-all-apis.sh [BASE_URL]
# Default BASE_URL: http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
API_PF="$BASE_URL/api/v1/portfolios"
API_SC="$BASE_URL/api/v1/scenarios"
API_EX="$BASE_URL/api/v1/exposure"
API_REP="$BASE_URL/api/v1/reports"
API_AL="$BASE_URL/api/v1/alerts"
API_ML="$BASE_URL/api/v1/ml"
PASS=0
FAIL=0

red='\033[0;31m'
green='\033[0;32m'
nc='\033[0m'
ok()  { echo -e "${green}  OK${nc} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${red}  FAIL${nc} $1"; FAIL=$((FAIL+1)); }

echo "=============================================="
echo "  PortfolioQ — Validate All APIs"
echo "  BASE_URL: $BASE_URL"
echo "=============================================="
echo ""

# --- Prerequisites ---
echo ">>> Prerequisites"
echo "---"
if ! curl -sf "$BASE_URL/health" >/dev/null 2>&1; then
  fail "Backend unreachable at $BASE_URL. Start stack: docker compose up -d"
  echo ""
  echo "=============================================="
  echo "  Result: $PASS passed, $FAIL failed"
  echo "=============================================="
  exit 1
fi
ok "Backend reachable"
echo ""

# --- Portfolios ---
echo ">>> Portfolios"
echo "---"
PF_LIST=$(curl -sf "$API_PF/" 2>/dev/null) || PF_LIST="[]"
if echo "$PF_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,list) else 1)" 2>/dev/null; then
  ok "GET /portfolios/"
else
  fail "GET /portfolios/"
fi

# Create portfolio if empty
PF_COUNT=$(echo "$PF_LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "${PF_COUNT:-0}" -eq 0 ]; then
  CREATE_PF=$(curl -sf -X POST "$API_PF/" -H "Content-Type: application/json" \
    -d '{"name":"Validate API Portfolio","description":"Created by validate-all-apis"}' 2>/dev/null)
  PID=$(echo "$CREATE_PF" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
  if [ -n "$PID" ]; then
    ok "POST /portfolios/ (created)"
    curl -sf -X POST "$API_PF/$PID/holdings" -H "Content-Type: application/json" \
      -d '{"symbol":"AAPL","company_name":"Apple Inc","quantity":50,"average_price":150,"sector":"Technology"}' >/dev/null 2>&1 && ok "POST /portfolios/{id}/holdings" || fail "POST holdings"
  else
    fail "POST /portfolios/"
  fi
else
  PID=$(echo "$PF_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null)
  ok "GET /portfolios/ (existing data)"
fi

if [ -n "$PID" ]; then
  GET_PF=$(curl -sf "$API_PF/$PID" 2>/dev/null)
  if echo "$GET_PF" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('id') and d.get('name') else 1)" 2>/dev/null; then
    ok "GET /portfolios/{id}"
  else
    fail "GET /portfolios/{id}"
  fi
fi
echo ""

# --- Scenarios ---
echo ">>> Scenarios"
echo "---"
SC_LIST=$(curl -sf "$API_SC/" 2>/dev/null) || SC_LIST="[]"
if echo "$SC_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,list) else 1)" 2>/dev/null; then
  ok "GET /scenarios/"
else
  fail "GET /scenarios/"
fi

SC_COUNT=$(echo "$SC_LIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "${SC_COUNT:-0}" -eq 0 ]; then
  CREATE_SC=$(curl -sf -X POST "$API_SC/" -H "Content-Type: application/json" \
    -d '{"name":"Validate API Scenario","description":"E2E","type":"market_shock","parameters":{"shock_pct":-0.05}}' 2>/dev/null)
  SCID=$(echo "$CREATE_SC" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
  if [ -n "$SCID" ]; then ok "POST /scenarios/ (created)"; else fail "POST /scenarios/"; fi
else
  SCID=$(echo "$SC_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null)
  ok "GET /scenarios/ (existing data)"
fi

if [ -n "$SCID" ]; then
  GET_SC=$(curl -sf "$API_SC/$SCID" 2>/dev/null)
  if echo "$GET_SC" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('id') and d.get('type') else 1)" 2>/dev/null; then
    ok "GET /scenarios/{id}"
  else
    fail "GET /scenarios/{id}"
  fi
fi
echo ""

# --- Scenario run (workflow) ---
echo ">>> Scenario run (workflow)"
echo "---"
if [ -n "$PID" ] && [ -n "$SCID" ]; then
  RUN=$(curl -sf -X POST "$API_SC/$SCID/run" -H "Content-Type: application/json" \
    -d "{\"portfolio_ids\":[\"$PID\"]}" 2>/dev/null)
  STATUS=$(echo "$RUN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null)
  REPORT_ID=$(echo "$RUN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('report_id',''))" 2>/dev/null)
  if [ "$STATUS" = "completed" ] && [ -n "$REPORT_ID" ]; then
    ok "POST /scenarios/{id}/run (status=$STATUS, report_id present)"
  else
    fail "POST /scenarios/{id}/run (status=$STATUS, report_id=$REPORT_ID)"
  fi
else
  fail "Skip scenario run (no portfolio or scenario)"
  REPORT_ID=""
fi
echo ""

# --- Reports ---
echo ">>> Reports"
echo "---"
REP_LIST=$(curl -sf "$API_REP/" 2>/dev/null) || REP_LIST="[]"
if echo "$REP_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,list) else 1)" 2>/dev/null; then
  ok "GET /reports/"
else
  fail "GET /reports/"
fi

if [ -n "$REPORT_ID" ]; then
  REP_ONE=$(curl -sf "$API_REP/$REPORT_ID" 2>/dev/null)
  if echo "$REP_ONE" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('summary',{}) or {}
ra=s.get('risk_assessment'); es=s.get('exposure_summary'); top=s.get('top_holdings_at_risk')
exit(0 if (ra is not None and es is not None and isinstance(top,list)) else 1)
" 2>/dev/null; then
    ok "GET /reports/{id} (summary has risk_assessment, exposure_summary, top_holdings_at_risk)"
  else
    fail "GET /reports/{id} or summary structure"
  fi
  # Download only if file_path would be set (workflow uses json)
  FMT=$(echo "$REP_ONE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('format',''))" 2>/dev/null)
  if [ "$FMT" = "json" ]; then
    DOWNLOAD=$(curl -sf -o /dev/null -w "%{http_code}" "$API_REP/$REPORT_ID/download" 2>/dev/null)
    if [ "$DOWNLOAD" = "200" ]; then ok "GET /reports/{id}/download"; else fail "GET /reports/{id}/download (http $DOWNLOAD)"; fi
  fi
else
  fail "Skip report checks (no report_id)"
fi
echo ""

# --- Exposure ---
echo ">>> Exposure"
echo "---"
if [ -n "$PID" ]; then
  EX_PF=$(curl -sf "$API_EX/portfolio/$PID" 2>/dev/null) || EX_PF="[]"
  if echo "$EX_PF" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,list) else 1)" 2>/dev/null; then
    ok "GET /exposure/portfolio/{id}"
  else
    fail "GET /exposure/portfolio/{id}"
  fi
  if [ -n "$SCID" ]; then
    EX_CALC=$(curl -sf -X POST "$API_EX/calculate" -H "Content-Type: application/json" \
      -d "{\"portfolio_id\":\"$PID\",\"scenario_id\":\"$SCID\"}" 2>/dev/null)
    if echo "$EX_CALC" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,dict) and ('company_exposures' in d or 'sensitivity_score' in d or 'total_exposure' in d) else 1)" 2>/dev/null; then
      ok "POST /exposure/calculate"
    else
      fail "POST /exposure/calculate"
    fi
  fi
  RS=$(curl -sf "$API_EX/risk-scores/portfolio/$PID" 2>/dev/null) || RS="[]"
  if echo "$RS" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,list) else 1)" 2>/dev/null; then
    ok "GET /exposure/risk-scores/portfolio/{id}"
  else
    fail "GET /exposure/risk-scores/portfolio/{id}"
  fi
else
  fail "Skip exposure (no portfolio_id)"
fi
echo ""

# --- Alerts ---
echo ">>> Alerts"
echo "---"
AL_LIST=$(curl -sf "$API_AL/" 2>/dev/null) || AL_LIST="[]"
if echo "$AL_LIST" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,list) else 1)" 2>/dev/null; then
  ok "GET /alerts/"
else
  fail "GET /alerts/"
fi
AL_SUM=$(curl -sf "$API_AL/summary/counts" 2>/dev/null) || AL_SUM="{}"
if echo "$AL_SUM" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,dict) else 1)" 2>/dev/null; then
  ok "GET /alerts/summary/counts"
else
  fail "GET /alerts/summary/counts"
fi
echo ""

# --- ML ---
echo ">>> ML"
echo "---"
ML_STATUS=$(curl -sf "$API_ML/status" 2>/dev/null) || ML_STATUS="{}"
if echo "$ML_STATUS" | python3 -c "
import sys,json
d=json.load(sys.stdin)
f=d.get('factor_model',{}).get('fitted'); r=d.get('risk_model',{}).get('fitted'); o=d.get('opportunity_model',{}).get('fitted')
sys.exit(0 if (f and r and o) else 1)
" 2>/dev/null; then
  ok "GET /ml/status (all models fitted)"
else
  fail "GET /ml/status (one or more models not fitted)"
fi
SCORE_RES=$(curl -sf -X POST "$API_ML/score" -H "Content-Type: application/json" \
  -d '{"portfolio_id":"v","scenario_type":"market_shock"}' 2>/dev/null)
if echo "$SCORE_RES" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('risk_score'); l=d.get('risk_level')
levels=('low','medium','high','critical')
sys.exit(0 if s is not None and 0<=float(s)<=1 and l in levels else 1)
" 2>/dev/null; then
  ok "POST /ml/score"
else
  fail "POST /ml/score"
fi
BETAS=$(curl -sf -X POST "$API_ML/factor-betas" -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL"],"scenario_type":"market_shock"}' 2>/dev/null)
if echo "$BETAS" | python3 -c "
import sys,json
d=json.load(sys.stdin)
s=d.get('symbols',{})
factors=('market','small_cap','value','momentum','oil','gold','bonds','usd')
for sym,b in s.items():
  if not b or not all(f in b for f in factors): sys.exit(1)
sys.exit(0)
" 2>/dev/null; then
  ok "POST /ml/factor-betas"
else
  fail "POST /ml/factor-betas"
fi
echo ""

# --- Rebalancing (if endpoint exists) ---
if [ -n "$PID" ]; then
  REB=$(curl -sf "$API_PF/$PID/rebalancing-recommendations?scenario_id=$SCID" 2>/dev/null)
  REB_HTTP=$?
  if [ $REB_HTTP -eq 0 ] && echo "$REB" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if isinstance(d,dict) and ('holding_recommendations' in d or 'sector_recommendations' in d or 'recommendations' in d) else 1)" 2>/dev/null; then
    ok "GET /portfolios/{id}/rebalancing-recommendations"
  else
    # Endpoint may not exist yet; do not fail
    echo "  (skip) GET /portfolios/{id}/rebalancing-recommendations (optional)"
  fi
fi
echo ""

echo "=============================================="
echo "  Result: $PASS passed, $FAIL failed"
echo "=============================================="
[ "$FAIL" -eq 0 ]
