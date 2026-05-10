"""Tests for AuthService register/login on top of FakeSupabase."""

from __future__ import annotations

import pytest
from app.core.constants import AuthProvider, UserRole
from app.core.exceptions import (
    AlreadyExistsError,
    DatabaseError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService

from tests.fakes.fake_supabase import FakeSupabase


async def test_register_creates_user_with_local_provider(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """Registration writes a users row with auth_provider=local and hashed password."""
    payload = UserCreate(
        email="patient@example.com",
        password="secret-password-123",
        full_name="Pat Patient",
        role=UserRole.PATIENT,
    )

    user = await auth_service.register(payload)

    assert user.email == "patient@example.com"
    assert user.role is UserRole.PATIENT
    assert user.auth_provider is AuthProvider.LOCAL
    assert user.is_active is True

    rows = fake_db.all_rows("users")
    assert len(rows) == 1
    assert rows[0]["password_hash"] != "secret-password-123"  # must be hashed
    assert rows[0]["password_hash"].startswith("$2")  # bcrypt prefix

    role_id_by_name = {row["name"]: row["id"] for row in fake_db.all_rows("roles")}
    user_roles = fake_db.all_rows("user_roles")
    assert any(
        row["user_id"] == user.id and row["role_id"] == role_id_by_name["patient"]
        for row in user_roles
    )


async def test_register_with_existing_email_raises_already_exists(
    auth_service: AuthService,
) -> None:
    """Registering twice with the same email surfaces a 409 AlreadyExistsError."""
    payload = UserCreate(
        email="dup@example.com",
        password="secret-password-123",
        full_name="Dup",
        role=UserRole.PATIENT,
    )

    await auth_service.register(payload)

    with pytest.raises(AlreadyExistsError):
        await auth_service.register(payload)


async def test_login_returns_token_for_valid_credentials(
    auth_service: AuthService,
) -> None:
    """A successful login returns a TokenResponse whose embedded user matches register."""
    register_payload = UserCreate(
        email="login@example.com",
        password="secret-password-123",
        full_name="Login User",
        role=UserRole.DOCTOR,
    )
    await auth_service.register(register_payload)

    token = await auth_service.login(
        UserLogin(email="login@example.com", password="secret-password-123"),
    )

    assert token.token_type == "bearer"
    assert token.access_token  # non-empty signed JWT
    assert token.user.email == "login@example.com"
    assert token.user.role is UserRole.DOCTOR


async def test_login_with_wrong_password_raises_invalid_credentials(
    auth_service: AuthService,
) -> None:
    """Wrong password raises InvalidCredentialsError, never DatabaseError."""
    await auth_service.register(
        UserCreate(
            email="wrongpw@example.com",
            password="correct-password-123",
            full_name="WrongPW",
            role=UserRole.PATIENT,
        ),
    )

    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            UserLogin(email="wrongpw@example.com", password="bad-password-000"),
        )


async def test_login_with_inactive_user_raises_unauthorized(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """Inactive users cannot log in even with the correct password."""
    await auth_service.register(
        UserCreate(
            email="inactive@example.com",
            password="secret-password-123",
            full_name="Inactive",
            role=UserRole.PATIENT,
        ),
    )

    # Soft-deactivate the user directly in the fake store.
    for row in fake_db.tables["users"]:
        if row["email"] == "inactive@example.com":
            row["is_active"] = False

    with pytest.raises(UnauthorizedError):
        await auth_service.login(
            UserLogin(email="inactive@example.com", password="secret-password-123"),
        )


async def test_login_with_missing_password_hash_raises_database_error(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """A user row missing password_hash is a DB shape problem, not an auth failure."""
    await auth_service.register(
        UserCreate(
            email="broken@example.com",
            password="secret-password-123",
            full_name="Broken",
            role=UserRole.PATIENT,
        ),
    )

    # Corrupt the row so password_hash is missing. This simulates a row
    # produced by a migration bug or by an OAuth user being mis-handled.
    for row in fake_db.tables["users"]:
        if row["email"] == "broken@example.com":
            row["password_hash"] = None

    with pytest.raises(DatabaseError):
        await auth_service.login(
            UserLogin(email="broken@example.com", password="secret-password-123"),
        )
