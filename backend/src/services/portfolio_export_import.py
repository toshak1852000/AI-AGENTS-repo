"""Portfolio export (CSV/Excel) and import with validation and error reporting."""
import csv
import io
from typing import Optional

from openpyxl import Workbook

from src.services import portfolio_service as svc
from src.schemas.portfolio import HoldingCreate, PortfolioCreate


# CSV format: row1 = portfolio header, row2 = portfolio data, row3 = holdings header, row4+ = holdings
PORTFOLIO_CSV_HEADER = ["portfolio_name", "portfolio_description"]
HOLDINGS_CSV_HEADER = ["symbol", "company_name", "quantity", "average_price", "sector"]


def export_portfolio_csv(portfolio_id: str) -> Optional[str]:
    """Export portfolio and holdings as CSV string. Returns None if portfolio not found."""
    p = svc.get_portfolio(portfolio_id)
    if p is None:
        return None
    result = svc.list_holdings(portfolio_id, skip=0, limit=10_000)
    holdings = (result[0], result[1]) if result else ([], 0)
    holdings_list = holdings[0]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(PORTFOLIO_CSV_HEADER)
    w.writerow([p.name, p.description or ""])
    w.writerow(HOLDINGS_CSV_HEADER)
    for h in holdings_list:
        w.writerow([h.symbol, h.company_name, h.quantity, h.average_price, h.sector or ""])
    return buf.getvalue()


def export_portfolio_excel(portfolio_id: str) -> Optional[bytes]:
    """Export portfolio and holdings as Excel bytes. Returns None if portfolio not found."""
    p = svc.get_portfolio(portfolio_id)
    if p is None:
        return None
    result = svc.list_holdings(portfolio_id, skip=0, limit=10_000)
    holdings_list = result[0] if result else []
    wb = Workbook()
    ws_p = wb.active
    ws_p.title = "Portfolio"
    ws_p.append(["name", "description"])
    ws_p.append([p.name, p.description or ""])
    ws_h = wb.create_sheet("Holdings")
    ws_h.append(HOLDINGS_CSV_HEADER)
    for h in holdings_list:
        ws_h.append([h.symbol, h.company_name, h.quantity, h.average_price, h.sector or ""])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _parse_float(s: str) -> Optional[float]:
    try:
        return float(s.strip()) if s and s.strip() else None
    except ValueError:
        return None


