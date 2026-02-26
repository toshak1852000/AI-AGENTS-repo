"""FastAPI application entry point."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="PortfolioQ API",
    description="Autonomous Market & Portfolio Scenario Analyst API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PortfolioQ API",
        "version": "0.1.0",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Load fake market data at startup if configured (for local/dev)
_fake_csv = os.environ.get("FAKE_MARKET_DATA_CSV")
if _fake_csv and Path(_fake_csv).is_file():
    from src.services import market_data_fake_store as _fake_store
    _fake_store.load_from_csv(_fake_csv)

# Import and include API routers
from src.api.v1.router import api_router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.debug,
    )
