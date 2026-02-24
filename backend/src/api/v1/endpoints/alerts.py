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
