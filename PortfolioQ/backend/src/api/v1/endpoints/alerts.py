"""Alert endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.services.alert_service import list_alerts, mark_alert_read

router = APIRouter()


@router.get("/")
def get_alerts(
    portfolio_id: Optional[str] = None,
    unread_only: bool = False,
    db: Session = Depends(get_db),
):
    alerts = list_alerts(db, portfolio_id=portfolio_id, unread_only=unread_only)
    return [
        {
            "id": a.id, "severity": a.severity, "title": a.title, "message": a.message,
            "portfolio_id": a.portfolio_id, "scenario_id": a.scenario_id,
            "run_id": a.run_id, "read": a.read, "metadata": a.metadata_,
            "created_at": a.created_at,
        }
        for a in alerts
    ]


@router.get("/{alert_id}")
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    from src.models.alert import Alert
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": a.id, "severity": a.severity, "title": a.title, "message": a.message,
        "portfolio_id": a.portfolio_id, "scenario_id": a.scenario_id,
        "run_id": a.run_id, "read": a.read, "metadata": a.metadata_,
        "created_at": a.created_at,
    }


@router.put("/{alert_id}/read")
def read_alert(alert_id: str, db: Session = Depends(get_db)):
    a = mark_alert_read(db, alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"id": a.id, "read": a.read}


@router.get("/summary/counts")
def alert_summary(db: Session = Depends(get_db)):
    from src.models.alert import Alert
    from src.analytics.metrics import ALERTS_UNREAD
    total = db.query(Alert).count()
    unread = db.query(Alert).filter(Alert.read == False).count()  # noqa: E712
    critical = db.query(Alert).filter(Alert.severity == "critical", Alert.read == False).count()  # noqa: E712
    ALERTS_UNREAD.set(unread)
    return {"total": total, "unread": unread, "critical_unread": critical}
