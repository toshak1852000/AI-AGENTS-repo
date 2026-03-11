"""Tests for WebSocket alerts endpoint."""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_websocket_no_auth():
    """Test connecting without a token fails."""
    # TestClient context manager for websockets
    try:
        with client.websocket_connect("/api/v1/ws/alerts") as _websocket:
            # Should raise WebSocketDisconnect due to 1008 policy violation
            pass
        assert False, "Should have disconnected"
    except Exception as e:
        # FastAPI's TestClient raises different disconnection exceptions based on Starlette version
        assert "1008" in str(e) or "violation" in str(e).lower() or type(e).__name__ == 'WebSocketDisconnect'


def test_websocket_invalid_auth():
    """Test connecting with invalid token fails."""
    try:
        with client.websocket_connect("/api/v1/ws/alerts?token=invalid_token") as _websocket:
            pass
        assert False, "Should have disconnected"
    except Exception as e:
        assert "1008" in str(e) or "violation" in str(e).lower() or type(e).__name__ == 'WebSocketDisconnect'


def test_websocket_broadcast():
    """Test connecting with valid auth and receiving a broadcasted alert."""
    # Connect standard valid token over "portfolio_123" channel
    with client.websocket_connect("/api/v1/ws/alerts?token=valid123&channel=portfolio_123") as websocket:
        
        # Trigger an alert dynamically via the REST dummy endpoint
        alert_payload = {
            "title": "Test Alert",
            "message": "This is a test broadcast",
            "severity": "high",
            "channel": "portfolio_123"
        }
        response = client.post("/api/v1/alerts/trigger_dummy", json=alert_payload)
        assert response.status_code == 200
        
        # Receive the websocket data that should have been concurrently broadcasted
        data = websocket.receive_json()
        assert data["title"] == "Test Alert"
        assert data["message"] == "This is a test broadcast"
        assert data["severity"] == "high"
        
def test_websocket_wrong_channel():
    """Test connecting to one channel doesn't receive messages from another."""
    with client.websocket_connect("/api/v1/ws/alerts?token=valid123&channel=system") as websocket:
        
        # Trigger alert on different channel
        alert_payload = {
            "title": "Other Channel Alert",
            "message": "Should not see this",
            "channel": "portfolio_123"
        }
        client.post("/api/v1/alerts/trigger_dummy", json=alert_payload)
        
        # We need a way to prove we didn't get it without hanging forever.
        # Since TestClient websocket receives are blocking, we can't easily timeout.
        # Instead, we send a ping-like message, then trigger another alert on OUR channel
        # and verify the FIRST thing we receive is the second alert.
        
        sys_alert = {
            "title": "System Alert",
            "message": "Should see this",
            "channel": "system"
        }
        client.post("/api/v1/alerts/trigger_dummy", json=sys_alert)
        
        data = websocket.receive_json()
        assert data["title"] == "System Alert"
