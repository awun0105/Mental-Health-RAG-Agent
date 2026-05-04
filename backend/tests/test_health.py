"""Tests for the /health endpoint."""

from __future__ import annotations

from app.api.health import health_check


async def test_health_returns_healthy_status() -> None:
    """`/health` returns the canonical healthy payload used by liveness probes."""
    body = await health_check()
    assert body["status"] == "healthy"
    assert "version" in body
