"""Tests for ``PermissionRepository.get_permission_codes_for_user`` (RPC path)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.db.repositories.permission_repo import PermissionRepository

from tests.conftest import seed_rbac_tables
from tests.fakes.fake_supabase import FakeSupabase


@pytest.mark.asyncio
async def test_get_permission_codes_for_user_returns_admin_set(
    fake_db: FakeSupabase,
    permission_repo: PermissionRepository,
) -> None:
    """Admin user resolves the full admin permission code set."""
    user_id = str(uuid4())
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, "admin")])

    codes = set(await permission_repo.get_permission_codes_for_user(user_id))

    assert "assignment:create" in codes
    assert "role:assign" in codes
    assert "permission:assign" in codes
    assert "user:create" in codes


@pytest.mark.asyncio
async def test_get_permission_codes_for_user_returns_patient_set(
    fake_db: FakeSupabase,
    permission_repo: PermissionRepository,
) -> None:
    """Patient user resolves only the seeded patient permissions."""
    user_id = str(uuid4())
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, "patient")])

    codes = set(await permission_repo.get_permission_codes_for_user(user_id))

    assert codes == {
        "auth:me",
        "session:create",
        "session:read",
        "session:close",
        "message:create",
        "message:read",
        "consent:accept",
        "consent:read_status",
    }


@pytest.mark.asyncio
async def test_get_permission_codes_for_user_returns_empty_for_unknown_user(
    fake_db: FakeSupabase,
    permission_repo: PermissionRepository,
) -> None:
    """A user with no ``user_roles`` row resolves to an empty list."""
    seed_rbac_tables(fake_db)

    codes = await permission_repo.get_permission_codes_for_user(str(uuid4()))

    assert codes == []


@pytest.mark.asyncio
async def test_get_permission_codes_for_user_dedupes_overlap(
    fake_db: FakeSupabase,
    permission_repo: PermissionRepository,
) -> None:
    """A user holding overlapping roles still gets each code once."""
    user_id = str(uuid4())
    seed_rbac_tables(
        fake_db,
        user_role_pairs=[(user_id, "patient"), (user_id, "doctor")],
    )

    codes = await permission_repo.get_permission_codes_for_user(user_id)

    assert codes.count("session:read") == 1
    assert codes.count("consent:read_status") == 1


@pytest.mark.asyncio
async def test_list_all_returns_seeded_permissions(
    fake_db: FakeSupabase,
    permission_repo: PermissionRepository,
) -> None:
    """``list_all`` surfaces every seeded permission row."""
    seed_rbac_tables(fake_db)

    results = await permission_repo.list_all()
    codes = {p.code for p in results}

    assert "auth:me" in codes
    assert "role:assign" in codes
    assert "session:create" in codes
