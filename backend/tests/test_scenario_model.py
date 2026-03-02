import pytest
from datetime import datetime
from src.schemas.scenario import Scenario, ScenarioCreate, ScenarioRun, ScenarioRunCreate
from src.config.constants import ScenarioType

def test_scenario_schema():
    """Test scenario Pydantic schema validation."""
    data = {
        "name": "Market Crash",
        "name": "Global Recession",
        "description": "A significant economic downturn across major markets.",
        "type": ScenarioType.MARKET_SHOCK,
        "parameters": {"market_decline_percentage": 30.0, "duration_months": 12},
    }
    
    schema = ScenarioCreate(**data)
    assert schema.name == "Global Recession"
    assert schema.type == ScenarioType.MARKET_SHOCK
    assert schema.parameters["market_decline_percentage"] == 30.0
    assert schema.status == "draft" # Verify field exists with default

    scenario = Scenario(
        id="scen_123",
        created_at=datetime.utcnow(),
        **data
    )
    assert scenario.id == "scen_123"

def test_scenario_run_schema():
    """Test scenario run Pydantic schema validation."""
    data = {
        "scenario_id": "scen_123",
        "portfolio_ids": ["port_1", "port_2"],
        "status": "pending"
    }
    
    run_create = ScenarioRunCreate(**data)
    assert run_create.scenario_id == "scen_123"
    assert len(run_create.portfolio_ids) == 2
    assert "port_1" in run_create.portfolio_ids
    assert run_create.status == "pending"
    
    run = ScenarioRun(
        id="run_123",
        started_at=datetime.utcnow(),
        **data
    )
    assert run.id == "run_123"
    assert run.results is None


def test_scenario_create_json_schema():
    """Verify that ScenarioCreate correctly exposes its documentation payload."""
    schema = ScenarioCreate.model_json_schema()
    
    # Prove the JSON Schema properly generates the 'example' block configured for API docs
    assert "example" in schema
    example = schema["example"]
    
    assert example["type"] == "market_shock"
    assert "parameters" in example
    assert example["parameters"]["market_decline_percentage"] == 20.0
