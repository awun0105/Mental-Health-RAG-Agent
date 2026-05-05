"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
from app.api.dependencies import get_supabase
from app.core.config import settings
from app.core.constants import AuthProvider, UserRole
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.message_repo import MessageRepository
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.user_repo import UserRepository
from app.main import app
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.consent_service import ConsentService
from app.services.session_service import SessionService
from fastapi.testclient import TestClient
from jose import jwt
from supabase import Client

from tests.fakes.fake_supabase import FakeSupabase


@pytest.fixture
def fake_db() -> FakeSupabase:
    """Fresh in-memory Supabase per test."""
    return FakeSupabase()


@pytest.fixture
def user_repo(fake_db: FakeSupabase) -> UserRepository:
    return UserRepository(db=cast(Client, fake_db))


@pytest.fixture
def consent_repo(fake_db: FakeSupabase) -> ConsentRepository:
    return ConsentRepository(db=cast(Client, fake_db))


@pytest.fixture
def audit_repo(fake_db: FakeSupabase) -> AuditRepository:
    return AuditRepository(db=cast(Client, fake_db))


@pytest.fixture
def assignment_repo(fake_db: FakeSupabase) -> AssignmentRepository:
    return AssignmentRepository(db=cast(Client, fake_db))


@pytest.fixture
def session_repo(fake_db: FakeSupabase) -> SessionRepository:
    return SessionRepository(db=cast(Client, fake_db))


@pytest.fixture
def message_repo(fake_db: FakeSupabase) -> MessageRepository:
    return MessageRepository(db=cast(Client, fake_db))


@pytest.fixture
def audit_service(audit_repo: AuditRepository) -> AuditService:
    return AuditService(audit_repo=audit_repo)


@pytest.fixture
def auth_service(
    user_repo: UserRepository,
    fake_db: FakeSupabase,
    audit_service: AuditService,
) -> AuthService:
    """AuthService wired with the in-memory FakeSupabase and a real audit service.

    AuthService now depends on the supabase Client (for the Google OAuth
    proxy methods) and on AuditService (for ``USER_LOGIN`` /
    ``USER_REGISTERED`` log events). The class-level
    ``_pending_tokens`` store is cleared per test so tokens minted in
    one test cannot leak into another.
    """
    AuthService._pending_tokens.clear()
    return AuthService(
        user_repo=user_repo,
        supabase=cast(Client, fake_db),
        audit_service=audit_service,
    )


@pytest.fixture
def consent_service(
    consent_repo: ConsentRepository,
    audit_service: AuditService,
) -> ConsentService:
    return ConsentService(consent_repo=consent_repo, audit_service=audit_service)


@pytest.fixture
def assignment_service(
    assignment_repo: AssignmentRepository,
    user_repo: UserRepository,
    audit_service: AuditService,
) -> AssignmentService:
    return AssignmentService(
        assignment_repo=assignment_repo,
        user_repo=user_repo,
        audit_service=audit_service,
    )


@pytest.fixture
def session_service(
    session_repo: SessionRepository,
    consent_repo: ConsentRepository,
    assignment_repo: AssignmentRepository,
    audit_service: AuditService,
) -> SessionService:
    return SessionService(
        session_repo=session_repo,
        consent_repo=consent_repo,
        assignment_repo=assignment_repo,
        audit_service=audit_service,
    )


def make_user_row(
    *,
    role: UserRole,
    email: str | None = None,
    full_name: str = "Test User",
    is_active: bool = True,
    password_hash: str = "fake-bcrypt-hash",
    auth_provider: AuthProvider = AuthProvider.LOCAL,
) -> dict[str, Any]:
    """Build a complete users row suitable for direct seeding into FakeSupabase."""
    now = datetime.now(UTC).isoformat()
    user_id = str(uuid4())
    return {
        "id": user_id,
        "auth_user_id": None,
        "email": email or f"{role.value}-{user_id[:8]}@example.com",
        "full_name": full_name,
        "role": role.value,
        "auth_provider": auth_provider.value,
        "provider_user_id": None,
        "avatar_url": None,
        "is_active": is_active,
        "password_hash": password_hash,
        "created_at": now,
        "updated_at": now,
    }


def make_token(
    *,
    user_id: str = "user-id-1",
    email: str = "user@example.com",
    role: UserRole = UserRole.PATIENT,
    expires_in_seconds: int = 60,
) -> str:
    """Mint a signed JWT for API-layer tests, using the same secret as production."""
    exp = int((datetime.now(UTC) + timedelta(seconds=expires_in_seconds)).timestamp())
    payload = {"sub": user_id, "email": email, "role": role.value, "exp": exp}
    return str(
        jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        ),
    )


def auth_headers(
    *,
    user_id: str = "user-id-1",
    email: str = "user@example.com",
    role: UserRole = UserRole.PATIENT,
) -> dict[str, str]:
    """Build a Bearer Authorization header for the given identity."""
    return {"Authorization": f"Bearer {make_token(user_id=user_id, email=email, role=role)}"}


@pytest.fixture
def client(fake_db: FakeSupabase) -> Iterator[TestClient]:
    """FastAPI TestClient with FakeSupabase wired into every repo via DI override.

    The `fake_db` fixture is shared with the same test, so seeding rows in
    `fake_db` is visible from inside the API call's repo lookups.

    ``AuthService._pending_tokens`` is a class-level dict shared across
    request-scoped instances, so it is cleared per test to prevent
    tokens minted by one test from leaking into another.
    """
    AuthService._pending_tokens.clear()
    app.dependency_overrides[get_supabase] = lambda: fake_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_supabase, None)
        AuthService._pending_tokens.clear()
