from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import AuthProvider, UserRole


class UserCreate(BaseModel):
    """Internal schema for creating any application user.

    This schema is used by privileged code paths (admin user provisioning,
    OAuth user creation) where the role is chosen by the caller, not by
    the end user. Public self-registration must NOT use this schema; it
    must use ``PublicUserRegister`` which has no ``role`` field.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.PATIENT


class PublicUserRegister(BaseModel):
    """Public self-registration schema for the ``/auth/register`` endpoint.

    Only patients may self-register. Doctor and admin accounts must be
    provisioned through admin-only flows (out of scope for this schema).
    The ``role`` field is intentionally absent to prevent privilege
    escalation via the public endpoint.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    """Request schema for local email/password login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class GoogleExchangeRequest(BaseModel):
    """Request schema for exchanging a one-time Google OAuth code for an app JWT."""

    auth_code: str = Field(min_length=1)


class UserResponse(BaseModel):
    """Public user response schema.

    Never include password_hash in this model.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    auth_user_id: str | None = None
    email: EmailStr
    full_name: str
    role: UserRole
    auth_provider: AuthProvider
    provider_user_id: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """JWT response returned after successful login/OAuth exchange."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
