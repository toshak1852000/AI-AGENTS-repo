"""In-memory portfolio service. Replace with DB-backed service when database is available."""
from datetime import datetime, timezone
from typing import Optional
import uuid

from src.schemas.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioUpdate,
    Holding,
    HoldingCreate,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# In-memory stores (keyed by id)
_portfolios: dict[str, dict] = {}
_holdings_by_portfolio: dict[str, list[dict]] = {}  # portfolio_id -> list of holding dicts


def list_portfolios(
    skip: int = 0,
    limit: int = 20,
    name: Optional[str] = None,
) -> tuple[list[Portfolio], int]:
    """Return (portfolios slice, total count). Applies name filter if provided."""
    items = list(_portfolios.values())
    if name is not None and name.strip():
        name_lower = name.strip().lower()
        items = [p for p in items if name_lower in (p.get("name") or "").lower()]
    total = len(items)
    # Sort by created_at desc for stable pagination
    items.sort(key=lambda p: p["created_at"], reverse=True)
    slice_items = items[skip : skip + limit]
    portfolios = [
        Portfolio(
            id=p["id"],
            name=p["name"],
            description=p.get("description"),
            created_at=p["created_at"],
            updated_at=p.get("updated_at"),
        )
        for p in slice_items
    ]
    return portfolios, total


def get_portfolio(portfolio_id: str) -> Optional[Portfolio]:
    """Get a portfolio by ID or None if not found."""
    p = _portfolios.get(portfolio_id)
    if not p:
        return None
    return Portfolio(
        id=p["id"],
        name=p["name"],
        description=p.get("description"),
        created_at=p["created_at"],
        updated_at=p.get("updated_at"),
    )


def create_portfolio(payload: PortfolioCreate) -> Portfolio:
    """Create a new portfolio. Returns the created portfolio."""
    pid = str(uuid.uuid4())
    now = _now()
    _portfolios[pid] = {
        "id": pid,
        "name": payload.name,
        "description": payload.description,
        "created_at": now,
        "updated_at": None,
    }
    _holdings_by_portfolio[pid] = []
    return get_portfolio(pid)  # type: ignore


def update_portfolio(portfolio_id: str, payload: PortfolioUpdate) -> Optional[Portfolio]:
    """Update a portfolio. Returns updated portfolio or None if not found."""
    p = _portfolios.get(portfolio_id)
    if not p:
        return None
    now = _now()
    if payload.name is not None:
        p["name"] = payload.name
    if payload.description is not None:
        p["description"] = payload.description
    p["updated_at"] = now
    return get_portfolio(portfolio_id)


def delete_portfolio(portfolio_id: str) -> tuple[bool, bool]:
    """Delete a portfolio. Returns (found, had_holdings). If had_holdings, caller should not delete."""
    if portfolio_id not in _portfolios:
        return False, False
    holdings = _holdings_by_portfolio.get(portfolio_id, [])
    had_holdings = len(holdings) > 0
    if had_holdings:
        return True, True
    del _portfolios[portfolio_id]
    _holdings_by_portfolio.pop(portfolio_id, None)
    return True, False


def get_holdings_count(portfolio_id: str) -> int:
    """Return number of holdings for a portfolio."""
    return len(_holdings_by_portfolio.get(portfolio_id, []))


def clear_all() -> None:
    """Clear all in-memory data. For testing only."""
    _portfolios.clear()
    _holdings_by_portfolio.clear()


def add_holding(portfolio_id: str, payload: HoldingCreate) -> Optional[Holding]:
    """Add a holding to a portfolio. Returns Holding or None if portfolio not found."""
    if portfolio_id not in _portfolios:
        return None
    hid = str(uuid.uuid4())
    now = _now()
    h = {
        "id": hid,
        "portfolio_id": portfolio_id,
        "symbol": payload.symbol,
        "company_name": payload.company_name,
        "quantity": payload.quantity,
        "average_price": payload.average_price,
        "sector": payload.sector,
        "current_price": None,
        "created_at": now,
    }
    _holdings_by_portfolio.setdefault(portfolio_id, []).append(h)
    return Holding(
        id=hid,
        portfolio_id=portfolio_id,
        symbol=payload.symbol,
        company_name=payload.company_name,
        quantity=payload.quantity,
        average_price=payload.average_price,
        sector=payload.sector,
        current_price=None,
        created_at=now,
    )
