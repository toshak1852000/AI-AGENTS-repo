"""Pytest fixtures for API tests."""
import pytest
from fastapi.testclient import TestClient

from main import app
from src.services import portfolio_service as portfolio_svc


@pytest.fixture(autouse=True)
def reset_portfolio_store():
    """Reset in-memory portfolio store before each test for isolation."""
    portfolio_svc.clear_all()
    yield


@pytest.fixture
def client() -> TestClient:
    """Return a test client for the FastAPI app."""
    return TestClient(app)
