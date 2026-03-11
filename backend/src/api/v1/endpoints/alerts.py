"""Alert endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_alerts():
    """List all alerts."""
    # TODO: Implement alert listing
    return {"alerts": []}


@router.get("/{alert_id}")
async def get_alert(alert_id: str):
    """Get an alert by ID."""
    # TODO: Implement alert retrieval
    return {"id": alert_id}


@router.put("/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """Mark an alert as read."""
    # TODO: Implement alert marking
    return {"id": alert_id, "read": True}

from typing import Optional
from pydantic import BaseModel
from src.services.websocket_manager import manager
import uuid
import datetime

class DummyAlert(BaseModel):
    title: str
    message: str
    severity: str = "info"
    channel: str = "system"

@router.post("/trigger_dummy")
async def trigger_dummy_alert(alert: DummyAlert):
    """Trigger a dummy alert to push via websockets."""
    alert_resp = {
        "id": str(uuid.uuid4()),
        "title": alert.title,
        "message": alert.message,
        "severity": alert.severity,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    await manager.broadcast_alert(alert_resp, channel=alert.channel)
    return {"status": "success", "alert": alert_resp}
