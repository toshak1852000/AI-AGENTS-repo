# Data Pipelines

## Overview

PortfolioQ data pipelines cover **ingestion**, **validation**, **cleaning**, and **drift detection**.

---

## 1. Data Ingestion

- **Sources:** Financial market APIs (Yahoo Finance, FRED, Alpha Vantage), portfolio holdings from DB.
- **Entry points:**  
  - `src.ingestion.ingest_market_prices(db, symbols, period, persist)` — OHLCV fetch and optional DB persist.  
  - `src.ingestion.ingest_factor_returns(period)` — Factor returns (market, size, value, momentum, oil, gold, bonds, usd).  
  - `src.ingestion.ingest_macro_indicators(start)` — FRED macro indicators.  
  - `src.ingestion.ingest_portfolio_holdings_for_scenario(db, scenario, holdings)` — Full market data for a scenario run (used by workflow).
- **Connectors:** Implemented in `backend/src/ingestion/connectors.py`; delegate to `integrations/yahoo_finance`, `integrations/fred`, and `services/market_data_service`.

---

## 2. Data Validation

- **Schema:** `src.data_validation.schema.validate_price_schema(df)`, `validate_factor_schema(df)` — Required columns for price and factor data.
- **Missing values:** `handle_missing(series, strategy)` — Strategies: `drop`, `fill_zero`, `interpolate`.
- **Outliers:** `detect_outliers(series, method)` — Methods: `iqr`, `zscore`, `winsorize`.
- **Cleaning:** `clean_series(series, missing_strategy, outlier_method, drop_outliers)` — Single entry for cleaning a series.

---

## 3. Data Drift Detection

- **PSI:** `src.data_validation.drift.compute_psi(expected, actual, bins)` — Population Stability Index between reference and current distribution.
- **Drift check:** `detect_data_drift(reference_df, current_df, column, psi_threshold)` — Per-column or full numeric columns; flags when max PSI > threshold.
- **Use:** Monitoring pipeline and alerting when drift is detected (config: `configs/config.yaml` → `data_validation.drift_psi_threshold`).

---

## 4. Pipeline Automation

- **Daily ingestion:** Celery task `refresh_all_prices` (market data); workflow data_collection uses `collect_scenario_market_data` on demand.
- **Training:** `backend/pipelines/training_pipeline.py` — Single-command model retraining; can be triggered by Celery `retrain_all_models`.
- **Scenario:** `backend/pipelines/scenario_pipeline.py` — Scenario engine only; full workflow via `POST /scenarios/{id}/run`.
- **Monitoring:** `backend/pipelines/monitoring_pipeline.py` — Data drift (optional CSV ref/current), risk threshold breach.

All pipelines run with a single command or API call; no manual steps required for normal operation.
