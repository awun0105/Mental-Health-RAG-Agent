"""Service-layer tests for SessionService (Sessions CRUD foundation)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from app.core.config import settings
from app.core.constants import AuditAction, SessionStatus, UserRole
from app.core.exceptions import (
    AlreadyExistsError,
    ConsentRequiredError,
    ForbiddenError,
    NotFoundError,
)
from app.services.authorization_service import AuthorizationService
from app.services.session_service import SessionService

from tests.conftest import make_user_row, seed_rbac_tables
from tests.fakes.fake_supabase import FakeSupabase


def _seed_consent(fake_db: FakeSupabase, user_id: str, *, accepted: bool = True) -> None:
    """Insert a consent_records row matching the current consent policy version."""
    fake_db.seed(
        "consent_records",
        [
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "policy_version": settings.current_consent_policy_version,
                "accepted": accepted,
                "accepted_at": datetime.now(UTC).isoformat(),
            },
        ],
    )


def _seed_session(
    fake_db: FakeSupabase,
    *,
    user_id: str,
    status: SessionStatus = SessionStatus.ACTIVE,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Insert a chat_sessions row directly and return its id."""
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
                "metadata": metadata or {},
            },
        ],
    )
    return session_id


def _seed_user_with_role(
    fake_db: FakeSupabase,
    *,
    role: UserRole,
    email: str | None = None,
) -> dict[str, Any]:
    """Seed a users row AND its matching ``user_roles`` row.

    The session service now resolves the actor's role from
    ``user_roles`` via the production ``AuthorizationService``, so test
    users must have both representations seeded for the resource-level
    branching to work end-to-end against ``FakeSupabase``.
    """
    user = make_user_row(role=role, email=email)
    fake_db.seed("users", [user])
    seed_rbac_tables(fake_db, user_role_pairs=[(user["id"], role.value)])
    return user


@pytest.fixture(autouse=True)
def _reset_authz_cache() -> None:
    """Drop the process-local AuthorizationService cache between tests.

    The role-name cache is class-level; without this reset, a role-name
    set seeded in one test would leak into the next test that happens to
    reuse the same generated user id.
    """
    AuthorizationService.clear_cache()


