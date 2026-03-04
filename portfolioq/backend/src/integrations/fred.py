"""FRED (Federal Reserve Economic Data) integration."""
import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

MACRO_SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "gdp_growth": "A191RL1Q225SBEA",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "corporate_spread": "BAA10Y",
    "oil_price_wti": "DCOILWTICO",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def fetch_series(series_id: str, start: str = "2020-01-01") -> pd.Series:
    """Fetch a FRED series as a pandas Series indexed by date."""
    api_key = os.getenv("FRED_API_KEY", "")
    if not api_key:
        logger.warning("FRED_API_KEY not set; returning empty series for %s", series_id)
        return pd.Series(dtype=float)
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start,
    }
    r = requests.get(FRED_BASE_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json().get("observations", [])
    rows = {obs["date"]: float(obs["value"]) for obs in data if obs["value"] != "."}
    return pd.Series(rows, name=series_id)


def fetch_macro_indicators(start: str = "2020-01-01") -> dict[str, Any]:
    """Fetch all macro indicators; return as dict of latest values."""
    result: dict[str, Any] = {}
    for name, series_id in MACRO_SERIES.items():
        try:
            s = fetch_series(series_id, start)
            if not s.empty:
                result[name] = {
                    "latest": float(s.iloc[-1]),
                    "date": str(s.index[-1]),
                    "series_id": series_id,
                }
        except Exception as exc:
            logger.warning("Failed to fetch FRED %s (%s): %s", name, series_id, exc)
            result[name] = {"latest": None, "date": None, "series_id": series_id}
    return result
