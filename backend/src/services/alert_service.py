"""Mock alert service for development."""
import uuid
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from src.schemas.alert import Alert, AlertCreate, AlertUpdate

# In-memory storage: mapping from alert_id to Alert instance
_alerts: dict[str, Alert] = {}

def list_alerts(
    skip: int = 0,
    limit: int = 20,
    severity: Optional[str] = None,
    unread_only: bool = False
) -> Tuple[List[Alert], int]:
    """
    List alerts with optional filtering and pagination.
    Returns (filtered_alerts, total_count).
    """
    filtered = list(_alerts.values())

    # Apply filters
    if severity:
        severity = severity.lower()
        filtered = [a for a in filtered if a.severity == severity]
        
    if unread_only:
        filtered = [a for a in filtered if not a.read]

    # Sort descending by creation date
    filtered.sort(key=lambda a: a.created_at, reverse=True)

    total = len(filtered)
    # Apply pagination
    paginated = filtered[skip : skip + limit]
    
    return paginated, total


def get_alert(alert_id: str) -> Optional[Alert]:
    """Get a single alert by its ID."""
    return _alerts.get(alert_id)


def create_alert(payload: AlertCreate) -> Alert:
    """Create and store a new alert."""
    alert_id = f"alert_{uuid.uuid4().hex[:8]}"
    alert = Alert(
        id=alert_id,
        created_at=datetime.now(timezone.utc),
        read=False,
        **payload.model_dump()
    )
    _alerts[alert_id] = alert
    return alert


def update_alert(alert_id: str, payload: AlertUpdate) -> Optional[Alert]:
    """Update an alert's properties (like marking it read)."""
    alert = _alerts.get(alert_id)
    if not alert:
        return None
        
    update_data = payload.model_dump(exclude_unset=True)
    
    if "read" in update_data:
        alert.read = update_data["read"]
        
    return alert


def mark_alert_read(alert_id: str) -> Optional[Alert]:
    """Convenience shortcut to mark an alert as read / dismissed."""
    return update_alert(alert_id, AlertUpdate(read=True))


# Seed with some dummy alerts for testing UI/API behavior immediately
create_alert(AlertCreate(
    severity="info",
    title="System initialized",
    message="PortfolioQ platform is online and ready.",
    channel="system"
))
create_alert(AlertCreate(
    severity="warning",
    title="High Market Volatility",
    message="VIX index has spiked above 25. Consider reviewing high-beta portfolios.",
    channel="market"
))
create_alert(AlertCreate(
    severity="critical",
    title="Data Feed Disconnected",
    message="Lost connection to primary Bloomberg API stream. Retrying connection...",
    channel="system"
))
