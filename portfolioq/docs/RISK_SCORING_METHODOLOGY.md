# Risk Scoring Methodology

## Overview

Risk scoring combines **quantitative ML predictions**, **rule-based financial logic**, and optional **statistical confidence intervals** to produce portfolio and holding-level risk metrics.

---

## 1. Portfolio Risk Score

- **ML model:** XGBoost classifier trained on synthetic/real portfolio features; outputs class probabilities; risk_score is derived from probability-weighted class indices (0–1 scale).
- **Features:** total_exposure_pct, market_beta, scenario_severity, sector_concentration, top_holding_weight, n_holdings, market_volatility, oil_exposure, bond_exposure, regulatory_factor (built from exposure and scenario in `risk_service.assess_risk`).
- **Rule-based fallback:** When model is not fitted, a simple score from features and thresholds is used (`risk_model._fallback_risk`).
- **Levels:** low (<0.3), medium (0.3–0.6), high (0.6–0.8), critical (≥0.8) (configurable in `configs/config.yaml`).

---

## 2. Company Exposure Risk

- Per-holding risk is derived from exposure (e.g. |scenario_pl_impact|/market_value) and scaled; combined with factor betas for opportunity model input.
- **Opportunity model:** Isolation Forest on holding features; outputs anomaly_score, is_anomaly, signal (strong_buy → sell), opportunity_score.
- **Risk engine:** `risk_scoring.engine.compute_risk_score(features)` for portfolio; `compute_holding_risk(...)` for per-holding signals (wraps opportunity model).

---

## 3. Sector Vulnerability

- Sector vulnerability is computed in the **scenario engine** as P&L per sector as % of portfolio (see SCENARIO_ENGINE_DESIGN.md).
- Risk reports and dashboards show sector-level exposure and vulnerability for board-ready output.

---

## 4. Scenario Probability Impact

- Scenario severity is mapped per scenario type (e.g. market_shock 0.9, regulatory_change 0.6) and fed into the risk feature vector.
- Combined with market_beta and factor exposures to capture scenario probability impact in the risk score.

---

## 5. Confidence Intervals

- Optional `include_confidence=True` in `compute_risk_score` can extend to bootstrap or posterior intervals from class probabilities; currently returns a placeholder structure for integration.

---

## 6. Monitoring and Alerts

- **Risk threshold breach:** Monitoring pipeline and alert system flag when risk_score ≥ critical (0.8) or high (0.6) (see config and `monitoring.drift_monitor.check_risk_threshold_breach`).
- Alerts are persisted and can trigger dashboard and (when configured) email notifications.