@pytest.mark.asyncio
async def test_start_session_happy_path_creates_row_and_audit(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """A patient with valid consent can start an active session and emits audit."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    _seed_consent(fake_db, patient["id"])

    session = await session_service.start_session(
        user_id=patient["id"],
        metadata={"source": "web"},
    )

    assert session.user_id == patient["id"]
    assert session.status == SessionStatus.ACTIVE
    assert session.metadata == {"source": "web"}
    assert session.ended_at is None

    rows = fake_db.all_rows("chat_sessions")
    assert len(rows) == 1

    audits = [
        a
        for a in fake_db.all_rows("audit_logs")
        if a["action"] == AuditAction.SESSION_STARTED.value
    ]
    assert len(audits) == 1
    assert audits[0]["role"] == UserRole.PATIENT.value
    assert audits[0]["resource_id"] == session.id


@pytest.mark.asyncio
async def test_start_session_without_consent_raises(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """Without an accepted consent record, start_session must reject with 403."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)

    with pytest.raises(ConsentRequiredError):
        await session_service.start_session(
            user_id=patient["id"],
        )

    assert fake_db.all_rows("chat_sessions") == []


@pytest.mark.asyncio
async def test_start_session_rejects_when_active_session_exists(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """Q2 policy: 409 conflict if patient already has an active session."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    _seed_consent(fake_db, patient["id"])
    _seed_session(fake_db, user_id=patient["id"], status=SessionStatus.ACTIVE)

    with pytest.raises(AlreadyExistsError) as excinfo:
        await session_service.start_session(
            user_id=patient["id"],
        )

    assert excinfo.value.status_code == 409


@pytest.mark.asyncio
async def test_start_session_allows_after_previous_closed(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """A new session is permitted after the previous one was closed."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    _seed_consent(fake_db, patient["id"])
    _seed_session(fake_db, user_id=patient["id"], status=SessionStatus.CLOSED)

    session = await session_service.start_session(
        user_id=patient["id"],
    )

    assert session.status == SessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_start_session_rejects_non_patient(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """Doctors and admins cannot start patient chat sessions."""
    doctor = _seed_user_with_role(fake_db, role=UserRole.DOCTOR)

    with pytest.raises(ForbiddenError):
        await session_service.start_session(
            user_id=doctor["id"],
        )


@pytest.mark.asyncio
async def test_close_session_happy_path(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """Closing an active session sets status, ended_at and emits audit with reason."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    _seed_consent(fake_db, patient["id"])
    session_id = _seed_session(fake_db, user_id=patient["id"])

    closed = await session_service.close_session(
        session_id=session_id,
        current_user_id=patient["id"],
        reason="user_end",
    )

    assert closed.status == SessionStatus.CLOSED
    assert closed.ended_at is not None

    audits = [
        a for a in fake_db.all_rows("audit_logs") if a["action"] == AuditAction.SESSION_CLOSED.value
    ]
    assert len(audits) == 1
    assert audits[0]["metadata"]["reason"] == "user_end"
    assert audits[0]["role"] == UserRole.PATIENT.value


@pytest.mark.asyncio
async def test_close_session_is_idempotent(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """Closing an already-closed session returns it unchanged with no extra audit."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    session_id = _seed_session(fake_db, user_id=patient["id"], status=SessionStatus.CLOSED)

    closed = await session_service.close_session(
        session_id=session_id,
        current_user_id=patient["id"],
    )

    assert closed.status == SessionStatus.CLOSED
    audits = [
        a for a in fake_db.all_rows("audit_logs") if a["action"] == AuditAction.SESSION_CLOSED.value
    ]
    assert audits == []


@pytest.mark.asyncio
async def test_close_session_not_found_raises(
    session_service: SessionService,
) -> None:
    """Closing an unknown session id raises NotFoundError."""
    with pytest.raises(NotFoundError):
        await session_service.close_session(
            session_id=str(uuid4()),
            current_user_id=str(uuid4()),
        )


@pytest.mark.asyncio
async def test_close_session_rejects_non_owner(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """Only the owning patient can close their own session."""
    owner = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    other = _seed_user_with_role(fake_db, role=UserRole.PATIENT, email="other@example.com")
    session_id = _seed_session(fake_db, user_id=owner["id"])

    with pytest.raises(ForbiddenError):
        await session_service.close_session(
            session_id=session_id,
            current_user_id=other["id"],
        )


@pytest.mark.asyncio
async def test_get_session_owner_patient_succeeds(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """The session's owner patient can read their own session."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    session_id = _seed_session(fake_db, user_id=patient["id"])

    session = await session_service.get_session(
        session_id=session_id,
        current_user_id=patient["id"],
    )

    assert session.id == session_id


@pytest.mark.asyncio
async def test_get_session_assigned_doctor_succeeds(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """A doctor with an active assignment to the patient can read the session."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    doctor = _seed_user_with_role(fake_db, role=UserRole.DOCTOR)
    session_id = _seed_session(fake_db, user_id=patient["id"])
    fake_db.seed(
        "doctor_assignments",
        [
            {
                "id": str(uuid4()),
                "doctor_id": doctor["id"],
                "patient_id": patient["id"],
                "assigned_by": doctor["id"],
                "is_active": True,
                "created_at": datetime.now(UTC).isoformat(),
            },
        ],
    )

    session = await session_service.get_session(
        session_id=session_id,
        current_user_id=doctor["id"],
    )

    assert session.id == session_id


@pytest.mark.asyncio
async def test_get_session_unassigned_doctor_rejected(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """A doctor without an active assignment to the patient cannot read the session."""
    patient = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    doctor = _seed_user_with_role(fake_db, role=UserRole.DOCTOR)
    session_id = _seed_session(fake_db, user_id=patient["id"])

    with pytest.raises(ForbiddenError):
        await session_service.get_session(
            session_id=session_id,
            current_user_id=doctor["id"],
        )


@pytest.mark.asyncio
async def test_list_sessions_for_user_filters_by_user_only(
    session_service: SessionService,
    fake_db: FakeSupabase,
) -> None:
    """``list_sessions_for_user`` returns only sessions belonging to that user."""
    me = _seed_user_with_role(fake_db, role=UserRole.PATIENT)
    other = _seed_user_with_role(fake_db, role=UserRole.PATIENT, email="other@example.com")
    _seed_session(fake_db, user_id=me["id"])
    _seed_session(fake_db, user_id=other["id"])

    response = await session_service.list_sessions_for_user(
        user_id=me["id"],
    )

    assert len(response.items) == 1
    assert response.items[0].user_id == me["id"]
