"""API v1 router."""
from fastapi import APIRouter
from .endpoints import portfolios, scenarios, exposure, reports, alerts, websockets

# Create API router
api_router = APIRouter(prefix="/api/v1", tags=["api"])


@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "PortfolioQ API v1",
        "version": "1.0.0",
    }


# Include endpoint routers
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(exposure.router, prefix="/exposure", tags=["exposure"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])
