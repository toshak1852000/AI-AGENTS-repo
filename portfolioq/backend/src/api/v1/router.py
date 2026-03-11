"""API v1 router — registers all endpoint groups."""
from fastapi import APIRouter
from src.api.v1.endpoints import portfolios, scenarios, exposure, reports, alerts, ml

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(exposure.router, prefix="/exposure", tags=["exposure"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
