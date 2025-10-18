"""Tests for health check endpoints."""

from fastapi.testclient import TestClient

from apps.core import app

client = TestClient(app)


def test_healthz():
    """Test health check endpoint returns 200 and correct structure."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "time" in data


def test_version():
    """Test version endpoint returns correct structure."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "backend" in data
    assert "web" in data
    assert data["backend"] == "0.1.0"
