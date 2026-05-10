"""Tests for ``AuthorizationService.require_permission`` and the cache."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.exceptions import ForbiddenError
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.permission_repo import PermissionRepository
from app.services.authorization_service import AuthorizationService

from tests.conftest import seed_rbac_tables
from tests.fakes.fake_supabase import FakeSupabase


def _make_authorization_service(
    fake_db: FakeSupabase,
    *,
    cache_ttl_seconds: int = 300,
) -> AuthorizationService:
    AuthorizationService.clear_cache()
    return AuthorizationService(
        permission_repo=PermissionRepository(db=fake_db),  # type: ignore[arg-type]
        assignment_repo=AssignmentRepository(db=fake_db),  # type: ignore[arg-type]
        cache_ttl_seconds=cache_ttl_seconds,
    )


@pytest.mark.asyncio
async def test_require_permission_passes_for_admin_role(
    fake_db: FakeSupabase,
) -> None:
    """An admin user resolves the full admin permission set via RPC."""
    user_id = str(uuid4())
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, "admin")])
    authz = _make_authorization_service(fake_db)

    await authz.require_permission(user_id, "assignment:create")
    await authz.require_permission(user_id, "role:assign")
    await authz.require_permission(user_id, "session:read")


@pytest.mark.asyncio
async def test_require_permission_raises_when_role_lacks_permission(
    fake_db: FakeSupabase,
) -> None:
    """A patient user must not have ``assignment:create``."""
    user_id = str(uuid4())
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, "patient")])
    authz = _make_authorization_service(fake_db)

    with pytest.raises(ForbiddenError) as exc_info:
        await authz.require_permission(user_id, "assignment:create")

    assert "assignment:create" in str(exc_info.value)


@pytest.mark.asyncio
async def test_require_permission_raises_for_user_with_no_roles(
    fake_db: FakeSupabase,
) -> None:
    """A user that doesn't yet exist in ``user_roles`` resolves to no permissions."""
    seed_rbac_tables(fake_db)
    authz = _make_authorization_service(fake_db)

    with pytest.raises(ForbiddenError):
        await authz.require_permission(str(uuid4()), "auth:me")


@pytest.mark.asyncio
async def test_get_user_permissions_caches_results(fake_db: FakeSupabase) -> None:
    """Repeated lookups within the TTL must not re-query the underlying RPC."""
    user_id = str(uuid4())
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, "patient")])
    authz = _make_authorization_service(fake_db)

    first = await authz.get_user_permissions(user_id)

    fake_db.tables["user_roles"] = []
    fake_db.tables["role_permissions"] = []

    second = await authz.get_user_permissions(user_id)

    assert first == second
    assert "session:read" in second


@pytest.mark.asyncio
async def test_invalidate_cache_forces_refresh(fake_db: FakeSupabase) -> None:
    """``invalidate_cache`` drops the entry so the next call re-queries the RPC."""
    user_id = str(uuid4())
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, "patient")])
    authz = _make_authorization_service(fake_db)

    await authz.get_user_permissions(user_id)

    fake_db.tables["user_roles"] = []
    fake_db.tables["role_permissions"] = []
    authz.invalidate_cache(user_id)

    refreshed = await authz.get_user_permissions(user_id)
    assert refreshed == set()


@pytest.mark.asyncio
async def test_cache_expires_after_ttl(fake_db: FakeSupabase) -> None:
    """A stale cache entry must be ignored once the TTL has passed."""
    user_id = str(uuid4())
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, "patient")])
    authz = _make_authorization_service(fake_db, cache_ttl_seconds=300)

    await authz.get_user_permissions(user_id)

    AuthorizationService._cache[user_id] = (
        AuthorizationService._cache[user_id][0],
        datetime.now(UTC) - timedelta(seconds=600),
    )

    fake_db.tables["user_roles"] = []
    fake_db.tables["role_permissions"] = []

    refreshed = await authz.get_user_permissions(user_id)
    assert refreshed == set()


@pytest.mark.asyncio
async def test_user_with_multiple_roles_inherits_union(
    fake_db: FakeSupabase,
) -> None:
    """A user holding both ``patient`` and ``doctor`` resolves the union of permissions."""
    user_id = str(uuid4())
    seed_rbac_tables(
        fake_db,
        user_role_pairs=[(user_id, "patient"), (user_id, "doctor")],
    )
    authz = _make_authorization_service(fake_db)

    permissions = await authz.get_user_permissions(user_id)

    assert "session:create" in permissions
    assert "session:close" in permissions
    assert "patient:read" in permissions
    assert "assignment:read" in permissions
    assert "assignment:create" not in permissions
