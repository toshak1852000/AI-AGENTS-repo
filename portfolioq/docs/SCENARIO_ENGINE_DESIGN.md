# Scenario Engine Design

## Overview

The **Scenario Simulation Engine** models portfolio sensitivity to predefined scenario types and returns P&L impact, company exposure changes, and sector vulnerability scores.

---

## 1. Scenario Types

Supported scenarios (aligned with `factor_model.SCENARIO_SHOCKS`):

- market_shock  
- commodity_fluctuation  
- regulatory_change  
- geopolitical_event  
- interest_rate_change  
- currency_fluctuation  
- sector_decline  
- company_specific  

Each scenario is defined by a **factor shock vector** (percentage changes per factor: market, small_cap, value, momentum, oil, gold, bonds, usd).

---

## 2. Engine Flow

1. **Input:** List of holdings (symbol, quantity, current_price, sector, etc.), scenario type, optional scale.
2. **Factor model:** Load fitted factor model; get per-symbol factor betas (or sector defaults).
3. **Shocks:** Look up shock vector for scenario type.
4. **P&L:** For each holding, estimated return = sum(beta_f * shock_f); P&L = return × market_value.
5. **Aggregation:** Portfolio P&L, portfolio return %, portfolio factor betas (weighted), sensitivity score (derived from |P&L|/total_mv).
6. **Sector vulnerability:** Aggregate P&L by sector (from input holdings); return as % of portfolio.

---

## 3. Outputs

- **portfolio_pl_impact:** Total estimated P&L in currency.  
- **portfolio_return_pct:** Portfolio return under scenario (%).  
- **portfolio_factor_betas:** Weighted average factor exposures.  
- **sensitivity_score:** 0–1 score for portfolio sensitivity.  
- **company_exposures:** Per-holding market value, weight, factor betas, scenario_pl_impact.  
- **sector_vulnerability:** Per-sector P&L as % of portfolio (for heatmaps and dashboards).

---

## 4. Usage

- **API:** `POST /api/v1/ml/scenario-simulation` with body `{ "holdings": [...], "scenario_type": "market_shock", "scale": 1.0 }`.  
- **Workflow:** Full scenario run uses `exposure_service.calculate_exposure` (which uses factor model and scenario type) and `risk_service.assess_risk`; report includes exposure and risk.  
- **Pipeline:** `backend/pipelines/scenario_pipeline.py` for engine-only runs (e.g. batch or testing).

---

## 5. Validation

Scenario outputs can be validated against historical benchmarks by comparing implied returns to realized returns in backtests; the evaluation module can be extended with scenario-specific metrics.
