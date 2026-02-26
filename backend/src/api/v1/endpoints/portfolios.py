"""Portfolio endpoints: list (pagination, filters), get by id, create, update, delete."""
from fastapi import APIRouter, HTTPException, Query

from src.schemas.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioListResponse,
)
from src.services import portfolio_service as svc

router = APIRouter()


@router.get(
    "/",
    response_model=PortfolioListResponse,
    summary="List portfolios",
    description="List portfolios with optional pagination and name filter.",
)
async def list_portfolios(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    name: str | None = Query(None, description="Filter by name (substring, case-insensitive)"),
):
    """List all portfolios. Supports pagination (skip, limit) and optional name filter."""
    portfolios, total = svc.list_portfolios(skip=skip, limit=limit, name=name)
    return PortfolioListResponse(total=total, skip=skip, limit=limit, portfolios=portfolios)


@router.get(
    "/{portfolio_id}",
    response_model=Portfolio,
    summary="Get portfolio by ID",
    responses={404: {"description": "Portfolio not found"}},
)
async def get_portfolio(portfolio_id: str):
    """Get a portfolio by ID. Returns 404 when not found."""
    portfolio = svc.get_portfolio(portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.post(
    "/",
    response_model=Portfolio,
    status_code=201,
    summary="Create portfolio",
    responses={400: {"description": "Validation error"}},
)
async def create_portfolio(payload: PortfolioCreate):
    """Create a new portfolio. Request body is validated; invalid input returns 400."""
    portfolio = svc.create_portfolio(payload)
    return portfolio


@router.put(
    "/{portfolio_id}",
    response_model=Portfolio,
    summary="Update portfolio",
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Portfolio not found"},
    },
)
async def update_portfolio(portfolio_id: str, payload: PortfolioUpdate):
    """Update a portfolio. Returns 404 if portfolio does not exist; 400 on validation error."""
    portfolio = svc.update_portfolio(portfolio_id, payload)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.delete(
    "/{portfolio_id}",
    status_code=204,
    summary="Delete portfolio",
    responses={
        404: {"description": "Portfolio not found"},
        409: {
            "description": "Portfolio has holdings; remove or transfer holdings before deleting. See API docs.",
        },
    },
)
async def delete_portfolio(portfolio_id: str):
    """
    Delete a portfolio by ID.

    **Behavior when portfolio has holdings:**  
    Returns **409 Conflict**. You must remove all holdings (or transfer them) before deleting the portfolio.  
    This avoids accidental data loss. Alternative behavior (cascade delete) can be added later if required.
    """
    found, had_holdings = svc.delete_portfolio(portfolio_id)
    if not found:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if had_holdings:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete portfolio with holdings. Remove or transfer holdings first.",
        )
    # 204 No Content: no body
    return None
