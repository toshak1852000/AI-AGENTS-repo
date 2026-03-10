"""
Data ingestion layer — unified facade for financial market APIs,
macroeconomic datasets, commodity feeds, and portfolio holdings.
Connectors for structured and unstructured data; used by pipelines and services.
"""
from src.ingestion.connectors import (
    ingest_market_prices,
    ingest_factor_returns,
    ingest_macro_indicators,
    ingest_portfolio_holdings_for_scenario,
)

__all__ = [
    "ingest_market_prices",
    "ingest_factor_returns",
    "ingest_macro_indicators",
    "ingest_portfolio_holdings_for_scenario",
]
