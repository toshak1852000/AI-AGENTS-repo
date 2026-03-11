"""Tests for GET/POST/PUT/DELETE /api/v1/portfolios/{id}/holdings."""
from fastapi.testclient import TestClient


def test_list_holdings_portfolio_not_found(client: TestClient) -> None:
    """GET .../holdings returns 404 when portfolio not found."""
    r = client.get("/api/v1/portfolios/nonexistent/holdings")
    assert r.status_code == 404


def test_list_holdings_empty(client: TestClient) -> None:
    """GET .../holdings returns paginated list; empty for new portfolio."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r = client.get(f"/api/v1/portfolios/{pid}/holdings")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["holdings"] == []


def test_list_holdings_pagination(client: TestClient) -> None:
    """List holdings with skip/limit."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    for i in range(3):
        client.post(
            f"/api/v1/portfolios/{pid}/holdings",
            json={
                "symbol": f"SYM{i}",
                "company_name": f"Co{i}",
                "quantity": 10.0,
                "average_price": 100.0,
            },
        )
    r = client.get(f"/api/v1/portfolios/{pid}/holdings?skip=1&limit=1")
    assert r.status_code == 200
    assert r.json()["total"] == 3
    assert len(r.json()["holdings"]) == 1


def test_get_holding_not_found(client: TestClient) -> None:
    """GET .../holdings/{holding_id} returns 404 when portfolio or holding not found."""
    r = client.get("/api/v1/portfolios/nonexistent/holdings/some-holding")
    assert r.status_code == 404
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r2 = client.get(f"/api/v1/portfolios/{pid}/holdings/nonexistent-holding")
    assert r2.status_code == 404


def test_get_holding_success(client: TestClient) -> None:
    """GET .../holdings/{id} returns 200 and holding when found."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    add = client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={
            "symbol": "AAPL",
            "company_name": "Apple",
            "quantity": 10.0,
            "average_price": 150.0,
        },
    )
    hid = add.json()["id"]
    r = client.get(f"/api/v1/portfolios/{pid}/holdings/{hid}")
    assert r.status_code == 200
    assert r.json()["symbol"] == "AAPL"
    assert r.json()["quantity"] == 10.0


def test_create_holding_success(client: TestClient) -> None:
    """POST .../holdings with valid body returns 201 and holding."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r = client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={
            "symbol": "MSFT",
            "company_name": "Microsoft",
            "quantity": 5.0,
            "average_price": 200.0,
            "sector": "Technology",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["symbol"] == "MSFT"
    assert data["company_name"] == "Microsoft"
    assert data["quantity"] == 5.0
    assert data["average_price"] == 200.0
    assert data["sector"] == "Technology"
    assert "id" in data
    assert "created_at" in data


def test_create_holding_portfolio_not_found(client: TestClient) -> None:
    """POST .../holdings returns 404 when portfolio not found."""
    r = client.post(
        "/api/v1/portfolios/nonexistent/holdings",
        json={
            "symbol": "X",
            "company_name": "X",
            "quantity": 1.0,
            "average_price": 1.0,
        },
    )
    assert r.status_code == 404


def test_create_holding_validation_error(client: TestClient) -> None:
    """POST .../holdings with invalid body returns 422."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r = client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={"symbol": "X", "company_name": "X", "quantity": -1, "average_price": 1.0},
    )
    assert r.status_code == 422


def test_update_holding_success(client: TestClient) -> None:
    """PUT .../holdings/{id} returns 200 and updated holding."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    add = client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={
            "symbol": "GOOG",
            "company_name": "Alphabet",
            "quantity": 2.0,
            "average_price": 100.0,
        },
    )
    hid = add.json()["id"]
    r = client.put(
        f"/api/v1/portfolios/{pid}/holdings/{hid}",
        json={"quantity": 20.0, "average_price": 105.0},
    )
    assert r.status_code == 200
    assert r.json()["quantity"] == 20.0
    assert r.json()["average_price"] == 105.0


def test_update_holding_not_found(client: TestClient) -> None:
    """PUT .../holdings/{id} returns 404 when portfolio or holding not found."""
    r = client.put(
        "/api/v1/portfolios/nonexistent/holdings/some-id",
        json={"quantity": 1.0},
    )
    assert r.status_code == 404
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r2 = client.put(
        f"/api/v1/portfolios/{pid}/holdings/nonexistent-holding",
        json={"quantity": 1.0},
    )
    assert r2.status_code == 404


def test_update_holding_validation_error(client: TestClient) -> None:
    """PUT with invalid body (e.g. negative quantity) returns 422."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    add = client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={
            "symbol": "X",
            "company_name": "X",
            "quantity": 1.0,
            "average_price": 1.0,
        },
    )
    hid = add.json()["id"]
    r = client.put(
        f"/api/v1/portfolios/{pid}/holdings/{hid}",
        json={"quantity": -1},
    )
    assert r.status_code == 422


def test_delete_holding_not_found(client: TestClient) -> None:
    """DELETE .../holdings/{id} returns 404 when portfolio or holding not found."""
    r = client.delete("/api/v1/portfolios/nonexistent/holdings/some-id")
    assert r.status_code == 404


def test_delete_holding_success(client: TestClient) -> None:
    """DELETE .../holdings/{id} returns 204 and holding is removed."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    add = client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={
            "symbol": "DEL",
            "company_name": "Delete Me",
            "quantity": 1.0,
            "average_price": 1.0,
        },
    )
    hid = add.json()["id"]
    r = client.delete(f"/api/v1/portfolios/{pid}/holdings/{hid}")
    assert r.status_code == 204
    get_r = client.get(f"/api/v1/portfolios/{pid}/holdings/{hid}")
    assert get_r.status_code == 404
