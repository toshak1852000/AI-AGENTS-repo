"""Alert threshold monitoring Celery tasks."""
import logging
from src.tasks.celery_tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.alert_tasks.check_alert_thresholds", bind=True, max_retries=2)
def check_alert_thresholds(self):
    """Periodically check for new threshold breaches and create alerts."""
    from src.core.database import SessionLocal
    from src.models.exposure import RiskScore
    from src.models.portfolio import Portfolio
    from src.services.alert_service import create_alert
    from src.config.constants import AlertSeverity, RiskLevel

    db = SessionLocal()
    alerts_created = 0
    try:
        # Find portfolios with latest critical or high risk scores
        portfolios = db.query(Portfolio).all()
        for port in portfolios:
            latest_score = (
                db.query(RiskScore)
                .filter(RiskScore.portfolio_id == port.id)
                .order_by(RiskScore.created_at.desc())
                .first()
            )
            if not latest_score:
                continue
            score = float(latest_score.score or 0)
            level = latest_score.risk_level or "low"
            if level == RiskLevel.CRITICAL.value and score >= 0.8:
                create_alert(
                    db, AlertSeverity.CRITICAL.value,
                    f"Critical Risk Monitor: {port.name}",
                    f"Portfolio '{port.name}' has CRITICAL risk score of {score:.2f}. "
                    f"Immediate review required.",
                    portfolio_id=port.id,
                )
                alerts_created += 1

        return {"alerts_created": alerts_created}
    except Exception as exc:
        logger.error("check_alert_thresholds failed: %s", exc)
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()
