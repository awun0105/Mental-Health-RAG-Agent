"""API-layer test for the health endpoint via FastAPI TestClient."""

from __future__ import annotations

import pytest
from app.core.config import settings
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    """GET /api/v1/health returns 200 and a healthy payload."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"


def test_supabase_health_endpoint_returns_ok(client: TestClient) -> None:
    """GET /api/v1/health/supabase performs a lightweight Supabase read."""
    response = client.get("/api/v1/health/supabase")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "healthy",
        "service": "supabase",
        "checked_table": "roles",
        "row_count": "0",
    }


def test_supabase_health_endpoint_rejects_invalid_keepalive_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When KEEPALIVE_TOKEN is configured, callers must send the matching header."""
    monkeypatch.setattr(settings, "keepalive_token", "expected-token")

    response = client.get("/api/v1/health/supabase", headers={"X-Keepalive-Token": "bad"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid keepalive token"


def test_supabase_health_endpoint_accepts_valid_keepalive_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid keepalive token allows the Supabase ping."""
    monkeypatch.setattr(settings, "keepalive_token", "expected-token")

    response = client.get(
        "/api/v1/health/supabase",
        headers={"X-Keepalive-Token": "expected-token"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
