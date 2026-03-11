"""Tests for GET/POST/PUT/DELETE /api/v1/portfolios."""
from fastapi.testclient import TestClient

from src.services import portfolio_service as svc
from src.schemas.portfolio import HoldingCreate


def test_list_portfolios_empty(client: TestClient) -> None:
    """GET /api/v1/portfolios returns paginated list; empty initially."""
    r = client.get("/api/v1/portfolios")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert "portfolios" in data
    assert data["total"] == 0
    assert data["portfolios"] == []


def test_list_portfolios_pagination(client: TestClient) -> None:
    """List with skip/limit returns correct slice."""
    # Create 3 portfolios
    for i in range(3):
        client.post("/api/v1/portfolios", json={"name": f"P{i}", "description": None})
    r = client.get("/api/v1/portfolios?skip=1&limit=1")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["skip"] == 1
    assert data["limit"] == 1
    assert len(data["portfolios"]) == 1


def test_list_portfolios_name_filter(client: TestClient) -> None:
    """List with name filter returns only matching portfolios."""
    client.post("/api/v1/portfolios", json={"name": "Alpha Fund", "description": None})
    client.post("/api/v1/portfolios", json={"name": "Beta Fund", "description": None})
    r = client.get("/api/v1/portfolios?name=alpha")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["portfolios"][0]["name"] == "Alpha Fund"


def test_get_portfolio_not_found(client: TestClient) -> None:
    """GET /api/v1/portfolios/{id} returns 404 when not found."""
    r = client.get("/api/v1/portfolios/nonexistent-id")
    assert r.status_code == 404
    assert "not found" in r.json().get("detail", "").lower()


def test_get_portfolio_success(client: TestClient) -> None:
    """GET /api/v1/portfolios/{id} returns 200 and portfolio when found."""
    create = client.post("/api/v1/portfolios", json={"name": "My Portfolio", "description": "Desc"})
    assert create.status_code == 201
    pid = create.json()["id"]
    r = client.get(f"/api/v1/portfolios/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid
    assert r.json()["name"] == "My Portfolio"
    assert r.json()["description"] == "Desc"


def test_create_portfolio_success(client: TestClient) -> None:
    """POST /api/v1/portfolios with valid body returns 201 and portfolio."""
    r = client.post("/api/v1/portfolios", json={"name": "New", "description": "D"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["name"] == "New"
    assert data["description"] == "D"
    assert "created_at" in data


def test_create_portfolio_validation_error(client: TestClient) -> None:
    """POST with invalid body returns 422 (validation error)."""
    r = client.post("/api/v1/portfolios", json={})
    assert r.status_code == 422


def test_update_portfolio_success(client: TestClient) -> None:
    """PUT /api/v1/portfolios/{id} with valid body returns 200 and updated portfolio."""
    create = client.post("/api/v1/portfolios", json={"name": "Old", "description": None})
    pid = create.json()["id"]
    r = client.put(f"/api/v1/portfolios/{pid}", json={"name": "Updated"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"


def test_update_portfolio_not_found(client: TestClient) -> None:
    """PUT /api/v1/portfolios/{id} returns 404 when portfolio does not exist."""
    r = client.put("/api/v1/portfolios/nonexistent-id", json={"name": "X"})
    assert r.status_code == 404


def test_update_portfolio_validation_error(client: TestClient) -> None:
    """PUT with invalid body returns 422."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r = client.put(f"/api/v1/portfolios/{pid}", json={"name": 123})  # wrong type
    assert r.status_code == 422


def test_delete_portfolio_not_found(client: TestClient) -> None:
    """DELETE /api/v1/portfolios/{id} returns 404 when not found."""
    r = client.delete("/api/v1/portfolios/nonexistent-id")
    assert r.status_code == 404


def test_delete_portfolio_success(client: TestClient) -> None:
    """DELETE /api/v1/portfolios/{id} returns 204 when portfolio has no holdings."""
    create = client.post("/api/v1/portfolios", json={"name": "To Delete", "description": None})
    pid = create.json()["id"]
    r = client.delete(f"/api/v1/portfolios/{pid}")
    assert r.status_code == 204
    get_r = client.get(f"/api/v1/portfolios/{pid}")
    assert get_r.status_code == 404


def test_delete_portfolio_with_holdings_returns_409(client: TestClient) -> None:
    """DELETE /api/v1/portfolios/{id} returns 409 when portfolio has holdings."""
    create = client.post("/api/v1/portfolios", json={"name": "With Holdings", "description": None})
    pid = create.json()["id"]
    # Add a holding via service (holdings API not yet implemented)
    svc.add_holding(pid, HoldingCreate(symbol="AAPL", company_name="Apple", quantity=10.0, average_price=150.0))
    r = client.delete(f"/api/v1/portfolios/{pid}")
    assert r.status_code == 409
    assert "holdings" in r.json().get("detail", "").lower()
    # Portfolio still exists
    get_r = client.get(f"/api/v1/portfolios/{pid}")
    assert get_r.status_code == 200


def test_list_query_validation(client: TestClient) -> None:
    """Invalid query params (e.g. negative skip) return 422."""
    r = client.get("/api/v1/portfolios?skip=-1")
    assert r.status_code == 422
