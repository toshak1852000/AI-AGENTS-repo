"""
Data drift detection — PSI and threshold-based flagging for monitoring pipeline.
"""
import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_psi(
    expected: pd.Series,
    actual: pd.Series,
    bins: int = 10,
) -> float:
    """
    Population Stability Index between expected (reference) and actual (current) distributions.
    PSI > 0.25 often indicates significant drift.
    """
    try:
        combined = pd.concat([expected, actual])
        breakpoints = np.percentile(combined.dropna(), np.linspace(0, 100, bins + 1)[1:-1])
        if len(breakpoints) < 2:
            breakpoints = np.linspace(combined.min(), combined.max(), bins + 1)[1:-1]
        breakpoints = np.unique(breakpoints)
        if len(breakpoints) < 2:
            return 0.0
        exp_hist, _ = np.histogram(expected.dropna(), bins=np.r_[-np.inf, breakpoints, np.inf])
        act_hist, _ = np.histogram(actual.dropna(), bins=np.r_[-np.inf, breakpoints, np.inf])
        exp_pct = (exp_hist + 1e-10) / (exp_hist.sum() + 1e-10 * len(exp_hist))
        act_pct = (act_hist + 1e-10) / (act_hist.sum() + 1e-10 * len(act_hist))
        psi = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
        return float(psi)
    except Exception as exc:
        logger.warning("compute_psi failed: %s", exc)
        return 0.0


def detect_data_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    column: str | None = None,
    psi_threshold: float = 0.25,
) -> dict[str, Any]:
    """
    Detect drift between reference and current dataset.
    If column is None, compute PSI for all numeric columns and return max.
    """
    result: dict[str, Any] = {"drift_detected": False, "psi_values": {}, "max_psi": 0.0}
    cols = [column] if column else reference.select_dtypes(include=[np.number]).columns.tolist()
    if not cols:
        return result
    for col in cols:
        if col not in current.columns:
            continue
        exp = reference[col].dropna()
        cur = current[col].dropna()
        if exp.empty or cur.empty:
            continue
        psi = compute_psi(exp, cur)
        result["psi_values"][col] = round(psi, 4)
        if psi > result["max_psi"]:
            result["max_psi"] = psi
    result["drift_detected"] = result["max_psi"] > psi_threshold
    result["max_psi"] = round(result["max_psi"], 4)
    return result
