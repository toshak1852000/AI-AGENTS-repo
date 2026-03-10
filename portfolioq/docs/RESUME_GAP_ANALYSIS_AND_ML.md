# PortfolioQ — Resume Gap Analysis & ML Recommendation

**Note:** This document is a historical gap analysis. For today's status, see **"Current implementation status"** below.

This document maps the **resume/capability claims** to the **current codebase**, lists what is **remaining to implement**, and recommends **ML models** for the use case.

---

## Current implementation status (as of March 2025)

All resume points below are **Implemented** and validated via `scripts/validate-all-apis.sh` and `scripts/run-all.sh`.

| Resume claim | Status | Where in codebase |
|--------------|--------|--------------------|
| Evaluate portfolio exposure to market, commodity, regulatory changes | **Implemented** | `exposure_service.calculate_exposure`, factor model scenario shocks; `exposure_calculation_node` |
| Identify how scenarios affect individual holdings and sectors | **Implemented** | `exposure_service` → company_exposures, sector_exposures; report summary; GET `/exposure/portfolio/{id}` |
| Detect emerging risks and potential strategic opportunities | **Implemented** | `risk_service.assess_risk`, `risk_model`, `opportunity_model`; prioritized_holdings with signals; `risk_assessment_node` |
| Generate automated, actionable insights for governance and oversight | **Implemented** | `report_service.generate_report` (PDF/Excel/JSON), executive summary, recommendations; `report_generation_node` |
| Track scenario triggers and provide real-time notifications | **Implemented** | `alert_service.evaluate_and_create_alerts`, Alert model; Celery `check_alert_thresholds`; GET/PUT alerts API |
| Automated portfolio sensitivity modeling | **Implemented** | `factor_model.portfolio_sensitivity`, factor betas; exposure_result.sensitivity_score; exposure API |
| Market factor and regulatory impact assessment | **Implemented** | Factor model + scenario types in `constants.py`; `risk_service` features; scenario shocks in factor_model |
| Quantitative and qualitative data integration | **Implemented** | `integrations/` (yahoo_finance, fred, alpha_vantage); `llm_service.generate_scenario_narrative` (qualitative) |
| Scenario-driven risk scoring and prioritization | **Implemented** | `risk_model` (XGBoost), risk_service; prioritized_holdings; RiskScore model; GET risk-scores API |
| Scalable, repeatable, audit-ready analytics pipelines | **Implemented** | LangGraph workflow; PostgreSQL persistence (ScenarioRun, Exposure, Report, Alert); `run_workflow` |
| Conducted automated scenario analysis | **Implemented** | POST `/scenarios/{id}/run` runs full workflow; ScenarioRun persisted |
| Mapped company- and sector-level impacts | **Implemented** | company_exposures, sector_exposures in exposure_result and report; exposure API |
| Generated board-ready scenario reports | **Implemented** | report_service (_write_pdf, _write_excel, _write_json); GET report download; POST reports/generate |
| Continuous monitoring workflows for real-time alerts | **Implemented** | Celery Beat: refresh_all_prices (hourly), run_all_scheduled_scenarios (daily), check_alert_thresholds (30 min), retrain (weekly) |
| Integrated quantitative and qualitative insights | **Implemented** | Market data services + LLM narrative in reports |
| Portfolio Sensitivity Scores by market factor or scenario | **Implemented** | exposure_result.sensitivity_score, portfolio_factor_betas; GET exposure returns sensitivity_scores |
| Company-Level Exposure Analysis | **Implemented** | exposure_service company_exposures; GET exposure/portfolio, POST exposure/calculate |
| Stress-Tested P&L Impact | **Implemented** | factor_model portfolio_pl_impact; risk_result.pl_impact, pl_impact_pct; report risk_assessment |
| Risk & Opportunity Signal Frequency | **Implemented** | Alerts; opportunity model signals (strong_buy, buy, hold, reduce, sell) in prioritized_holdings |
| Scenario-Based Rebalancing Recommendations | **Implemented** | `rebalancing_service.generate_rebalancing_recommendations`; in report summary; GET `/portfolios/{id}/rebalancing-recommendations` |

