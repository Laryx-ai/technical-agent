"""Shared pytest fixtures for the technical-agent backend tests."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    """Import and return the FastAPI application (once per test session)."""
    from main import app as _app
    return _app


@pytest.fixture()
def client(app):
    """Return a fresh TestClient for each test."""
    return TestClient(app)
