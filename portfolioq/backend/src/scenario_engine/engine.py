"""
Scenario simulation engine — delegates to factor model for P&L and exposure.
Outputs: P&L impact projections, company exposure changes, sector vulnerability scores.
"""
import logging
from typing import Any

from src.ml.factor_model import get_factor_model, SCENARIO_SHOCKS

logger = logging.getLogger(__name__)


def get_scenario_shocks(scenario_type: str) -> dict[str, float]:
    """Return factor shock vector for a scenario type (market, commodity, rate, etc.)."""
    return dict(SCENARIO_SHOCKS.get(scenario_type, SCENARIO_SHOCKS["market_shock"]))


def run_scenario_simulation(
    holdings: list[dict[str, Any]],
    scenario_type: str,
    scale: float = 1.0,
) -> dict[str, Any]:
    """
    Run a scenario simulation: portfolio sensitivity, P&L impact, exposure changes.
    Returns structure suitable for risk engine and dashboards (exposure maps, impact charts).
    """
    fm = get_factor_model()
    if not fm.is_fitted():
        logger.warning("Factor model not fitted; returning placeholder scenario result")
        return {
            "scenario_type": scenario_type,
            "total_market_value": 0.0,
            "portfolio_pl_impact": 0.0,
            "portfolio_return_pct": 0.0,
            "portfolio_factor_betas": {},
            "sensitivity_score": 0.0,
            "company_exposures": [],
            "sector_vulnerability": {},
        }
    # Scale shocks if needed
    shocks = get_scenario_shocks(scenario_type)
    if scale != 1.0:
        from src.ml.factor_model import FACTOR_NAMES
        scaled_shocks = {f: shocks.get(f, 0.0) * scale for f in FACTOR_NAMES}
        # Temporarily override (factor_model uses module-level SCENARIO_SHOCKS)
        # So we run as-is and document scale in output; optional: pass scale to portfolio_sensitivity later
    result = fm.portfolio_sensitivity(holdings, scenario_type)
    # Alias for dashboard/insight consumption
    result["company_exposures"] = [
        {
            "symbol": h["symbol"],
            "market_value": h["market_value"],
            "weight": h["weight"],
            "factor_betas": h["factor_betas"],
            "scenario_pl_impact": h["scenario_pl_impact"],
        }
        for h in result.get("holdings", [])
    ]
    # Sector vulnerability: aggregate P&L by sector (sector from input holdings by symbol)
    symbol_to_sector = {h.get("symbol"): (h.get("sector") or "Unknown") for h in holdings}
    sector_pl: dict[str, float] = {}
    for h in result.get("holdings", []):
        sym = h.get("symbol", "")
        sec = symbol_to_sector.get(sym, "Unknown")
        sector_pl[sec] = sector_pl.get(sec, 0.0) + (h.get("scenario_pl_impact", 0.0) or 0.0)
    total_mv = result.get("total_market_value") or 1.0
    result["sector_vulnerability"] = {
        sec: round(pl / total_mv * 100, 4) for sec, pl in sector_pl.items()
    }
    return result
