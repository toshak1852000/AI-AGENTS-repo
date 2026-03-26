"""Push Prometheus metrics from Celery workers to Pushgateway.

The FastAPI process exposes /metrics; Celery runs in separate processes, so their
default registry is never scraped unless we push to Pushgateway (see Prometheus docs).
"""
from __future__ import annotations

import logging
import os
import socket

logger = logging.getLogger(__name__)


def push_worker_metrics() -> None:
    """Push the process registry to Pushgateway (no-op if PROMETHEUS_PUSHGATEWAY unset)."""
    gateway = (os.getenv("PROMETHEUS_PUSHGATEWAY") or "").strip()
    if not gateway:
        return
    try:
        from prometheus_client import REGISTRY, push_to_gateway

        # Unique per worker process so concurrent Celery workers do not overwrite each other
        instance = f"{os.getenv('HOSTNAME', socket.gethostname())}-{os.getpid()}"
        push_to_gateway(
            gateway,
            job="celery_worker",
            registry=REGISTRY,
            grouping_key={"instance": instance},
        )
    except Exception as exc:
        logger.warning("Prometheus pushgateway push failed (metrics still in-process): %s", exc)
