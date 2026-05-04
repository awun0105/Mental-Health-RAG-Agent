"""Tests for JWT decoding and role-based access checks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.core.config import settings
from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import (
    CurrentUserClaims,
    decode_access_token,
    require_roles,
)
from jose import jwt


def _make_token(
    *,
    subject: str = "user-123",
    email: str = "doc@example.com",
    role: str = UserRole.DOCTOR.value,
    expires_in_seconds: int = 60,
) -> str:
    exp = int((datetime.now(UTC) + timedelta(seconds=expires_in_seconds)).timestamp())
    payload = {"sub": subject, "email": email, "role": role, "exp": exp}
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def test_decode_access_token_with_valid_token_returns_claims() -> None:
    """Valid token decodes to claims with user_id, email and parsed role enum."""
    token = _make_token(
        subject="abc-123",
        email="doc@example.com",
        role=UserRole.DOCTOR.value,
    )

    claims = decode_access_token(token)

    assert claims.user_id == "abc-123"
    assert claims.email == "doc@example.com"
    assert claims.role is UserRole.DOCTOR


def test_decode_access_token_with_expired_token_raises_unauthorized() -> None:
    """Expired tokens must surface as 401 UnauthorizedError, not as JWTError."""
    token = _make_token(expires_in_seconds=-10)

    with pytest.raises(UnauthorizedError):
        decode_access_token(token)


def test_require_roles_allows_member() -> None:
    """`require_roles` is a no-op when the current role is in the allowed set."""
    claims = CurrentUserClaims(user_id="u", email="d@x.com", role=UserRole.DOCTOR)

    # Should not raise.
    require_roles(claims, {UserRole.DOCTOR, UserRole.ADMIN})


def test_require_roles_rejects_non_member() -> None:
    """`require_roles` raises ForbiddenError listing the allowed roles."""
    claims = CurrentUserClaims(user_id="u", email="p@x.com", role=UserRole.PATIENT)

    with pytest.raises(ForbiddenError) as excinfo:
        require_roles(claims, {UserRole.DOCTOR, UserRole.ADMIN})

    assert "doctor" in excinfo.value.message
    assert "admin" in excinfo.value.message
