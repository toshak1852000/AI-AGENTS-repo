"""FastAPI application entry point."""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse

from src.config.settings import settings
from src.analytics.metrics import (
    API_REQUEST_COUNT,
    API_REQUEST_DURATION,
    get_metrics_response,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create DB tables, train ML models, configure MLflow."""
    logger.info("PortfolioQ startup: initialising database tables...")
    try:
        from src.core.database import create_tables
        create_tables()
        logger.info("Database tables created/verified.")
    except Exception as exc:
        logger.error("DB init failed: %s", exc)

    logger.info("Initialising ML models...")
    try:
        from src.ml.mlflow_tracker import setup_mlflow
        from src.ml.training import train_all_models
        setup_mlflow()
        train_all_models(force_retrain=False)
        logger.info("ML models ready.")
    except Exception as exc:
        logger.error("ML model init failed: %s", exc)

    logger.info("PortfolioQ is ready.")
    yield
    logger.info("PortfolioQ shutting down.")


app = FastAPI(
    title="PortfolioQ API",
    description=(
        "Autonomous Market & Portfolio Scenario Analyst — "
        "Enterprise-grade scenario analysis, exposure scoring, risk assessment, "
        "ML-powered insights, and board-ready reports."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Record Prometheus metrics for every HTTP request."""
    start = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start
    endpoint = request.url.path
    API_REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code,
    ).inc()
    API_REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(duration)
    return response


@app.get("/")
async def root():
    return {
        "service": "PortfolioQ API",
        "version": "1.0.0",
        "description": "Autonomous Market & Portfolio Scenario Analyst",
        "docs": "/api/docs",
        "redoc": "/api/redoc",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    data, content_type = get_metrics_response()
    return StarletteResponse(content=data, media_type=content_type)


from src.api.v1.router import api_router  # noqa: E402
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.backend_port, reload=settings.debug)
