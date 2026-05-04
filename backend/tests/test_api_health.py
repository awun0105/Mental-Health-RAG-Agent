"""API-layer test for the health endpoint via FastAPI TestClient."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    """GET /api/v1/health returns 200 and a healthy payload."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
