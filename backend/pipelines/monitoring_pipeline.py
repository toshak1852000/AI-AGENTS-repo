#!/usr/bin/env python3
"""
Monitoring pipeline — data drift, model drift, prediction anomalies, risk threshold breaches.
Can be run on a schedule (e.g. Celery) to trigger alerts.
"""
import logging
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def run_monitoring_pipeline(
    reference_data_path: str | None = None,
    current_data_path: str | None = None,
    risk_score: float | None = None,
) -> dict:
    """
    Run monitoring checks. If paths provided, load DataFrames and check data drift.
    If risk_score provided, check threshold breach.
    """
    import pandas as pd
    from src.monitoring import check_data_drift, check_risk_threshold_breach

    results: dict = {"data_drift": None, "risk_breach": None}
    if reference_data_path and current_data_path and os.path.isfile(reference_data_path) and os.path.isfile(current_data_path):
        ref = pd.read_csv(reference_data_path)
        cur = pd.read_csv(current_data_path)
        results["data_drift"] = check_data_drift(ref, cur)
    if risk_score is not None:
        results["risk_breach"] = check_risk_threshold_breach(risk_score)
    return results


if __name__ == "__main__":
    # Example: risk threshold only
    out = run_monitoring_pipeline(risk_score=0.85)
    print("Monitoring result:", out)
