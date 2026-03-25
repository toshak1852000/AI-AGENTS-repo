"""
Data cleaning: missing value handling, outlier detection, time-series normalization.
"""
import logging
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def handle_missing(
    series: pd.Series,
    strategy: Literal["drop", "fill_zero", "interpolate"] = "drop",
) -> pd.Series:
    """Handle missing values in a series."""
    if strategy == "drop":
        return series.dropna()
    if strategy == "fill_zero":
        return series.fillna(0.0)
    if strategy == "interpolate":
        return series.interpolate(method="linear").bfill().fillna(0.0)
    return series


def detect_outliers(
    series: pd.Series,
    method: Literal["iqr", "zscore", "winsorize"] = "iqr",
    z_threshold: float = 3.0,
) -> pd.Series:
    """
    Return a boolean mask: True = inlier, False = outlier.
    """
    if method == "iqr":
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            return pd.Series(True, index=series.index)
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        return (series >= lower) & (series <= upper)
    if method == "zscore":
        mean, std = series.mean(), series.std()
        if std == 0:
            return pd.Series(True, index=series.index)
        z = np.abs((series - mean) / std)
        return z <= z_threshold
    if method == "winsorize":
        low, high = series.quantile(0.01), series.quantile(0.99)
        return (series >= low) & (series <= high)
    return pd.Series(True, index=series.index)


def clean_series(
    series: pd.Series,
    missing_strategy: Literal["drop", "fill_zero", "interpolate"] = "drop",
    outlier_method: Literal["iqr", "zscore", "winsorize"] = "iqr",
    drop_outliers: bool = False,
) -> pd.Series:
    """
    Clean a time series: handle missing, optionally drop or winsorize outliers.
    If drop_outliers=False, outliers are left in but flagged (caller can use detect_outliers separately).
    """
    s = handle_missing(series, strategy=missing_strategy)
    mask = detect_outliers(s, method=outlier_method)
    if drop_outliers:
        s = s[mask]
    return s
