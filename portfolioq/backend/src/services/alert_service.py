"""Alert creation, retrieval and notification service."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.config.constants import AlertSeverity, RiskLevel, RISK_SCORE_THRESHOLDS
from src.models.alert import Alert

logger = logging.getLogger(__name__)


def create_alert(
    db: Session,
    severity: str,
    title: str,
    message: str,
    portfolio_id: str | None = None,
    scenario_id: str | None = None,
    run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Alert:
    """Create and persist an alert."""
    alert = Alert(
        id=str(uuid.uuid4()),
        severity=severity,
        title=title,
        message=message,
        portfolio_id=portfolio_id,
        scenario_id=scenario_id,
        run_id=run_id,
        metadata_=metadata,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info("Alert created: [%s] %s", severity.upper(), title)
    return alert


def evaluate_and_create_alerts(
    db: Session,
    portfolio_id: str,
    scenario: dict[str, Any],
    exposure_result: dict[str, Any],
    risk_result: dict[str, Any],
    run_id: str,
) -> list[Alert]:
    """Evaluate risk results and create appropriate alerts."""
    created: list[Alert] = []
    scenario_id = scenario.get("id")
    risk_level = risk_result.get("risk_level", "low")
    risk_score = float(risk_result.get("risk_score", 0))
    pl_impact = float(risk_result.get("pl_impact", 0) or 0)
    pl_pct = float(risk_result.get("pl_impact_pct", 0) or 0)

    # Portfolio-level risk alert
    if risk_level == RiskLevel.CRITICAL.value:
        a = create_alert(
            db, AlertSeverity.CRITICAL.value,
            f"CRITICAL Risk: {scenario.get('name')}",
            f"Portfolio faces CRITICAL risk (score={risk_score:.2f}) under {scenario.get('name')}. "
            f"Estimated P&L impact: ${pl_impact:,.0f} ({pl_pct:.2f}%). Immediate action required.",
            portfolio_id=portfolio_id, scenario_id=scenario_id, run_id=run_id,
            metadata={"risk_score": risk_score, "pl_impact": pl_impact},
        )
        created.append(a)
    elif risk_level == RiskLevel.HIGH.value:
        a = create_alert(
            db, AlertSeverity.WARNING.value,
            f"High Risk: {scenario.get('name')}",
            f"Portfolio faces HIGH risk (score={risk_score:.2f}). "
            f"P&L impact: ${pl_impact:,.0f} ({pl_pct:.2f}%). Review recommended.",
            portfolio_id=portfolio_id, scenario_id=scenario_id, run_id=run_id,
            metadata={"risk_score": risk_score, "pl_impact": pl_impact},
        )
        created.append(a)

    # Sector concentration alert
    sectors = exposure_result.get("sector_exposures", [])
    for sec in sectors:
        if sec.get("exposure_pct", 0) > 0.40:
            a = create_alert(
                db, AlertSeverity.WARNING.value,
                f"Sector Concentration: {sec['sector']}",
                f"Sector '{sec['sector']}' represents {sec['exposure_pct']:.1%} of portfolio — above 40% threshold.",
                portfolio_id=portfolio_id, scenario_id=scenario_id, run_id=run_id,
                metadata={"sector": sec["sector"], "exposure_pct": sec["exposure_pct"]},
            )
            created.append(a)

    # Large P&L impact alert
    if abs(pl_pct) > 10.0:
        sev = AlertSeverity.CRITICAL.value if abs(pl_pct) > 20.0 else AlertSeverity.WARNING.value
        a = create_alert(
            db, sev,
            f"Large P&L Impact: {abs(pl_pct):.1f}%",
            f"Scenario '{scenario.get('name')}' could impact portfolio P&L by ${pl_impact:,.0f} ({pl_pct:.2f}%).",
            portfolio_id=portfolio_id, scenario_id=scenario_id, run_id=run_id,
            metadata={"pl_impact": pl_impact, "pl_pct": pl_pct},
        )
        created.append(a)

    # Top individual holdings
    for h in (risk_result.get("prioritized_holdings") or [])[:3]:
        if h.get("risk_level") in ["critical", "high"] and h.get("signal") in ["sell", "reduce"]:
            a = create_alert(
                db, AlertSeverity.WARNING.value,
                f"High Risk Holding: {h.get('symbol')}",
                f"{h.get('symbol')} has {h.get('risk_level','').upper()} risk (signal: {h.get('signal','')}) "
                f"under {scenario.get('name')}. P&L impact: ${h.get('scenario_pl_impact', 0):,.0f}.",
                portfolio_id=portfolio_id, scenario_id=scenario_id, run_id=run_id,
                metadata={"symbol": h.get("symbol"), "risk_score": h.get("risk_score")},
            )
            created.append(a)

    if not created:
        a = create_alert(
            db, AlertSeverity.INFO.value,
            f"Scenario Analysis Complete: {scenario.get('name')}",
            f"Analysis completed. Risk level: {risk_level.upper()}, score={risk_score:.2f}.",
            portfolio_id=portfolio_id, scenario_id=scenario_id, run_id=run_id,
        )
        created.append(a)

    return created


def list_alerts(db: Session, portfolio_id: str | None = None, unread_only: bool = False) -> list[Alert]:
    q = db.query(Alert)
    if portfolio_id:
        q = q.filter(Alert.portfolio_id == portfolio_id)
    if unread_only:
        q = q.filter(Alert.read == False)  # noqa: E712
    return q.order_by(Alert.created_at.desc()).all()


def mark_alert_read(db: Session, alert_id: str) -> Alert | None:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.read = True
        db.commit()
        db.refresh(alert)
    return alert
