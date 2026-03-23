#!/usr/bin/env python3
"""
Scenario pipeline — run scenario simulation for a portfolio (no DB required for engine-only).
For full workflow (data collection → exposure → risk → report), use API POST /scenarios/{id}/run.
"""
import logging
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def run_scenario_pipeline(
    holdings: list[dict],
    scenario_type: str = "market_shock",
    scale: float = 1.0,
) -> dict:
    """Run scenario simulation engine only (factor model + exposure + sector vulnerability)."""
    from src.scenario_engine import run_scenario_simulation

    return run_scenario_simulation(holdings, scenario_type, scale=scale)


if __name__ == "__main__":
    # Example: single holding
    sample_holdings = [
        {"symbol": "AAPL", "quantity": 100, "current_price": 150.0, "average_price": 140.0, "sector": "Technology"},
    ]
    out = run_scenario_pipeline(sample_holdings, scenario_type="market_shock")
    print("Scenario result:", out.get("portfolio_pl_impact"), out.get("sensitivity_score"))
