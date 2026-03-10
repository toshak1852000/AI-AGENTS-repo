"""
Scenario simulation engine — market shocks, commodity spikes, rate changes,
geopolitical and regulatory scenarios. Outputs P&L impact, exposure changes, sector vulnerability.
"""
from src.scenario_engine.engine import run_scenario_simulation, get_scenario_shocks

__all__ = ["run_scenario_simulation", "get_scenario_shocks"]
