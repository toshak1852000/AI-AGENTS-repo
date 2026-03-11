"""Tests for portfolio version history API."""
from fastapi.testclient import TestClient


def test_list_versions_portfolio_not_found(client: TestClient) -> None:
    """GET .../versions returns 404 when portfolio not found."""
    r = client.get("/api/v1/portfolios/nonexistent/versions")
    assert r.status_code == 404


def test_list_versions_empty_before_update(client: TestClient) -> None:
    """No versions until portfolio is updated."""
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r = client.get(f"/api/v1/portfolios/{pid}/versions")
    assert r.status_code == 200
    assert r.json() == []


def test_version_created_on_update(client: TestClient) -> None:
    """Updating portfolio creates a version snapshot."""
    create = client.post("/api/v1/portfolios", json={"name": "Original", "description": None})
    pid = create.json()["id"]
    client.put(f"/api/v1/portfolios/{pid}", json={"name": "Updated"})
    r = client.get(f"/api/v1/portfolios/{pid}/versions")
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 1
    assert versions[0]["portfolio_name"] == "Updated"
    assert "id" in versions[0]
    assert "created_at" in versions[0]


def test_get_portfolio_by_version_success(client: TestClient) -> None:
    """GET .../versions/{version_id} returns snapshot at that version."""
    create = client.post("/api/v1/portfolios", json={"name": "V1", "description": "D1"})
    pid = create.json()["id"]
    client.post(
        f"/api/v1/portfolios/{pid}/holdings",
        json={
            "symbol": "AAPL",
            "company_name": "Apple",
            "quantity": 10.0,
            "average_price": 100.0,
        },
    )
    client.put(f"/api/v1/portfolios/{pid}", json={"name": "V2"})
    # Now we have one version (created after first update). Version snapshot has name "V2" and 1 holding
    r_versions = client.get(f"/api/v1/portfolios/{pid}/versions")
    assert r_versions.status_code == 200
    versions = r_versions.json()
    assert len(versions) >= 1
    vid = versions[0]["id"]
    r_snap = client.get(f"/api/v1/portfolios/{pid}/versions/{vid}")
    assert r_snap.status_code == 200
    snap = r_snap.json()
    assert snap["name"] == "V2"
    assert "holdings" in snap
    assert len(snap["holdings"]) == 1
    assert snap["holdings"][0]["symbol"] == "AAPL"


def test_get_portfolio_by_version_not_found(client: TestClient) -> None:
    """GET .../versions/{version_id} returns 404 when portfolio or version not found."""
    r = client.get("/api/v1/portfolios/nonexistent/versions/some-version-id")
    assert r.status_code == 404
    create = client.post("/api/v1/portfolios", json={"name": "P", "description": None})
    pid = create.json()["id"]
    r2 = client.get(f"/api/v1/portfolios/{pid}/versions/nonexistent-version-id")
    assert r2.status_code == 404


def test_multiple_updates_create_multiple_versions(client: TestClient) -> None:
    """Each portfolio update creates a new version."""
    create = client.post("/api/v1/portfolios", json={"name": "A", "description": None})
    pid = create.json()["id"]
    client.put(f"/api/v1/portfolios/{pid}", json={"name": "B"})
    client.put(f"/api/v1/portfolios/{pid}", json={"name": "C"})
    r = client.get(f"/api/v1/portfolios/{pid}/versions")
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 2
    assert versions[0]["portfolio_name"] == "C"
    assert versions[1]["portfolio_name"] == "B"