def import_portfolio_csv(content: bytes | str) -> dict:
    """
    Import portfolio and holdings from CSV.
    Returns dict: portfolio_id, holdings_created, errors (list of {row, message}).
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    errors: list[dict] = []
    portfolio_id: Optional[str] = None
    holdings_created = 0
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if len(rows) < 2:
        return {
            "portfolio_id": None,
            "holdings_created": 0,
            "errors": [{"row": 1, "message": "CSV must have at least portfolio header and one data row"}],
        }
    # Row 0 = portfolio header, row 1 = portfolio data
    if rows[0] and [c.strip().lower() for c in rows[0]][:2] != [h.lower() for h in PORTFOLIO_CSV_HEADER]:
        errors.append({"row": 1, "message": f"Expected header row: {PORTFOLIO_CSV_HEADER}"})
    name = (rows[1][0].strip() if len(rows[1]) > 0 else "") or "Imported Portfolio"
    description = (rows[1][1].strip() if len(rows[1]) > 1 else "") or None
    portfolio = svc.create_portfolio(PortfolioCreate(name=name, description=description))
    portfolio_id = portfolio.id
    if len(rows) < 4:
        return {"portfolio_id": portfolio_id, "holdings_created": 0, "errors": errors}
    # Row 2 = holdings header, row 3+ = holdings
    for i, row in enumerate(rows[3:], start=4):
        if not row or all(not str(c).strip() for c in row):
            continue
        if len(row) < 5:
            errors.append({"row": i, "message": "Row must have symbol, company_name, quantity, average_price, sector"})
            continue
        symbol = (row[0] or "").strip()
        company_name = (row[1] or "").strip()
        qty = _parse_float(row[2])
        avg_price = _parse_float(row[3])
        sector = (row[4] or "").strip() or None
        if not symbol or not company_name:
            errors.append({"row": i, "message": "symbol and company_name are required"})
            continue
        if qty is None or qty <= 0:
            errors.append({"row": i, "message": "quantity must be a positive number"})
            continue
        if avg_price is None or avg_price <= 0:
            errors.append({"row": i, "message": "average_price must be a positive number"})
            continue
        try:
            payload = HoldingCreate(
                symbol=symbol,
                company_name=company_name,
                quantity=qty,
                average_price=avg_price,
                sector=sector,
            )
            if svc.add_holding(portfolio_id, payload):
                holdings_created += 1
        except Exception as e:
            errors.append({"row": i, "message": str(e)})
    return {"portfolio_id": portfolio_id, "holdings_created": holdings_created, "errors": errors}


def import_portfolio_excel(content: bytes) -> dict:
    """
    Import portfolio and holdings from Excel (first sheet = portfolio, second = holdings or first has both).
    Returns dict: portfolio_id, holdings_created, errors.
    """
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    errors: list[dict] = []
    portfolio_id = None
    holdings_created = 0
    if "Portfolio" in wb.sheetnames:
        ws_p = wb["Portfolio"]
        rows_p = list(ws_p.iter_rows(min_row=1, max_row=2, values_only=True))
        if len(rows_p) >= 2:
            name = str(rows_p[1][0] or "").strip() or "Imported Portfolio"
            description = str(rows_p[1][1] or "").strip() or None
            portfolio = svc.create_portfolio(PortfolioCreate(name=name, description=description))
            portfolio_id = portfolio.id
    else:
        # First sheet: first row name, second description
        ws = wb.active
        rows = list(ws.iter_rows(min_row=1, max_row=2, values_only=True))
        if not rows:
            return {"portfolio_id": None, "holdings_created": 0, "errors": [{"row": 1, "message": "Empty sheet"}]}
        name = str(rows[0][0] or "").strip() or "Imported Portfolio"
        description = str(rows[1][0] if len(rows) > 1 else "").strip() or None
        portfolio = svc.create_portfolio(PortfolioCreate(name=name, description=description))
        portfolio_id = portfolio.id
    if portfolio_id and "Holdings" in wb.sheetnames:
        ws_h = wb["Holdings"]
        for i, row in enumerate(ws_h.iter_rows(min_row=2, values_only=True), start=2):
            if not row or all(v is None or str(v).strip() == "" for v in row):
                continue
            row = [str(v or "").strip() for v in row]
            if len(row) < 5:
                errors.append({"row": i, "message": "Row must have symbol, company_name, quantity, average_price, sector"})
                continue
            symbol, company_name, qty_s, avg_s, sector_s = row[0], row[1], row[2], row[3], row[4] if len(row) > 4 else ""
            qty = _parse_float(qty_s)
            avg_price = _parse_float(avg_s)
            if not symbol or not company_name:
                errors.append({"row": i, "message": "symbol and company_name are required"})
                continue
            if qty is None or qty <= 0:
                errors.append({"row": i, "message": "quantity must be a positive number"})
                continue
            if avg_price is None or avg_price <= 0:
                errors.append({"row": i, "message": "average_price must be a positive number"})
                continue
            try:
                payload = HoldingCreate(symbol=symbol, company_name=company_name, quantity=qty, average_price=avg_price, sector=sector_s or None)
                if svc.add_holding(portfolio_id, payload):
                    holdings_created += 1
            except Exception as e:
                errors.append({"row": i, "message": str(e)})
    wb.close()
    return {"portfolio_id": portfolio_id, "holdings_created": holdings_created, "errors": errors}
