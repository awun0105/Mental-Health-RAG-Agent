"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
from app.api.dependencies import (
    get_authorization_service,
    get_current_user,
    get_supabase,
)
from app.core.config import settings
from app.core.constants import AuthProvider, UserRole
from app.core.exceptions import ForbiddenError
from app.core.security import CurrentUserClaims
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.message_repo import MessageRepository
from app.db.repositories.permission_repo import PermissionRepository
from app.db.repositories.role_permission_repo import RolePermissionRepository
from app.db.repositories.role_repo import RoleRepository
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.user_repo import UserRepository
from app.db.repositories.user_role_repo import UserRoleRepository
from app.main import app
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.authorization_service import AuthorizationService
from app.services.consent_service import ConsentService
from app.services.session_service import SessionService
from fastapi import Depends
from fastapi.testclient import TestClient
from jose import jwt

from supabase import Client
from tests.fakes.fake_supabase import FakeSupabase

# Mirror the seed mapping in ``supabase/seeds/202605110003_rbac_seed.sql``. Keep this in sync
# with that file; deviating will silently break route-level RBAC tests.
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    UserRole.ADMIN.value: {
        "auth:me",
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
        "role:read",
        "role:assign",
        "permission:read",
        "permission:assign",
        "assignment:create",
        "assignment:read",
        "assignment:deactivate",
        "session:create",
        "session:read",
        "session:close",
        "patient:read",
        "consent:accept",
        "consent:read_status",
    },
    UserRole.DOCTOR.value: {
        "auth:me",
        "assignment:read",
        "session:read",
        "patient:read",
        "consent:read_status",
    },
    UserRole.PATIENT.value: {
        "auth:me",
        "session:create",
        "session:read",
        "session:close",
        "consent:accept",
        "consent:read_status",
    },
}


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
def role_repo(fake_db: FakeSupabase) -> RoleRepository:
    return RoleRepository(db=cast(Client, fake_db))


@pytest.fixture
def permission_repo(fake_db: FakeSupabase) -> PermissionRepository:
    return PermissionRepository(db=cast(Client, fake_db))


@pytest.fixture
def user_role_repo(fake_db: FakeSupabase) -> UserRoleRepository:
    return UserRoleRepository(db=cast(Client, fake_db))


@pytest.fixture
def role_permission_repo(fake_db: FakeSupabase) -> RolePermissionRepository:
    return RolePermissionRepository(db=cast(Client, fake_db))


@pytest.fixture
def message_repo(fake_db: FakeSupabase) -> MessageRepository:
    return MessageRepository(db=cast(Client, fake_db))


@pytest.fixture
def audit_service(audit_repo: AuditRepository) -> AuditService:
    return AuditService(audit_repo=audit_repo)


