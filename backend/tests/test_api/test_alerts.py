"""Tests for Alerts API endpoints."""
import pytest
from fastapi.testclient import TestClient
from main import app

# Keep a reference to the service to easily wipe state between tests
from src.services import alert_service
from src.schemas.alert import AlertCreate

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_alerts_state():
    """Reset the in-memory alerts state before each test."""
    # We clear the global mock dictionary
    alert_service._alerts.clear()
    
    # Re-seed some standard test data
    alert_service.create_alert(AlertCreate(
        severity="info", title="Info 1", message="m1", channel="system"
    ))
    alert_service.create_alert(AlertCreate(
        severity="warning", title="Warn 1", message="m2", channel="system"
    ))
    alert_service.create_alert(AlertCreate(
        severity="critical", title="Crit 1", message="m3", channel="system"
    ))
    yield
    # Cleanup after test not strictly needed due to setup clear, but good practice


def test_list_alerts_default():
    """Test default listing returns all seeded alerts."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["alerts"]) == 3
    
    # Check that the three types of alerts are present 
    severities = {a["severity"] for a in data["alerts"]}
    assert severities == {"info", "warning", "critical"}


def test_list_alerts_filter_severity():
    """Test filtering alerts by severity."""
    response = client.get("/api/v1/alerts?severity=warning")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["severity"] == "warning"


def test_list_alerts_filter_unread():
    """Test filtering alerts by unread status."""
    # First, let's mark one as read
    all_alerts = client.get("/api/v1/alerts").json()["alerts"]
    alert_to_read = all_alerts[0]["id"]
    
    # Mark it
    client.patch(f"/api/v1/alerts/{alert_to_read}", json={"read": True})
    
    # Now filter by unread = True
    response = client.get("/api/v1/alerts?unread_only=true")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2
    assert len(data["alerts"]) == 2
    for a in data["alerts"]:
        assert a["read"] is False


def test_list_alerts_pagination():
    """Test skip and limit parameters."""
    response = client.get("/api/v1/alerts?skip=1&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # Total should remain the same across DB
    assert len(data["alerts"]) == 1
    assert data["skip"] == 1
    assert data["limit"] == 1


def test_get_alert_by_id():
    """Test fetching a specific alert."""
    # Grab an ID first
    all_alerts = client.get("/api/v1/alerts").json()["alerts"]
    target_id = all_alerts[0]["id"]
    
    response = client.get(f"/api/v1/alerts/{target_id}")
    assert response.status_code == 200
    assert response.json()["id"] == target_id


def test_get_alert_not_found():
    """Test 404 response for missing alert."""
    response = client.get("/api/v1/alerts/invalid_id_999")
    assert response.status_code == 404


def test_update_alert_read():
    """Test marking an alert as read / dismissed."""
    all_alerts = client.get("/api/v1/alerts").json()["alerts"]
    target_id = all_alerts[0]["id"]
    
    # Verify unread initially
    assert all_alerts[0]["read"] is False
    
    # Patch it
    response = client.patch(f"/api/v1/alerts/{target_id}", json={"read": True})
    assert response.status_code == 200
    assert response.json()["read"] is True
    
    # Verify it persisted
    get_resp = client.get(f"/api/v1/alerts/{target_id}")
    assert get_resp.json()["read"] is True


def test_update_alert_not_found():
    """Test marking a non-existent alert read returns 404."""
    response = client.patch("/api/v1/alerts/invalid_id_999", json={"read": True})
    assert response.status_code == 404
