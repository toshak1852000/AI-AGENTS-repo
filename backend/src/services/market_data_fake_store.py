"""
In-memory store for fake market data (symbol -> time series).
Load from CSV for local/dev use; data_collection node uses this when populated.
"""
from pathlib import Path
from typing import Optional

# symbol -> list of {date, open, high, low, close, volume} sorted by date
_market_data: dict[str, list[dict]] = {}


def load_from_csv(path: str | Path) -> None:
    """Load market_data.csv into the store. CSV columns: symbol, date, open, high, low, close, volume."""
    path = Path(path)
    if not path.exists():
        return
    _market_data.clear()
    with open(path, newline="", encoding="utf-8") as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            symbol = (row.get("symbol") or "").strip()
            if not symbol:
                continue
            try:
                date_str = (row.get("date") or "").strip()
                open_p = float(row.get("open", 0))
                high = float(row.get("high", 0))
                low = float(row.get("low", 0))
                close = float(row.get("close", 0))
                volume = int(float(row.get("volume", 0)))
            except (ValueError, TypeError):
                continue
            entry = {
                "date": date_str,
                "open": open_p,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
            _market_data.setdefault(symbol, []).append(entry)
    for symbol in _market_data:
        _market_data[symbol].sort(key=lambda x: x["date"])


def get_series(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """Return time series for symbol, optionally filtered by date range (inclusive)."""
    rows = _market_data.get(symbol, [])
    if not start_date and not end_date:
        return list(rows)
    out = []
    for r in rows:
        d = r.get("date", "")
        if start_date and d < start_date:
            continue
        if end_date and d > end_date:
            continue
        out.append(r)
    return out


def get_latest_price(symbol: str) -> Optional[float]:
    """Return latest close price for symbol, or None if not found."""
    rows = _market_data.get(symbol, [])
    if not rows:
        return None
    return rows[-1].get("close")


def has_data() -> bool:
    """Return True if the store has any data."""
    return len(_market_data) > 0


def get_symbols() -> list[str]:
    """Return list of symbols in the store."""
    return list(_market_data.keys())


def clear() -> None:
    """Clear all data (for tests)."""
    _market_data.clear()