**Section 5 checklist (all done):** DB enabled and used; market data integrations and market_data_service; exposure_service and node; risk_service and node; report_service (PDF/Excel/JSON) and download; alert creation and listing; Celery periodic tasks; sensitivity/rebalancing logic; ML (factor, risk, opportunity, LLM).

---

## 1. Resume Points vs Implementation Status (historical)

| Resume claim | Status | Where in codebase |
|--------------|--------|--------------------|
| **Evaluate portfolio exposure to market, commodity, regulatory changes** | ⚠️ **Partial** | Workflow node `exposure_calculation` exists but is a **stub** (returns empty company/sector exposures). No real market/commodity/regulatory data or formulas. |
| **Identify how scenarios affect individual holdings and sectors** | ❌ **Missing** | Schemas exist (`CompanyExposure`, `SectorExposure`). No service or workflow logic that computes real holdings/sector impact. |
| **Detect emerging risks and potential strategic opportunities** | ❌ **Missing** | No risk-detection logic, no “opportunity” signals. `risk_assessment` node is a stub. |
| **Generate automated, actionable insights for governance and oversight** | ⚠️ **Partial** | Report generation node exists but is a **stub** (returns placeholder report ID). No PDF/Excel/board-ready content. |
| **Track scenario triggers and provide real-time notifications** | ❌ **Missing** | Alert API and model are stubs. No trigger logic, no notifications (email/push/UI). |
| **Automated portfolio sensitivity modeling** | ❌ **Missing** | No sensitivity (e.g. delta/gamma to factors) implementation. Constants mention `factor_exposure` but no code. |
| **Market factor and regulatory impact assessment** | ❌ **Missing** | Scenario types and default params exist in `constants.py`. No service that applies factors or regulatory impact to portfolios. |
| **Quantitative and qualitative data integration** | ❌ **Missing** | No market data integrations (Alpha Vantage, Yahoo, FRED are configured but `integrations/` is empty). No qualitative (news/sentiment) pipeline. |
| **Scenario-driven risk scoring and prioritization** | ⚠️ **Partial** | Risk schemas and thresholds exist. `risk_assessment` node returns empty scores; no real scoring or prioritization. |
| **Scalable, repeatable, audit-ready analytics pipelines** | ⚠️ **Partial** | LangGraph pipeline (data → exposure → risk → report) is in place and repeatable. No persistence of runs/results (DB models commented out), so not yet audit-ready. |
| **Conducted automated scenario analysis** | ✅ **Done** | `POST /scenarios/{id}/run` runs the full workflow (stub nodes execute end-to-end). |
| **Mapped company- and sector-level impacts** | ❌ **Missing** | Only schema/stub; no real mapping logic. |
| **Generated board-ready scenario reports** | ❌ **Missing** | Report node is stub; no PDF/Excel generation (reportlab/openpyxl in deps but unused). |
| **Continuous monitoring workflows for real-time alerts** | ❌ **Missing** | Celery has a health-check task only. No scheduled scenario/monitoring tasks or alert publishing. |
| **Integrated quantitative and qualitative insights** | ❌ **Missing** | No data integration layer. |
| **Portfolio Sensitivity Scores by market factor or scenario** | ❌ **Missing** | No computed sensitivity metrics or API. |
| **Company-Level Exposure Analysis** | ❌ **Missing** | Schema only; no calculation or API implementation. |
| **Stress-Tested P&L Impact** | ❌ **Missing** | Risk node has `pl_impact` in stub output; no real stress or P&L logic. |
| **Risk & Opportunity Signal Frequency** | ❌ **Missing** | No signals or metrics. |
| **Scenario-Based Rebalancing Recommendations** | ❌ **Missing** | Not present anywhere. |

---

## 2. What Is Implemented (Summary)

