"""API-layer tests for /api/v1/sessions/* endpoints (Sessions CRUD foundation)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import settings
from app.core.constants import SessionStatus, UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user_row
from tests.fakes.fake_supabase import FakeSupabase


def _seed_consent(fake_db: FakeSupabase, user_id: str) -> None:
    fake_db.seed(
        "consent_records",
        [
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "policy_version": settings.current_consent_policy_version,
                "accepted": True,
                "accepted_at": datetime.now(UTC).isoformat(),
            },
        ],
    )


def _seed_session(
    fake_db: FakeSupabase,
    *,
    user_id: str,
    status: SessionStatus = SessionStatus.ACTIVE,
) -> str:
    session_id = str(uuid4())
    fake_db.seed(
        "chat_sessions",
        [
            {
                "id": session_id,
                "user_id": user_id,
                "status": status.value,
                "started_at": datetime.now(UTC).isoformat(),
                "ended_at": None,
                "metadata": {},
            },
        ],
    )
    return session_id


def test_post_sessions_without_token_is_unauthorised(client: TestClient) -> None:
    """Anonymous callers cannot start sessions."""
    response = client.post("/api/v1/sessions", json={})

    assert response.status_code in (401, 403)


def test_post_sessions_as_doctor_is_forbidden(client: TestClient) -> None:
    """Only patients can start a chat session."""
    response = client.post(
        "/api/v1/sessions",
        json={},
        headers=auth_headers(role=UserRole.DOCTOR),
    )

    assert response.status_code == 403


def test_post_sessions_happy_path_returns_201(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """A patient with valid consent can start a session."""
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])
    _seed_consent(fake_db, patient["id"])

    response = client.post(
        "/api/v1/sessions",
        json={"metadata": {"locale": "vi"}},
        headers=auth_headers(
            user_id=patient["id"],
            email=patient["email"],
            role=UserRole.PATIENT,
        ),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == patient["id"]
    assert body["status"] == SessionStatus.ACTIVE.value
    assert body["metadata"] == {"locale": "vi"}


def test_post_sessions_without_consent_returns_403(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """A patient who has not accepted consent cannot start a session."""
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])

    response = client.post(
        "/api/v1/sessions",
        json={},
        headers=auth_headers(
            user_id=patient["id"],
            email=patient["email"],
            role=UserRole.PATIENT,
        ),
    )

    assert response.status_code == 403


def test_post_sessions_close_returns_200_and_records_audit(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Closing an owned active session marks it closed and audits the reason."""
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])
    session_id = _seed_session(fake_db, user_id=patient["id"])

    response = client.post(
        f"/api/v1/sessions/{session_id}/close",
        json={"reason": "intent_end"},
        headers=auth_headers(
            user_id=patient["id"],
            email=patient["email"],
            role=UserRole.PATIENT,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == SessionStatus.CLOSED.value
    audits = [a for a in fake_db.all_rows("audit_logs") if a["resource_id"] == session_id]
    assert len(audits) == 1
    assert audits[0]["metadata"]["reason"] == "intent_end"


def test_get_session_owner_returns_200(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """The owner patient can read their session by id."""
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])
    session_id = _seed_session(fake_db, user_id=patient["id"])

    response = client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers(
            user_id=patient["id"],
            email=patient["email"],
            role=UserRole.PATIENT,
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == session_id


def test_get_session_stranger_patient_returns_403(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """A different patient cannot read someone else's session."""
    owner = make_user_row(role=UserRole.PATIENT)
    other = make_user_row(role=UserRole.PATIENT, email="other@example.com")
    fake_db.seed("users", [owner, other])
    session_id = _seed_session(fake_db, user_id=owner["id"])

    response = client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers(
            user_id=other["id"],
            email=other["email"],
            role=UserRole.PATIENT,
        ),
    )

    assert response.status_code == 403


def test_get_my_sessions_returns_only_own(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """``GET /sessions/me`` returns only the caller's sessions."""
    me = make_user_row(role=UserRole.PATIENT)
    other = make_user_row(role=UserRole.PATIENT, email="other@example.com")
    fake_db.seed("users", [me, other])
    _seed_session(fake_db, user_id=me["id"])
    _seed_session(fake_db, user_id=other["id"])

    response = client.get(
        "/api/v1/sessions/me",
        headers=auth_headers(
            user_id=me["id"],
            email=me["email"],
            role=UserRole.PATIENT,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["user_id"] == me["id"]
    assert body["limit"] == 20
    assert body["offset"] == 0
