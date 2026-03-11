"""In-memory portfolio service. Replace with DB-backed service when database is available."""
import copy
from datetime import datetime, timezone
from typing import Optional
import uuid

from src.schemas.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioUpdate,
    Holding,
    HoldingCreate,
    HoldingUpdate,
    PortfolioWithHoldings,
    PortfolioVersionInfo,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# In-memory stores (keyed by id)
_portfolios: dict[str, dict] = {}
_holdings_by_portfolio: dict[str, list[dict]] = {}  # portfolio_id -> list of holding dicts
# Version snapshots: portfolio_id -> list of { "id", "created_at", "portfolio": {...}, "holdings": [...] }
_version_snapshots: dict[str, list[dict]] = {}


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
    """Update a portfolio. Returns updated portfolio or None if not found. Creates a version snapshot on update."""
    p = _portfolios.get(portfolio_id)
    if not p:
        return None
    now = _now()
    if payload.name is not None:
        p["name"] = payload.name
    if payload.description is not None:
        p["description"] = payload.description
    p["updated_at"] = now
    _create_version_snapshot(portfolio_id)
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
    _version_snapshots.pop(portfolio_id, None)
    return True, False


def get_holdings_count(portfolio_id: str) -> int:
    """Return number of holdings for a portfolio."""
    return len(_holdings_by_portfolio.get(portfolio_id, []))


def list_holdings(
    portfolio_id: str,
    skip: int = 0,
    limit: int = 20,
) -> Optional[tuple[list[Holding], int]]:
    """Return (holdings slice, total count) or None if portfolio not found."""
    if portfolio_id not in _portfolios:
        return None
    items = list(_holdings_by_portfolio.get(portfolio_id, []))
    total = len(items)
    items.sort(key=lambda h: h.get("created_at", ""), reverse=True)
    slice_items = items[skip : skip + limit]
    holdings = [
        _holding_from_dict(h, portfolio_id)
        for h in slice_items
    ]
    return holdings, total


def get_holding(portfolio_id: str, holding_id: str) -> Optional[Holding]:
    """Get a holding by ID. Returns None if portfolio or holding not found."""
    if portfolio_id not in _portfolios:
        return None
    for h in _holdings_by_portfolio.get(portfolio_id, []):
        if h.get("id") == holding_id:
            return _holding_from_dict(h, portfolio_id)
    return None


def _holding_from_dict(h: dict, portfolio_id: str) -> Holding:
    return Holding(
        id=h["id"],
        portfolio_id=portfolio_id,
        symbol=h["symbol"],
        company_name=h["company_name"],
        quantity=h["quantity"],
        average_price=h["average_price"],
        sector=h.get("sector"),
        current_price=h.get("current_price"),
        created_at=h["created_at"],
    )


def update_holding(
    portfolio_id: str,
    holding_id: str,
    payload: HoldingUpdate,
) -> Optional[Holding]:
    """Update a holding. Returns updated Holding or None if portfolio/holding not found."""
    if portfolio_id not in _portfolios:
        return None
    for h in _holdings_by_portfolio.get(portfolio_id, []):
        if h.get("id") == holding_id:
            if payload.quantity is not None:
                h["quantity"] = payload.quantity
            if payload.average_price is not None:
                h["average_price"] = payload.average_price
            if payload.current_price is not None:
                h["current_price"] = payload.current_price
            return _holding_from_dict(h, portfolio_id)
    return None


def delete_holding(portfolio_id: str, holding_id: str) -> bool:
    """Delete a holding. Returns True if deleted, False if portfolio or holding not found."""
    if portfolio_id not in _portfolios:
        return False
    lst = _holdings_by_portfolio.get(portfolio_id, [])
    for i, h in enumerate(lst):
        if h.get("id") == holding_id:
            lst.pop(i)
            return True
    return False


def _create_version_snapshot(portfolio_id: str) -> None:
    """Create a version snapshot of current portfolio and holdings (deep copy)."""
    if portfolio_id not in _portfolios:
        return
    p = _portfolios[portfolio_id]
    holdings = _holdings_by_portfolio.get(portfolio_id, [])
    vid = str(uuid.uuid4())
    now = _now()
    snapshot = {
        "id": vid,
        "created_at": now,
        "portfolio": copy.deepcopy(p),
        "holdings": copy.deepcopy(holdings),
    }
    _version_snapshots.setdefault(portfolio_id, []).append(snapshot)


def list_versions(portfolio_id: str) -> Optional[list[PortfolioVersionInfo]]:
    """List version history for a portfolio (newest first). Returns None if portfolio not found."""
    if portfolio_id not in _portfolios:
        return None
    snapshots = _version_snapshots.get(portfolio_id, [])
    # Newest first
    sorted_snapshots = sorted(snapshots, key=lambda s: s["created_at"], reverse=True)
    return [
        PortfolioVersionInfo(
            id=s["id"],
            created_at=s["created_at"],
            portfolio_name=s["portfolio"].get("name", ""),
        )
        for s in sorted_snapshots
    ]


def get_portfolio_by_version(
    portfolio_id: str,
    version_id: str,
) -> Optional[PortfolioWithHoldings]:
    """Get portfolio and holdings snapshot at a given version. Returns None if not found."""
    if portfolio_id not in _portfolios:
        return None
    for s in _version_snapshots.get(portfolio_id, []):
        if s["id"] == version_id:
            p = s["portfolio"]
            holdings = [
                _holding_from_dict(h, portfolio_id)
                for h in s["holdings"]
            ]
            return PortfolioWithHoldings(
                id=p["id"],
                name=p["name"],
                description=p.get("description"),
                created_at=p["created_at"],
                updated_at=p.get("updated_at"),
                holdings=holdings,
            )
    return None


def clear_all() -> None:
    """Clear all in-memory data. For testing only."""
    _portfolios.clear()
    _holdings_by_portfolio.clear()
    _version_snapshots.clear()


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
