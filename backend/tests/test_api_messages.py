"""API-layer tests for patient transcript message endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.constants import MessageRole, SessionStatus, UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user_row
from tests.fakes.fake_supabase import FakeSupabase


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


def _seed_message(
    fake_db: FakeSupabase,
    *,
    session_id: str,
    content: str,
    created_at: datetime,
) -> None:
    fake_db.seed(
        "chat_messages",
        [
            {
                "id": str(uuid4()),
                "session_id": session_id,
                "role": MessageRole.PATIENT.value,
                "content": content,
                "safety_flag": False,
                "safety_severity": "none",
                "trace_id": None,
                "created_at": created_at.isoformat(),
            },
        ],
    )


def test_list_messages_returns_owned_session_messages(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])
    session_id = _seed_session(fake_db, user_id=patient["id"])
    base_time = datetime(2030, 1, 1, tzinfo=UTC)
    _seed_message(
        fake_db,
        session_id=session_id,
        content="second",
        created_at=base_time + timedelta(seconds=2),
    )
    _seed_message(fake_db, session_id=session_id, content="first", created_at=base_time)

    response = client.get(
        f"/api/v1/sessions/{session_id}/messages",
        headers=auth_headers(user_id=patient["id"], email=patient["email"], role=UserRole.PATIENT),
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["content"] for item in body["items"]] == ["first", "second"]
    assert body["limit"] == 50
    assert body["offset"] == 0


def test_create_message_for_owned_active_session_returns_patient_message(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])
    session_id = _seed_session(fake_db, user_id=patient["id"])

    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "I feel anxious today"},
        headers=auth_headers(user_id=patient["id"], email=patient["email"], role=UserRole.PATIENT),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["session_id"] == session_id
    assert body["role"] == MessageRole.PATIENT.value
    assert body["content"] == "I feel anxious today"


def test_create_message_for_closed_session_returns_403(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])
    session_id = _seed_session(fake_db, user_id=patient["id"], status=SessionStatus.CLOSED)

    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "hello"},
        headers=auth_headers(user_id=patient["id"], email=patient["email"], role=UserRole.PATIENT),
    )

    assert response.status_code == 403


def test_stranger_patient_cannot_list_or_create_messages(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    owner = make_user_row(role=UserRole.PATIENT)
    other = make_user_row(role=UserRole.PATIENT, email="other@example.com")
    fake_db.seed("users", [owner, other])
    session_id = _seed_session(fake_db, user_id=owner["id"])

    headers = auth_headers(user_id=other["id"], email=other["email"], role=UserRole.PATIENT)

    list_response = client.get(f"/api/v1/sessions/{session_id}/messages", headers=headers)
    create_response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": "not mine"},
        headers=headers,
    )

    assert list_response.status_code == 403
    assert create_response.status_code == 403


def test_empty_message_content_returns_422(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [patient])
    session_id = _seed_session(fake_db, user_id=patient["id"])

    response = client.post(
        f"/api/v1/sessions/{session_id}/messages",
        json={"content": ""},
        headers=auth_headers(user_id=patient["id"], email=patient["email"], role=UserRole.PATIENT),
    )

    assert response.status_code == 422
