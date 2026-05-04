"""API-layer tests for /api/v1/consent/* endpoints."""

from __future__ import annotations

from app.core.constants import UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers
from tests.fakes.fake_supabase import FakeSupabase


def test_accept_consent_without_token_returns_401(client: TestClient) -> None:
    """The consent accept endpoint requires authentication."""
    response = client.post(
        "/api/v1/consent/accept",
        json={"policy_version": "1.0"},
    )

    assert response.status_code in (401, 403)


def test_accept_consent_persists_record_and_audit(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """A logged-in user can accept consent; a record + audit row are written.

    Regression guard for PR #9: the audit row must include the caller's role.
    """
    headers = auth_headers(
        user_id="patient-1",
        email="p1@example.com",
        role=UserRole.PATIENT,
    )

    response = client.post(
        "/api/v1/consent/accept",
        json={"policy_version": "1.0"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "patient-1"
    assert body["policy_version"] == "1.0"
    assert body["accepted"] is True

    consent_rows = fake_db.tables.get("consent_records", [])
    assert len(consent_rows) == 1

    audit_rows = fake_db.tables.get("audit_logs", [])
    assert len(audit_rows) == 1
    assert audit_rows[0]["role"] == "patient"
    assert audit_rows[0]["action"] == "consent_accepted"


def test_consent_status_reads_back_latest(
    client: TestClient,
) -> None:
    """After accepting v1.0, /consent/status should report it as the latest accepted version."""
    headers = auth_headers(
        user_id="patient-2",
        email="p2@example.com",
        role=UserRole.PATIENT,
    )
    accept = client.post(
        "/api/v1/consent/accept",
        json={"policy_version": "1.0"},
        headers=headers,
    )
    assert accept.status_code == 200

    response = client.get("/api/v1/consent/status", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["latest_accepted_policy_version"] == "1.0"
