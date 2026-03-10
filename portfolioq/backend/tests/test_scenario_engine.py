"""Tests for scenario engine."""
import pytest

from src.scenario_engine import get_scenario_shocks, run_scenario_simulation


def test_get_scenario_shocks():
    shocks = get_scenario_shocks("market_shock")
    assert "market" in shocks
    assert isinstance(shocks["market"], (int, float))


def test_run_scenario_simulation(sample_holdings):
    result = run_scenario_simulation(sample_holdings, "market_shock")
    assert "scenario_type" in result
    assert "portfolio_pl_impact" in result
    assert "sensitivity_score" in result
    assert "company_exposures" in result
    assert "sector_vulnerability" in result
