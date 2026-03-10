"""
Unified data ingestion connectors — financial APIs, macro, commodity, portfolio holdings.
Delegates to existing integrations and market_data_service; provides single entry for pipelines.
"""
import logging
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.integrations import yahoo_finance as yf_int
from src.integrations import fred as fred_int
from src.services.market_data_service import (
    get_latest_prices,
    get_price_history,
    collect_scenario_market_data,
    fetch_and_store_prices,
)

logger = logging.getLogger(__name__)


def ingest_market_prices(
    db: Session,
    symbols: list[str],
    period: str = "2y",
    persist: bool = True,
) -> dict[str, Any]:
    """
    Ingest OHLCV market prices for given symbols.
    Returns dict with prices DataFrame (if not persisted) or rows_saved per symbol.
    """
    if persist:
        result = fetch_and_store_prices(db, symbols, period=period)
        return {"provider": "yahoo_finance", "rows_saved": result, "symbols": symbols}
    # Non-persisting: fetch and return as structure for downstream
    out: dict[str, Any] = {"provider": "yahoo_finance", "symbols": symbols, "data": {}}
    for sym in symbols:
        try:
            df = yf_int.fetch_price_history(sym, period=period)
            if not df.empty:
                out["data"][sym] = df
        except Exception as exc:
            logger.warning("ingest_market_prices %s: %s", sym, exc)
    return out


def ingest_factor_returns(period: str = "2y") -> pd.DataFrame:
    """Ingest factor returns (market, size, value, momentum, oil, gold, bonds, usd)."""
    return yf_int.fetch_factor_returns(period=period)


def ingest_macro_indicators(start: str = "2020-01-01") -> dict[str, Any]:
    """Ingest macroeconomic indicators from FRED."""
    return fred_int.fetch_macro_indicators(start=start)


def ingest_portfolio_holdings_for_scenario(
    db: Session,
    scenario: dict[str, Any],
    portfolio_holdings: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Collect all market data required for a scenario run (prices, factor stats, macro).
    Aligns with workflow data_collection; returns structure expected by exposure/risk nodes.
    """
    return collect_scenario_market_data(db, scenario, portfolio_holdings)