- **API structure**: FastAPI with routes for portfolios, scenarios, exposure, reports, alerts.
- **Workflow**: LangGraph pipeline `data_collection → exposure_calculation → risk_assessment → report_generation`; `POST /scenarios/{scenario_id}/run` runs it.
- **Schemas**: Scenario, Exposure (company/sector), Report, Alert, Portfolio (Pydantic + commented SQLAlchemy models).
- **Constants**: Scenario types (market, commodity, regulatory, etc.), risk levels, exposure methods, report formats, default scenario parameters.
- **Infrastructure**: Docker Compose (postgres, redis, backend, celery worker, celery beat), Celery (one health-check task).
- **Stub workflow nodes**: All four nodes run but return placeholder data (no real market data, exposure, risk, or report content).

---

## 3. What Remains to Fulfill the Resume (Prioritized)

### Tier 1 — Core analytics (needed for “enterprise-grade” claim)

1. **Database layer**  
   - Uncomment and wire SQLAlchemy models (Portfolio, Holding, Scenario, ScenarioRun, Exposure, Report, Alert).  
   - Run Alembic migrations.  
   - Use DB in APIs and workflow (store runs, exposures, reports, alerts).

2. **Market data integration**  
   - Implement `integrations/` (e.g. Alpha Vantage, Yahoo Finance, FRED) to fetch prices, indices, commodities, rates.  
   - Normalize to a common structure (symbol, date, value, type).

3. **Exposure service**  
   - Implement `exposure_service.calculate_exposure()`:  
     - Input: portfolio holdings + scenario type/parameters + market data.  
     - Output: company-level and sector-level exposure (e.g. % of AUM, factor betas, or scenario-specific deltas).  
   - Replace `_calculate_exposure` stub in `exposure_calculation` node with this service.

4. **Risk service**  
   - Implement `risk_service.assess_risk()`:  
     - Input: exposure result + scenario.  
     - Output: risk scores (e.g. 0–1), prioritized holdings, stress P&L impact.  
   - Replace `_assess_risk` stub in `risk_assessment` node.

5. **Report service**  
   - Implement `report_service.generate_report()`:  
     - Build board-ready content (summary, exposures, risk, recommendations).  
     - Export to PDF (reportlab), Excel (openpyxl), JSON.  
     - Persist report and link to ScenarioRun.  
   - Replace `_generate_report` stub and implement report download endpoint.

### Tier 2 — Alerts and monitoring

6. **Alerts**  
   - Define when to create alerts (e.g. risk score above threshold, scenario run completed, new high exposure).  
   - Persist alerts (use Alert model).  
   - Implement list/get/mark-read and, optionally, email/push.

7. **Continuous monitoring**  
   - Celery periodic task(s): run selected scenarios on a schedule (e.g. daily), compare to previous run, create alerts if thresholds breached.  
   - Use Celery Beat for scheduling.

### Tier 3 — Advanced metrics and recommendations

8. **Sensitivity and stress-testing**  
   - Portfolio sensitivity to market factors (e.g. betas, scenario deltas).  
   - Stress P&L: apply scenario shocks to holdings and aggregate P&L.

9. **Rebalancing recommendations**  
   - Logic that, given scenario outcomes and risk/return preferences, suggests rebalancing (e.g. reduce exposure to high-risk sectors or names).  
   - Expose via API and optionally in reports.

10. **Qualitative integration (optional)**  
    - News/sentiment API or internal corpus; combine with quantitative exposure/risk for “quantitative and qualitative insights.”

---

## 4. Best ML Models for This Use Case

Context: **portfolio scenario analysis**, **exposure and risk scoring**, **market/commodity/regulatory impact**, and **actionable insights**. Models can support:

- **Factor exposure / sensitivity** (how much the portfolio moves with factors).  
- **Scenario impact** (predict P&L or risk under a scenario).  
- **Risk scoring and prioritization**.  
- **Signal generation** (risk/opportunity).

### Recommended primary: **Factor models + scenario expansion**

