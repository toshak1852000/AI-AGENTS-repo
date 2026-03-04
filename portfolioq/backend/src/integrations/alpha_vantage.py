"""Alpha Vantage integration (supplementary data)."""
import logging
import os
from typing import Any

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
AV_BASE = "https://www.alphavantage.co/query"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def fetch_daily_adjusted(symbol: str, outputsize: str = "compact") -> pd.DataFrame:
    """Fetch daily adjusted prices from Alpha Vantage (fallback to yfinance if no key)."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        logger.info("ALPHA_VANTAGE_API_KEY not set; skipping AV for %s", symbol)
        return pd.DataFrame()
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": outputsize,
        "apikey": api_key,
    }
    r = requests.get(AV_BASE, params=params, timeout=15)
    r.raise_for_status()
    data = r.json().get("Time Series (Daily)", {})
    if not data:
        return pd.DataFrame()
    rows = []
    for date, vals in data.items():
        rows.append({
            "date": date,
            "close_price": float(vals["5. adjusted close"]),
            "volume": float(vals["6. volume"]),
        })
    df = pd.DataFrame(rows).set_index("date")
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def fetch_sector_performance() -> dict[str, Any]:
    """Fetch sector performance from Alpha Vantage."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key:
        return {}
    params = {"function": "SECTOR", "apikey": api_key}
    try:
        r = requests.get(AV_BASE, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("Rank A: Real-Time Performance", {})
    except Exception as exc:
        logger.warning("Failed AV sector: %s", exc)
        return {}
