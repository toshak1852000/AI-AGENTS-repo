"""Yahoo Finance integration via yfinance."""
import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

FACTOR_TICKERS = {
    "market": "^GSPC",
    "small_cap": "IWM",
    "value": "IWD",
    "growth": "IWF",
    "momentum": "MTUM",
    "low_vol": "USMV",
    "quality": "QUAL",
    "oil": "USO",
    "gold": "GLD",
    "bonds": "TLT",
    "usd": "UUP",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_price_history(
    symbol: str,
    start: datetime | None = None,
    end: datetime | None = None,
    period: str = "1y",
) -> pd.DataFrame:
    """Return OHLCV DataFrame for a symbol."""
    if start and end:
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)
    else:
        df = yf.download(symbol, period=period, progress=False, auto_adjust=True)

    if df.empty:
        logger.warning("No data returned for %s", symbol)
        return pd.DataFrame()

    # Flatten MultiIndex columns if any
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    df = df.rename(columns={"open": "open_price", "high": "high_price", "low": "low_price", "close": "close_price"})
    df.index.name = "date"
    return df


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_current_price(symbol: str) -> float | None:
    """Return the latest closing price for a symbol."""
    try:
        t = yf.Ticker(symbol)
        info = t.fast_info
        return float(info.last_price)
    except Exception as exc:
        logger.warning("Could not fetch current price for %s: %s", symbol, exc)
        return None


def fetch_factor_returns(period: str = "1y") -> pd.DataFrame:
    """Fetch risk factor returns (market, size, value, momentum, etc.)."""
    tickers = list(FACTOR_TICKERS.values())
    try:
        raw = yf.download(tickers, period=period, progress=False, auto_adjust=True)
        if isinstance(raw.columns, pd.MultiIndex):
            prices = raw["Close"]
        else:
            prices = raw
        returns = prices.pct_change().dropna()
        # Rename to factor names
        inv = {v: k for k, v in FACTOR_TICKERS.items()}
        returns = returns.rename(columns=inv)
        return returns
    except Exception as exc:
        logger.error("Failed to fetch factor returns: %s", exc)
        return pd.DataFrame()


def fetch_multiple_symbols(symbols: list[str], period: str = "1y") -> dict[str, pd.DataFrame]:
    """Fetch history for multiple symbols."""
    result: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        try:
            df = fetch_price_history(sym, period=period)
            if not df.empty:
                result[sym] = df
        except Exception as exc:
            logger.warning("Failed %s: %s", sym, exc)
    return result


def get_symbol_info(symbol: str) -> dict[str, Any]:
    """Return basic ticker info (sector, name, etc.)."""
    try:
        t = yf.Ticker(symbol)
        info = t.info
        return {
            "symbol": symbol,
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap"),
        }
    except Exception as exc:
        logger.warning("Could not fetch info for %s: %s", symbol, exc)
        return {"symbol": symbol, "name": symbol, "sector": "Unknown", "industry": "Unknown"}
