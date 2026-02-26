"""Tests for portfolio import/export API."""
import io

from fastapi.testclient import TestClient


def test_export_csv_portfolio_not_found(client: TestClient) -> None:
    """GET .../export returns 404 when portfolio not found."""
    r = client.get("/api/v1/portfolios/nonexistent/export?format=csv")
    assert r.status_code == 404


def test_export_csv_success(client: TestClient) -> None:
    """Export portfolio as CSV returns CSV content and correct headers."""
    create = client.post("/api/v1/portfolios", json={"name": "Export Me", "description": "Desc"})
    pid = create.json()["id"]
    client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={
            "symbol": "AAPL",
            "company_name": "Apple",
            "quantity": 10.0,
            "average_price": 150.0,
        },
    )
    r = client.get(f"/api/v1/portfolios/{pid}/export?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    text = r.content.decode("utf-8")
    assert "portfolio_name" in text
    assert "Export Me" in text
    assert "symbol" in text
    assert "AAPL" in text


def test_export_excel_success(client: TestClient) -> None:
    """Export portfolio as Excel returns xlsx content."""
    create = client.post("/api/v1/portfolios", json={"name": "Excel Fund", "description": None})
    pid = create.json()["id"]
    r = client.get(f"/api/v1/portfolios/{pid}/export?format=xlsx")
    assert r.status_code == 200
    assert "spreadsheet" in r.headers.get("content-type", "") or "xlsx" in r.headers.get("content-type", "")
    assert len(r.content) > 100


def test_export_invalid_format(client: TestClient) -> None:
    """Export with invalid format returns 400."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r = client.get(f"/api/v1/portfolios/{pid}/export?format=pdf")
    assert r.status_code == 400


def test_import_csv_success(client: TestClient) -> None:
    """Import CSV creates portfolio and holdings; returns portfolio_id and counts."""
    csv_content = (
        "portfolio_name,portfolio_description\n"
        "Imported Fund,My description\n"
        "symbol,company_name,quantity,average_price,sector\n"
        "MSFT,Microsoft,5,200.5,Technology\n"
        "GOOG,Alphabet,2,150.0,\n"
    )
    r = client.post(
        "/api/v1/portfolios/import",
        files={"file": ("port.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["portfolio_id"] is not None
    assert data["holdings_created"] == 2
    assert data["errors"] == []
    pid = data["portfolio_id"]
    get_r = client.get(f"/api/v1/portfolios/{pid}")
    assert get_r.status_code == 200
    assert get_r.json()["name"] == "Imported Fund"
    list_r = client.get(f"/api/v1/portfolios/{pid}/holdings")
    assert list_r.json()["total"] == 2


def test_import_csv_round_trip(client: TestClient) -> None:
    """Export then re-import round-trip: import creates portfolio with same data."""
    create = client.post("/api/v1/portfolios", json={"name": "Round Trip", "description": "D"})
    pid = create.json()["id"]
    client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={"symbol": "X", "company_name": "X Inc", "quantity": 1.0, "average_price": 10.0},
    )
    export_r = client.get(f"/api/v1/portfolios/{pid}/export?format=csv")
    csv_bytes = export_r.content
    import_r = client.post(
        "/api/v1/portfolios/import",
        files={"file": ("reimport.csv", io.BytesIO(csv_bytes), "text/csv")},
    )
    assert import_r.status_code == 200
    data = import_r.json()
    assert data["holdings_created"] == 1
    assert data["errors"] == []
    new_pid = data["portfolio_id"]
    assert new_pid != pid
    p = client.get(f"/api/v1/portfolios/{new_pid}").json()
    assert p["name"] == "Round Trip"
    assert p["description"] == "D"


def test_import_csv_invalid_columns(client: TestClient) -> None:
    """Import CSV with invalid/missing columns returns error report."""
    csv_content = "bad_header,other\n"
    r = client.post(
        "/api/v1/portfolios/import",
        files={"file": ("bad.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    # With only header and no data row, import may return error and no portfolio
    assert "errors" in data
    assert data["holdings_created"] == 0


def test_import_csv_validation_errors(client: TestClient) -> None:
    """Import CSV with invalid quantity/price returns errors in report."""
    csv_content = (
        "portfolio_name,portfolio_description\n"
        "P,\n"
        "symbol,company_name,quantity,average_price,sector\n"
        "A,Company A,-1,100,\n"
        "B,Company B,1,0,\n"
        "C,Valid Co,2,50,\n"
    )
    r = client.post(
        "/api/v1/portfolios/import",
        files={"file": ("v.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["portfolio_id"] is not None
    assert data["holdings_created"] == 1
    assert len(data["errors"]) >= 2


def test_import_wrong_file_type(client: TestClient) -> None:
    """Import with non-CSV/Excel file returns 400."""
    r = client.post(
        "/api/v1/portfolios/import",
        files={"file": ("x.pdf", io.BytesIO(b"binary"), "application/pdf")},
    )
    assert r.status_code == 400


def test_import_excel_success(client: TestClient) -> None:
    """Import Excel (generated by export) creates portfolio and holdings."""
    create = client.post("/api/v1/portfolios", json={"name": "For Excel", "description": "Ex"})
    pid = create.json()["id"]
    client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={"symbol": "E", "company_name": "E Corp", "quantity": 3.0, "average_price": 20.0},
    )
    export_r = client.get(f"/api/v1/portfolios/{pid}/export?format=xlsx")
    xlsx_bytes = export_r.content
    import_r = client.post(
        "/api/v1/portfolios/import",
        files={"file": ("re.xlsx", io.BytesIO(xlsx_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert import_r.status_code == 200
    data = import_r.json()
    assert data["portfolio_id"] is not None
    assert data["holdings_created"] == 1
    assert data["errors"] == []
