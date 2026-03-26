"""Market data Celery tasks."""
import logging
import time

from src.tasks.celery_tasks import celery_app

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "JPM",
    "JNJ", "XOM", "V", "PG", "UNH", "HD", "BAC", "MA",
    "CVX", "LLY", "PFE", "SPY", "QQQ",
]


@celery_app.task(name="src.tasks.market_data_tasks.refresh_all_prices", bind=True, max_retries=3)
def refresh_all_prices(self):
    """Fetch and cache latest prices for all tracked symbols."""
    from src.core.database import SessionLocal
    from src.models.portfolio import Holding
    from src.integrations.yahoo_finance import fetch_current_price
    from src.analytics.metrics import MARKET_DATA_FETCH_DURATION, MARKET_DATA_FETCH_TOTAL

    db = SessionLocal()
    updated = 0
    failed = 0
    try:
        holdings = db.query(Holding).all()
        symbols = list({h.symbol for h in holdings} | set(DEFAULT_SYMBOLS))

        for sym in symbols:
            try:
                t0 = time.perf_counter()
                price = fetch_current_price(sym)
                MARKET_DATA_FETCH_DURATION.labels(provider="yfinance").observe(time.perf_counter() - t0)
                if price:
                    for h in [h for h in holdings if h.symbol == sym]:
                        h.current_price = price
                    updated += 1
                    MARKET_DATA_FETCH_TOTAL.labels(provider="yfinance", status="success").inc()
            except Exception as exc:
                failed += 1
                MARKET_DATA_FETCH_TOTAL.labels(provider="yfinance", status="error").inc()
                logger.warning("Failed to refresh %s: %s", sym, exc)

        db.commit()
        logger.info("Prices refreshed: %d updated, %d failed", updated, failed)
        return {"updated": updated, "failed": failed, "symbols": len(symbols)}
    except Exception as exc:
        db.rollback()
        logger.error("refresh_all_prices failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
    finally:
        from src.analytics.pushgateway import push_worker_metrics

        push_worker_metrics()
        db.close()
