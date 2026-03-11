"""Tests for Report API endpoints."""
import os
import pytest
from fastapi.testclient import TestClient

from main import app
from src.services import report_service


@pytest.fixture(autouse=True)
def reset_report_store():
    """Reset in-memory report store before each test."""
    report_service.clear_all()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestGenerateReport:
    """POST /api/v1/reports/generate"""

    def test_generate_report_returns_201_completed(self, client: TestClient):
        payload = {
            "name": "Test Report",
            "type": "portfolio_analysis",
            "format": "pdf",
            "portfolio_id": "p1",
        }
        resp = client.post("/api/v1/reports/generate", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["name"] == "Test Report"
        assert data["status"] == "completed"
        assert data["file_path"] is not None
        assert data["download_url"] is not None

    def test_generate_report_requires_name(self, client: TestClient):
        payload = {"type": "portfolio_analysis", "format": "pdf"}
        resp = client.post("/api/v1/reports/generate", json=payload)
        assert resp.status_code == 422  # validation error


class TestGenerateMultiFormat:
    """Generate reports in PDF, Excel, JSON, and CSV formats."""

    @pytest.mark.parametrize("fmt", ["pdf", "excel", "json", "csv"])
    def test_generate_each_format(self, client: TestClient, fmt: str):
        payload = {
            "name": f"{fmt.upper()} Report",
            "type": "portfolio_analysis",
            "format": fmt,
        }
        resp = client.post("/api/v1/reports/generate", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["format"] == fmt
        assert data["file_path"] is not None
        assert data["download_url"] is not None


class TestListReports:
    """GET /api/v1/reports/"""

    def test_list_empty(self, client: TestClient):
        resp = client.get("/api/v1/reports/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reports"] == []
        assert data["total"] == 0

    def test_list_after_create(self, client: TestClient):
        client.post("/api/v1/reports/generate", json={
            "name": "R1", "type": "scenario_analysis", "format": "excel"
        })
        client.post("/api/v1/reports/generate", json={
            "name": "R2", "type": "scenario_analysis", "format": "json"
        })
        resp = client.get("/api/v1/reports/")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["reports"]) == 2


class TestGetReport:
    """GET /api/v1/reports/{report_id}"""

    def test_get_existing(self, client: TestClient):
        cr = client.post("/api/v1/reports/generate", json={
            "name": "Get Test", "type": "portfolio_analysis", "format": "csv"
        })
        rid = cr.json()["id"]
        resp = client.get(f"/api/v1/reports/{rid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == rid
        assert resp.json()["status"] == "completed"

    def test_get_nonexistent(self, client: TestClient):
        resp = client.get("/api/v1/reports/nonexistent-id")
        assert resp.status_code == 404


class TestDownloadReport:
    """GET /api/v1/reports/{report_id}/download"""

    def test_download_completed_report(self, client: TestClient):
        cr = client.post("/api/v1/reports/generate", json={
            "name": "DL Report", "type": "portfolio_analysis", "format": "pdf"
        })
        rid = cr.json()["id"]
        resp = client.get(f"/api/v1/reports/{rid}/download")
        assert resp.status_code == 200
        assert "application/pdf" in resp.headers["content-type"]
        # Real PDF starts with %PDF
        assert resp.content[:5] == b"%PDF-"

    def test_download_nonexistent(self, client: TestClient):
        resp = client.get("/api/v1/reports/nonexistent/download")
        assert resp.status_code == 404

    def test_download_pending_report_returns_400(self, client: TestClient):
        """Manually create a pending report without generating a file."""
        from src.schemas.report import ReportCreate
        report = report_service.create_report(ReportCreate(
            name="Stuck", type="portfolio_analysis", format="pdf"
        ))
        resp = client.get(f"/api/v1/reports/{report.id}/download")
        assert resp.status_code == 400
        assert "not ready" in resp.json()["detail"].lower()


class TestDownloadContentTypeAndSize:
    """Download returns correct content-type and non-zero size for each format."""

    EXPECTED_CT = {
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "csv": "text/csv",
    }

    @pytest.mark.parametrize("fmt", ["pdf", "excel", "json", "csv"])
    def test_download_content_type_per_format(self, client: TestClient, fmt: str):
        cr = client.post("/api/v1/reports/generate", json={
            "name": f"CT {fmt}", "type": "portfolio_analysis", "format": fmt
        })
        rid = cr.json()["id"]
        resp = client.get(f"/api/v1/reports/{rid}/download")
        assert resp.status_code == 200
        assert self.EXPECTED_CT[fmt] in resp.headers["content-type"]

    @pytest.mark.parametrize("fmt", ["pdf", "excel", "json", "csv"])
    def test_download_has_content(self, client: TestClient, fmt: str):
        """Downloaded file must have non-zero size."""
        cr = client.post("/api/v1/reports/generate", json={
            "name": f"Size {fmt}", "type": "portfolio_analysis", "format": fmt
        })
        rid = cr.json()["id"]
        resp = client.get(f"/api/v1/reports/{rid}/download")
        assert resp.status_code == 200
        assert len(resp.content) > 0


class TestInvalidInputs:
    """Invalid run_id, format, and template handling."""

    def test_invalid_report_id_get(self, client: TestClient):
        resp = client.get("/api/v1/reports/invalid-uuid-999")
        assert resp.status_code == 404

    def test_invalid_report_id_download(self, client: TestClient):
        resp = client.get("/api/v1/reports/invalid-uuid-999/download")
        assert resp.status_code == 404

    def test_invalid_format_rejected(self, client: TestClient):
        """Pydantic ReportFormat enum should reject unknown formats."""
        payload = {
            "name": "Bad Format",
            "type": "portfolio_analysis",
            "format": "docx",  # not a valid ReportFormat
        }
        resp = client.post("/api/v1/reports/generate", json=payload)
        assert resp.status_code == 422

    def test_missing_type_rejected(self, client: TestClient):
        payload = {"name": "No Type", "format": "pdf"}
        resp = client.post("/api/v1/reports/generate", json=payload)
        assert resp.status_code == 422

    def test_empty_payload_rejected(self, client: TestClient):
        resp = client.post("/api/v1/reports/generate", json={})
        assert resp.status_code == 422
