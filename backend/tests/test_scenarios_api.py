"""Tests for GET/POST/PUT/DELETE /api/v1/scenarios."""
import pytest
from fastapi.testclient import TestClient

from src.services import scenario_service as svc
from src.schemas.scenario import ScenarioCreate
from src.config.constants import ScenarioType


@pytest.fixture(autouse=True)
def _clear_scenarios():
    """Clear in-memory scenarios before each test."""
    svc.clear_all()
    yield
    svc.clear_all()


def test_list_scenarios_empty(client: TestClient) -> None:
    """GET /api/v1/scenarios returns paginated list; empty initially."""
    r = client.get("/api/v1/scenarios")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["scenarios"] == []


def test_create_and_get_scenario(client: TestClient) -> None:
    """POST /api/v1/scenarios creates a scenario and GET retrieves it."""
    payload = {
        "name": "Market Drop",
        "description": "50% drop",
        "type": ScenarioType.MARKET_SHOCK.value,
        "parameters": {"drop": 50}
    }
    r = client.post("/api/v1/scenarios", json=payload)
    assert r.status_code == 201
    
    data = r.json()
    assert "id" in data
    assert data["name"] == "Market Drop"
    assert data["parameters"]["drop"] == 50
    assert data["status"] == "draft"  # Default status
    
    scenario_id = data["id"]
    r_get = client.get(f"/api/v1/scenarios/{scenario_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == scenario_id


def test_create_scenario_invalid_type(client: TestClient) -> None:
    """POST with an invalid scenario type returns 422."""
    payload = {
        "name": "Invalid Type Drop",
        "description": "50% drop",
        "type": "not_a_valid_type",
        "parameters": {"drop": 50}
    }
    r = client.post("/api/v1/scenarios", json=payload)
    assert r.status_code == 422


def test_create_scenario_missing_parameters(client: TestClient) -> None:
    """POST with missing parameters returns 422."""
    payload = {
        "name": "Missing Params",
        "description": "50% drop",
        "type": ScenarioType.MARKET_SHOCK.value,
        # missing parameters field
    }
    r = client.post("/api/v1/scenarios", json=payload)
    assert r.status_code == 422


def test_get_scenario_not_found(client: TestClient) -> None:
    """GET /api/v1/scenarios/{id} returns 404 when scenario does not exist."""
    r = client.get("/api/v1/scenarios/nonexistent-id")
    assert r.status_code == 404
    assert "not found" in r.json().get("detail", "").lower()


def test_list_scenarios_pagination_and_filter(client: TestClient) -> None:
    """Test pagination and type filtering on list endpoint."""
    for i in range(3):
        client.post("/api/v1/scenarios", json={
            "name": f"Shock {i}",
            "type": ScenarioType.MARKET_SHOCK.value,
            "parameters": {}
        })
    client.post("/api/v1/scenarios", json={
        "name": "Commodity Event",
        "type": ScenarioType.COMMODITY_FLUCTUATION.value,
        "parameters": {}
    })
    
    # Test pagination
    r = client.get("/api/v1/scenarios?skip=1&limit=2")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 4
    assert len(data["scenarios"]) == 2
    
    # Test filtering
    r = client.get(f"/api/v1/scenarios?type={ScenarioType.COMMODITY_FLUCTUATION.value}")
    data = r.json()
    assert data["total"] == 1
    assert data["scenarios"][0]["name"] == "Commodity Event"


def test_update_scenario(client: TestClient) -> None:
    """PUT /api/v1/scenarios/{id} updates the scenario."""
    r = client.post("/api/v1/scenarios", json={
        "name": "Original",
        "type": ScenarioType.MARKET_SHOCK.value,
        "parameters": {"x": 1}
    })
    scenario_id = r.json()["id"]
    
    r_put = client.put(f"/api/v1/scenarios/{scenario_id}", json={
        "name": "Updated",
        "parameters": {"x": 2}, # type cannot be updated per schema
        "status": "active"
    })
    assert r_put.status_code == 200
    assert r_put.json()["name"] == "Updated"
    assert r_put.json()["parameters"]["x"] == 2
    assert r_put.json()["status"] == "active"


def test_update_scenario_not_found(client: TestClient) -> None:
    """PUT /api/v1/scenarios/{id} returns 404 when scenario does not exist."""
    r = client.put("/api/v1/scenarios/nonexistent-id", json={"name": "Updated"})
    assert r.status_code == 404
    assert "not found" in r.json().get("detail", "").lower()


def test_delete_scenario(client: TestClient) -> None:
    """DELETE /api/v1/scenarios/{id} removes the scenario."""
    r = client.post("/api/v1/scenarios", json={
        "name": "To Delete",
        "type": ScenarioType.MARKET_SHOCK.value,
        "parameters": {}
    })
    scenario_id = r.json()["id"]
    
    r_del = client.delete(f"/api/v1/scenarios/{scenario_id}")
    assert r_del.status_code == 204
    
    r_get = client.get(f"/api/v1/scenarios/{scenario_id}")
    assert r_get.status_code == 404


def test_delete_scenario_not_found(client: TestClient) -> None:
    """DELETE /api/v1/scenarios/{id} returns 404 when scenario does not exist."""
    r = client.delete("/api/v1/scenarios/nonexistent-id")
    assert r.status_code == 404
    assert "not found" in r.json().get("detail", "").lower()


def test_get_scenario_templates(client: TestClient) -> None:
    """GET /api/v1/scenarios/templates retrieves the scenario templates."""
    r = client.get("/api/v1/scenarios/templates")
    assert r.status_code == 200
    templates = r.json()
    assert isinstance(templates, list)
    assert len(templates) >= 3
    
    # Check shape of a template
    t1 = templates[0]
    assert "id" in t1
    assert "name" in t1
    assert "description" in t1
    assert "type" in t1
    assert "parameters" in t1


def test_create_scenario_from_template_success(client: TestClient) -> None:
    """POST /api/v1/scenarios/from-template creates a new scenario using overrides."""
    payload = {
        "template_id": "tpl_market_crash",
        "name": "Custom Crash Test",
        "parameters": {
            "market_decline_percentage": 90.0
        }
    }
    r = client.post("/api/v1/scenarios/from-template", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["name"] == "Custom Crash Test"
    assert data["type"] == ScenarioType.MARKET_SHOCK.value
    assert data["parameters"]["market_decline_percentage"] == 90.0
    # Overridden
    assert data["parameters"]["duration_days"] == 30 
    # Persisted from template


def test_create_scenario_from_template_not_found(client: TestClient) -> None:
    """POST /api/v1/scenarios/from-template returns 404 for invalid template mapping."""
    payload = {
        "template_id": "tpl_nonexistent_fake",
        "name": "Should Fail"
    }
    r = client.post("/api/v1/scenarios/from-template", json=payload)
    assert r.status_code == 404
    assert "not found" in r.json().get("detail", "").lower()
