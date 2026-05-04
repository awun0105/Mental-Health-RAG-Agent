"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from app.core.constants import AuthProvider, UserRole
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.user_repo import UserRepository
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.consent_service import ConsentService
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
def audit_service(audit_repo: AuditRepository) -> AuditService:
    return AuditService(audit_repo=audit_repo)


@pytest.fixture
def auth_service(user_repo: UserRepository) -> AuthService:
    return AuthService(user_repo=user_repo)


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
