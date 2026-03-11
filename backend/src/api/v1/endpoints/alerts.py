"""Alert endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import uuid
import datetime

from src.schemas.alert import Alert, AlertListResponse, AlertUpdate
from src.services import alert_service as svc
from src.services.websocket_manager import manager

router = APIRouter()


@router.get(
    "/",
    response_model=AlertListResponse,
    summary="List alerts",
    description="List all alerts with optional pagination, severity filtering, and unread toggles."
)
async def list_alerts(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, critical)"),
    unread_only: bool = Query(False, description="If true, only returns unread alerts")
):
    """List alerts according to filters."""
    alerts, total = svc.list_alerts(skip=skip, limit=limit, severity=severity, unread_only=unread_only)
    return AlertListResponse(total=total, skip=skip, limit=limit, alerts=alerts)


@router.get(
    "/{alert_id}",
    response_model=Alert,
    summary="Get alert by ID",
    responses={404: {"description": "Alert not found"}}
)
async def get_alert(alert_id: str):
    """Get an alert by ID."""
    alert = svc.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch(
    "/{alert_id}",
    response_model=Alert,
    summary="Update alert (read/dismiss)",
    responses={404: {"description": "Alert not found"}}
)
async def update_alert(alert_id: str, payload: AlertUpdate):
    """Update an alert, primarily used right now to mark it as read=True (dismissed)."""
    alert = svc.update_alert(alert_id, payload)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


class DummyAlert(BaseModel):
    title: str
    message: str
    severity: str = "info"
    channel: str = "system"

@router.post(
    "/trigger_dummy",
    summary="Trigger dummy websocket push",
    description="For testing live websocket broadcasts"
)
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
