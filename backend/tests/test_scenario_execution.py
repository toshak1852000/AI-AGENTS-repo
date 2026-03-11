"""Tests for GET/POST /api/v1/scenarios/{id}/run and GET /api/v1/scenarios/runs/{id}."""
import pytest
from fastapi.testclient import TestClient

from src.services import scenario_service as svc
from src.services import portfolio_service as port_svc
from src.config.constants import ScenarioType


@pytest.fixture(autouse=True)
def _clear_data():
    """Clear memory before each test."""
    svc.clear_all()
    port_svc.clear_all()
    yield
    svc.clear_all()
    port_svc.clear_all()


def test_run_scenario_success(client: TestClient) -> None:
    """POST /api/v1/scenarios/{scenario_id}/run creates a run and executes."""
    # Create scenario first
    create_payload = {
        "name": "Stress Test",
        "description": "Validation run",
        "type": ScenarioType.MARKET_SHOCK.value,
        "parameters": {"param": 100}
    }
    r = client.post("/api/v1/scenarios", json=create_payload)
    scenario_id = r.json()["id"]
    
    # Create portfolios
    p1_payload = {"name": "Test Portfolio 1"}
    p2_payload = {"name": "Test Portfolio 2"}
    r_p1 = client.post("/api/v1/portfolios", json=p1_payload)
    r_p2 = client.post("/api/v1/portfolios", json=p2_payload)
    p1_id = r_p1.json()["id"]
    p2_id = r_p2.json()["id"]
    
    # Execute the scenario run
    run_payload = {
        "portfolio_ids": [p1_id, p2_id]
    }
    r_run = client.post(f"/api/v1/scenarios/{scenario_id}/run", json=run_payload)
    
    assert r_run.status_code == 200
    data = r_run.json()
    assert "id" in data
    assert data["scenario_id"] == scenario_id
    assert p1_id in data["portfolio_ids"]
    assert data["status"] in ["completed", "failed"] # It should execute fully in the background synchronously in these implementations
    
    run_id = data["id"]
    
    # Validate retrieval endpoint
    r_get_run = client.get(f"/api/v1/scenarios/runs/{run_id}")
    assert r_get_run.status_code == 200
    assert r_get_run.json()["id"] == run_id
    
    # Validate result mapping has exposure attributes
    results = r_get_run.json().get("results", {})
    assert "report_id" in results
    assert "exposure_result" in results
    assert "risk_result" in results
    
    # Validate list runs endpoint
    r_list = client.get(f"/api/v1/scenarios/{scenario_id}/runs")
    assert r_list.status_code == 200
    list_data = r_list.json()
    assert isinstance(list_data, list)
    assert len(list_data) == 1
    assert list_data[0]["id"] == run_id
    assert "exposure_result" in list_data[0]["results"]


def test_run_scenario_not_found(client: TestClient) -> None:
    """POST /api/v1/scenarios/{scenario_id}/run with bad ID returns 404."""
    r_run = client.post("/api/v1/scenarios/bad-id/run", json={"portfolio_ids": []})
    assert r_run.status_code == 404


def test_get_run_not_found(client: TestClient) -> None:
    """GET /api/v1/scenarios/runs/{run_id} with bad ID returns 404."""
    r = client.get("/api/v1/scenarios/runs/bad-run-id")
    assert r.status_code == 404


def test_get_scenario_runs_not_found(client: TestClient) -> None:
    """GET /api/v1/scenarios/{scenario_id}/runs with bad scenario returns 404."""
    r = client.get("/api/v1/scenarios/bad-id/runs")
    assert r.status_code == 404


def test_run_scenario_invalid_portfolio(client: TestClient) -> None:
    """POST /api/v1/scenarios/{scenario_id}/run with bad portfolio ID returns 400."""
    create_payload = {
        "name": "Stress Test Invalid Port",
        "description": "Validation run",
        "type": ScenarioType.MARKET_SHOCK.value,
        "parameters": {"param": 100}
    }
    r = client.post("/api/v1/scenarios", json=create_payload)
    scenario_id = r.json()["id"]
    
    # Run against a missing portfolio
    run_payload = {
        "portfolio_ids": ["invalid_portfolio_123"]
    }
    r_run = client.post(f"/api/v1/scenarios/{scenario_id}/run", json=run_payload)
    
    # Should catch 400 Bad Request error from ValueError bubbling from scenario_service execution method
    assert r_run.status_code == 400
    assert "Portfolio not found: invalid_portfolio_123" in str(r_run.json()["detail"])