@pytest.fixture
def auth_service(
    user_repo: UserRepository,
    role_repo: RoleRepository,
    user_role_repo: UserRoleRepository,
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
    seed_rbac_tables(fake_db)
    return AuthService(
        user_repo=user_repo,
        supabase=cast(Client, fake_db),
        audit_service=audit_service,
        role_repo=role_repo,
        user_role_repo=user_role_repo,
    )


class _NullAuthzService:
    """Trivial AuthorizationService stand-in for tests that don't seed RBAC.

    Tests that pre-date Phase 6 PR A typically don't seed ``user_roles``
    rows, so the production ``AuthorizationService`` would resolve an
    empty role set for the actor. This stub returns an empty role set
    everywhere — consent acceptance / chat session lifecycle tests then
    assert their own concerns without depending on the role-name pipeline.
    Tests that DO want to exercise the role-name pipeline either build
    ``AuthorizationService`` directly via the ``authorization_service``
    fixture, or call ``seed_rbac_tables`` and route through the API.
    """

    async def get_user_role_names(self, user_id: str) -> set[str]:
        return set()

    async def get_primary_role_name(self, user_id: str) -> str | None:
        return None

    def invalidate_cache(self, user_id: str) -> None:
        return None


@pytest.fixture
def null_authz_service() -> _NullAuthzService:
    return _NullAuthzService()


@pytest.fixture
def consent_service(
    consent_repo: ConsentRepository,
    audit_service: AuditService,
    null_authz_service: _NullAuthzService,
) -> ConsentService:
    return ConsentService(
        consent_repo=consent_repo,
        audit_service=audit_service,
        authorization_service=cast(AuthorizationService, null_authz_service),
    )


@pytest.fixture
def authorization_service(
    permission_repo: PermissionRepository,
    user_role_repo: UserRoleRepository,
) -> AuthorizationService:
    AuthorizationService.clear_cache()
    return AuthorizationService(
        permission_repo=permission_repo,
        user_role_repo=user_role_repo,
    )


@pytest.fixture
def assignment_service(
    assignment_repo: AssignmentRepository,
    user_repo: UserRepository,
    audit_service: AuditService,
    authorization_service: AuthorizationService,
) -> AssignmentService:
    return AssignmentService(
        assignment_repo=assignment_repo,
        user_repo=user_repo,
        audit_service=audit_service,
        authorization_service=authorization_service,
    )


@pytest.fixture
def session_service(
    session_repo: SessionRepository,
    consent_repo: ConsentRepository,
    assignment_repo: AssignmentRepository,
    audit_service: AuditService,
    authorization_service: AuthorizationService,
) -> SessionService:
    return SessionService(
        session_repo=session_repo,
        consent_repo=consent_repo,
        assignment_repo=assignment_repo,
        audit_service=audit_service,
        authorization_service=authorization_service,
    )


@pytest.fixture
def consent_service_with_authz(
    consent_repo: ConsentRepository,
    audit_service: AuditService,
    authorization_service: AuthorizationService,
) -> ConsentService:
    """ConsentService wired with the production AuthorizationService.

    The default ``consent_service`` fixture is used by tests written
    against the legacy signature; this variant exercises the Phase 6
    PR A pipeline (resolves the actor's role from ``user_roles``).
    """
    return ConsentService(
        consent_repo=consent_repo,
        audit_service=audit_service,
        authorization_service=authorization_service,
    )


class _RoleBasedAuthzService:
    """Test-only AuthorizationService that resolves perms from the JWT role.

    Production resolves permissions and role names through Supabase
    RPCs; that requires seeded ``user_roles`` for every test user. Most
    route-level tests only care about the ``admin / doctor / patient``
    triad and don't seed RBAC tables — this stand-in mirrors the
    canonical seed mapping so the tests stay focused on route logic.
    Tests that exercise the real authorization pipeline (e.g.
    ``test_authorization_service.py``) construct ``AuthorizationService``
    directly and bypass this stub.
    """

    def __init__(self, role: str) -> None:
        self._role = role

    async def get_user_permissions(self, user_id: str) -> set[str]:
        return set(_ROLE_PERMISSIONS.get(self._role, set()))

    async def require_permission(
        self,
        user_id: str,
        permission_code: str,
    ) -> None:
        permissions = await self.get_user_permissions(user_id)
        if permission_code not in permissions:
            raise ForbiddenError(f"Missing permission: {permission_code}")

    async def get_user_role_names(self, user_id: str) -> set[str]:
        return {self._role}

    async def get_primary_role_name(self, user_id: str) -> str | None:
        return self._role

    def invalidate_cache(self, user_id: str) -> None:
        return None


def _fake_role_based_authz_service(
    current_user: CurrentUserClaims = Depends(get_current_user),  # type: ignore[assignment]
) -> _RoleBasedAuthzService:
    return _RoleBasedAuthzService(role=current_user.role.value)


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

    ``get_authorization_service`` is overridden with a JWT-role-based
    stub (``_RoleBasedAuthzService``) so route-level tests do not need
    to seed the full RBAC tables to satisfy ``require_permission``.
    Tests that exercise the production authorization pipeline construct
    ``AuthorizationService`` directly via the ``authorization_service``
    fixture instead of going through this client.
    """
    AuthService._pending_tokens.clear()
    AuthorizationService.clear_cache()
    app.dependency_overrides[get_supabase] = lambda: fake_db
    app.dependency_overrides[get_authorization_service] = _fake_role_based_authz_service
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_supabase, None)
        app.dependency_overrides.pop(get_authorization_service, None)
        AuthService._pending_tokens.clear()
        AuthorizationService.clear_cache()


def seed_rbac_tables(
    fake_db: FakeSupabase,
    *,
    user_role_pairs: list[tuple[str, str]] | None = None,
) -> dict[str, dict[str, str]]:
    """Seed the ``roles`` / ``permissions`` / ``role_permissions`` tables.

    Returns a mapping ``{"roles": {name: id}, "permissions": {code: id}}``
    so callers can wire ``user_roles`` rows for specific test users.

    ``user_role_pairs`` is an optional list of ``(user_id, role_name)``
    tuples that get materialised into ``user_roles`` immediately, which
    is useful when the test exercises the production authorization
    pipeline against ``FakeSupabase``.
    """
    role_rows = [
        {
            "id": str(uuid4()),
            "name": name,
            "display_name": name.title(),
            "description": None,
            "is_system": True,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        for name in ("admin", "doctor", "patient")
    ]
    role_id_by_name = {row["name"]: row["id"] for row in role_rows}

    all_codes = sorted({c for codes in _ROLE_PERMISSIONS.values() for c in codes})
    permission_rows = [
        {
            "id": str(uuid4()),
            "code": code,
            "module": code.split(":", 1)[0],
            "action": code.split(":", 1)[1] if ":" in code else code,
            "description": None,
            "created_at": datetime.now(UTC).isoformat(),
        }
        for code in all_codes
    ]
    perm_id_by_code = {row["code"]: row["id"] for row in permission_rows}

    role_permission_rows: list[dict[str, Any]] = []
    for role_name, codes in _ROLE_PERMISSIONS.items():
        role_id = role_id_by_name[role_name]
        for code in codes:
            role_permission_rows.append(
                {
                    "role_id": role_id,
                    "permission_id": perm_id_by_code[code],
                    "granted_by": None,
                    "granted_at": datetime.now(UTC).isoformat(),
                },
            )

    fake_db.tables.setdefault("roles", []).extend(role_rows)
    fake_db.tables.setdefault("permissions", []).extend(permission_rows)
    fake_db.tables.setdefault("role_permissions", []).extend(role_permission_rows)

    if user_role_pairs:
        user_role_rows = [
            {
                "user_id": user_id,
                "role_id": role_id_by_name[role_name],
                "assigned_by": None,
                "assigned_at": datetime.now(UTC).isoformat(),
            }
            for user_id, role_name in user_role_pairs
        ]
        fake_db.tables.setdefault("user_roles", []).extend(user_role_rows)

    return {"roles": role_id_by_name, "permissions": perm_id_by_code}
