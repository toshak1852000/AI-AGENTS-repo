"""Portfolio endpoints: list (pagination, filters), get by id, create, update, delete."""
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from src.schemas.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioListResponse,
    Holding,
    HoldingCreate,
    HoldingUpdate,
    HoldingListResponse,
    PortfolioWithHoldings,
    PortfolioVersionInfo,
)
from src.services import portfolio_service as svc
from src.services import portfolio_export_import as export_import

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


@router.post(
    "/import",
    summary="Import portfolio from CSV or Excel",
    description="Upload a CSV or Excel file. Creates portfolio and holdings. Returns portfolio_id, holdings_created, and errors.",
    responses={400: {"description": "Invalid file or validation errors"}},
)
async def import_portfolio(file: UploadFile = File(...)):
    """Import portfolio and holdings from CSV or Excel. Returns success count and error report."""
    content = await file.read()
    filename = (file.filename or "").lower()
    if filename.endswith(".csv"):
        result = export_import.import_portfolio_csv(content)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        result = export_import.import_portfolio_excel(content)
    else:
        raise HTTPException(
            status_code=400,
            detail="File must be CSV (.csv) or Excel (.xlsx)",
        )
    return result


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


# ---- Export ----

@router.get(
    "/{portfolio_id}/export",
    summary="Export portfolio to CSV or Excel",
    description="Download portfolio and holdings as CSV or Excel (xlsx).",
    responses={404: {"description": "Portfolio not found"}},
)
async def export_portfolio(
    portfolio_id: str,
    format: str = Query("csv", description="Export format: csv or xlsx"),
):
    """Export portfolio and holdings. Returns file with appropriate content-type."""
    if format.lower() == "csv":
        content = export_import.export_portfolio_csv(portfolio_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return Response(
            content=content.encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="portfolio_{portfolio_id}.csv"'},
        )
    if format.lower() in ("xlsx", "excel"):
        content = export_import.export_portfolio_excel(portfolio_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="portfolio_{portfolio_id}.xlsx"'},
        )
    raise HTTPException(status_code=400, detail="format must be csv or xlsx")


# ---- Holdings (nested under /api/v1/portfolios/{portfolio_id}/holdings) ----

@router.get(
    "/{portfolio_id}/holdings",
    response_model=HoldingListResponse,
    summary="List holdings",
    description="List holdings for a portfolio with pagination.",
    responses={404: {"description": "Portfolio not found"}},
)
async def list_holdings(
    portfolio_id: str,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
):
    """List holdings for a portfolio. Returns 404 when portfolio not found."""
    result = svc.list_holdings(portfolio_id, skip=skip, limit=limit)
    if result is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    holdings, total = result
    return HoldingListResponse(total=total, skip=skip, limit=limit, holdings=holdings)


@router.get(
    "/{portfolio_id}/holdings/{holding_id}",
    response_model=Holding,
    summary="Get holding by ID",
    responses={404: {"description": "Portfolio or holding not found"}},
)
async def get_holding(portfolio_id: str, holding_id: str):
    """Get a holding by ID. Returns 404 when portfolio or holding not found."""
    holding = svc.get_holding(portfolio_id, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Portfolio or holding not found")
    return holding


@router.post(
    "/{portfolio_id}/holdings",
    response_model=Holding,
    status_code=201,
    summary="Add holding",
    responses={400: {"description": "Validation error"}, 404: {"description": "Portfolio not found"}},
)
async def create_holding(portfolio_id: str, payload: HoldingCreate):
    """Add a holding to a portfolio. Returns 404 when portfolio not found."""
    holding = svc.add_holding(portfolio_id, payload)
    if holding is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return holding


@router.put(
    "/{portfolio_id}/holdings/{holding_id}",
    response_model=Holding,
    summary="Update holding",
    responses={
        400: {"description": "Validation error"},
        404: {"description": "Portfolio or holding not found"},
    },
)
async def update_holding(portfolio_id: str, holding_id: str, payload: HoldingUpdate):
    """Update a holding. Returns 404 when portfolio or holding not found."""
    holding = svc.update_holding(portfolio_id, holding_id, payload)
    if holding is None:
        raise HTTPException(status_code=404, detail="Portfolio or holding not found")
    return holding


@router.delete(
    "/{portfolio_id}/holdings/{holding_id}",
    status_code=204,
    summary="Delete holding",
    responses={404: {"description": "Portfolio or holding not found"}},
)
async def delete_holding(portfolio_id: str, holding_id: str):
    """Delete a holding. Returns 404 when portfolio or holding not found."""
    deleted = svc.delete_holding(portfolio_id, holding_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Portfolio or holding not found")
    return None


# ---- Portfolio version history ----

@router.get(
    "/{portfolio_id}/versions",
    response_model=list[PortfolioVersionInfo],
    summary="List portfolio versions",
    description="List version history for a portfolio (newest first). Versions are created on each portfolio update.",
    responses={404: {"description": "Portfolio not found"}},
)
async def list_portfolio_versions(portfolio_id: str):
    """List version history. Returns 404 when portfolio not found."""
    versions = svc.list_versions(portfolio_id)
    if versions is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return versions


@router.get(
    "/{portfolio_id}/versions/{version_id}",
    response_model=PortfolioWithHoldings,
    summary="Get portfolio by version",
    description="Get portfolio and holdings snapshot at a given version.",
    responses={404: {"description": "Portfolio or version not found"}},
)
async def get_portfolio_by_version(portfolio_id: str, version_id: str):
    """Get snapshot at version. Returns 404 when portfolio or version not found."""
    snapshot = svc.get_portfolio_by_version(portfolio_id, version_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Portfolio or version not found")
    return snapshot