- **Use case**: “Market factor and regulatory impact assessment,” “portfolio sensitivity,” “stress-tested P&L.”
- **Approach**:  
  - **Linear / ridge factor model**: Regress portfolio or holding returns on risk factors (market, sector, rates, commodity, volatility). Get factor loadings (betas) = sensitivity.  
  - **Scenario P&L**: Apply scenario shocks to factors × loadings to get portfolio/holding P&L.  
- **Pros**: Interpretable, audit-friendly, no heavy ML infra.  
- **ML role**: Optional — use ML to **estimate factor loadings** (e.g. rolling regression, or tree/linear models with regularization) or to **select/weight factors**.

### Recommended for risk scoring and prioritization

- **Use case**: “Scenario-driven risk scoring,” “prioritized holdings,” “emerging risks.”  
- **Options**:  
  - **Gradient Boosting (XGBoost/LightGBM)** or **Random Forest**: Train on historical (scenario type, market regime, exposures, macro vars) to predict risk level or loss. Use feature importance for “which factors drive risk.”  
  - **Logistic regression** or **small neural net**: Simpler alternative for risk classification (e.g. high/medium/low).  
- **Pros**: Handles non-linearity, good for prioritization and “which holdings are riskiest under this scenario.”

### Recommended for “opportunity” and signals

- **Use case**: “Strategic opportunities,” “risk & opportunity signal frequency.”  
- **Options**:  
  - **Classification or ranking model**: Label “opportunity” (e.g. undervalued vs. scenario, or post-scenario rebound). Train on historical scenarios and forward returns.  
  - **Anomaly detection** (e.g. Isolation Forest, autoencoder): Flag unusual exposure/risk combinations that might be opportunities or hidden risks.  
- **Pros**: Complements risk-only view; can drive “actionable insights” and rebalancing ideas.

### Recommended for qualitative integration

- **Use case**: “Quantitative and qualitative data integration.”  
- **Options**:  
  - **NLP / embeddings**: News/sentiment (e.g. finBERT, or embedding + classifier) per sector/name; combine sentiment score with quantitative exposure in a small fusion model (e.g. linear combo or shallow MLP).  
  - **LLM (optional)**: Use an LLM to summarize scenario report, exposures, and risks into narrative “board-ready” text and bullet recommendations.  
- **Pros**: Directly supports “qualitative and quantitative insights” and “board-ready” narrative.

### Summary table

| Goal | Recommended approach | Typical model |
|------|----------------------|----------------|
| Factor exposure & sensitivity | Factor model (regression of returns on factors) | Linear/Ridge regression; optionally ML for factor selection |
| Scenario P&L / stress-test | Apply scenario shocks to factor loadings | Same factor model + arithmetic |
| Risk scoring & prioritization | Predict risk level or loss from features | XGBoost/LightGBM or Random Forest |
| Opportunity / signals | Classification or ranking; anomaly detection | Tree models; Isolation Forest / autoencoder |
| Qualitative integration | Sentiment + quant fusion; narrative summary | finBERT/sentiment model; optional LLM for narrative |

**Practical order**: Implement **factor-based exposure and scenario P&L** first (interpretable and matches resume). Add **tree-based risk scoring** for prioritization. Then add **signals/opportunity** and **qualitative/NLP** as Tier 3.

---

## 5. Next Steps (Checklist) — all complete

- [x] Enable and migrate DB (uncomment models, Alembic).  
- [x] Implement market data integrations and market_data_service.  
- [x] Implement exposure_service and plug into exposure_calculation node.  
- [x] Implement risk_service (scores, P&L) and plug into risk_assessment node.  
- [x] Implement report_service (PDF/Excel/JSON) and report download.  
- [x] Implement alert creation and listing; optional notification delivery.  
- [x] Add Celery periodic tasks for continuous scenario monitoring.  
- [x] Add sensitivity/stress metrics and rebalancing recommendation logic.  
- [x] Introduce ML: factor model for sensitivity and P&L; XGBoost/LightGBM for risk scoring; optional NLP/LLM for qualitative and narrative.

This gives you a clear map from “what the resume says” to “what’s built” and “what to build next,” plus a concrete ML strategy for PortfolioQ.
