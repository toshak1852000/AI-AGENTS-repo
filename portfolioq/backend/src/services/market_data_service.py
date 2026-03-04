"""Market data service: fetch, normalize and persist market data."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from src.integrations import yahoo_finance as yf_int
from src.integrations import fred as fred_int
from src.models.market_data import MarketData, CommodityPrice

logger = logging.getLogger(__name__)

COMMODITY_SYMBOLS = {
    "crude_oil": "CL=F",
    "natural_gas": "NG=F",
    "gold": "GC=F",
    "silver": "SI=F",
    "copper": "HG=F",
    "wheat": "ZW=F",
    "corn": "ZC=F",
}


def fetch_and_store_prices(db: Session, symbols: list[str], period: str = "1y") -> dict[str, int]:
    """Fetch OHLCV data for symbols and persist to DB. Returns {symbol: rows_saved}."""
    result: dict[str, int] = {}
    for sym in symbols:
        try:
            df = yf_int.fetch_price_history(sym, period=period)
            if df.empty:
                continue
            rows = 0
            for dt, row in df.iterrows():
                existing = db.query(MarketData).filter(
                    MarketData.symbol == sym, MarketData.date == dt
                ).first()
                if not existing:
                    db.add(MarketData(
                        id=str(uuid.uuid4()), symbol=sym, date=dt,
                        open_price=row.get("open_price"),
                        high_price=row.get("high_price"),
                        low_price=row.get("low_price"),
                        close_price=row["close_price"],
                        volume=row.get("volume"),
                    ))
                    rows += 1
            db.commit()
            result[sym] = rows
        except Exception as exc:
            logger.warning("Failed to store data for %s: %s", sym, exc)
    return result


def get_latest_prices(db: Session, symbols: list[str]) -> dict[str, float]:
    """Return latest close price per symbol from DB, fall back to live yfinance."""
    prices: dict[str, float] = {}
    for sym in symbols:
        row = (
            db.query(MarketData)
            .filter(MarketData.symbol == sym)
            .order_by(MarketData.date.desc())
            .first()
        )
        if row:
            prices[sym] = float(row.close_price)
        else:
            live = yf_int.fetch_current_price(sym)
            if live:
                prices[sym] = live
    return prices


def get_price_history(db: Session, symbol: str, limit: int = 252) -> pd.DataFrame:
    """Return price history from DB as DataFrame."""
    rows = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol)
        .order_by(MarketData.date.asc())
        .limit(limit)
        .all()
    )
    if not rows:
        return pd.DataFrame()
    data = [{"date": r.date, "close_price": float(r.close_price)} for r in rows]
    return pd.DataFrame(data).set_index("date")


def collect_scenario_market_data(
    db: Session,
    scenario: dict[str, Any],
    portfolio_holdings: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Collect all required market data for a scenario analysis.
    Returns normalized structure for downstream nodes.
    """
    symbols = list({h["symbol"] for h in portfolio_holdings})
    scenario_type = scenario.get("type", "market_shock")

    # Fetch current prices
    prices = get_latest_prices(db, symbols)

    # Fetch factor returns
    factor_rets = yf_int.fetch_factor_returns(period="6mo")
    factor_stats: dict[str, Any] = {}
    if not factor_rets.empty:
        for col in factor_rets.columns:
            factor_stats[col] = {
                "mean_return": round(float(factor_rets[col].mean()), 6),
                "volatility": round(float(factor_rets[col].std()), 6),
            }

    # Macro data
    macro = fred_int.fetch_macro_indicators()

    return {
        "scenario_id": scenario.get("id", ""),
        "scenario_type": scenario_type,
        "symbols": symbols,
        "current_prices": prices,
        "factor_stats": factor_stats,
        "macro_indicators": macro,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
