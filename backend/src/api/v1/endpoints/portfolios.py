"""Portfolio endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_portfolios():
    """List all portfolios."""
    # TODO: Implement portfolio listing
    return {"portfolios": []}


@router.get("/{portfolio_id}")
async def get_portfolio(portfolio_id: str):
    """Get a portfolio by ID."""
    # TODO: Implement portfolio retrieval
    return {"id": portfolio_id}


@router.post("/")
async def create_portfolio():
    """Create a new portfolio."""
    # TODO: Implement portfolio creation
    return {"message": "Portfolio creation not yet implemented"}


@router.put("/{portfolio_id}")
async def update_portfolio(portfolio_id: str):
    """Update a portfolio."""
    # TODO: Implement portfolio update
    return {"id": portfolio_id}


@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """Delete a portfolio."""
    # TODO: Implement portfolio deletion
    return {"message": "Portfolio deletion not yet implemented"}
