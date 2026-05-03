from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError, UnauthorizedError


class CurrentUserClaims(BaseModel):
    """Validated user claims extracted from an access token."""

    user_id: str
    email: str
    role: UserRole


def decode_access_token(token: str) -> CurrentUserClaims:
    """Decode and validate an access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc

    subject = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")

    if not isinstance(subject, str) or not subject:
        raise UnauthorizedError("Access token is missing subject")

    if not isinstance(email, str) or not email:
        raise UnauthorizedError("Access token is missing email")

    if not isinstance(role, str) or not role:
        raise UnauthorizedError("Access token is missing role")

    try:
        user_role = UserRole(role)
    except ValueError as exc:
        raise UnauthorizedError("Access token has invalid role") from exc

    return CurrentUserClaims(
        user_id=subject,
        email=email,
        role=user_role,
    )


def require_roles(
    current_user: CurrentUserClaims,
    allowed_roles: set[UserRole],
) -> None:
    """Raise ForbiddenError if current user role is not allowed."""
    if current_user.role not in allowed_roles:
        allowed_role_values = ", ".join(sorted(role.value for role in allowed_roles))
        raise ForbiddenError(
            f"Requires one of these roles: {allowed_role_values}",
        )


def require_admin(current_user: CurrentUserClaims) -> None:
    """Require the current user to be an admin."""
    require_roles(current_user, {UserRole.ADMIN})


def require_doctor(current_user: CurrentUserClaims) -> None:
    """Require the current user to be a doctor."""
    require_roles(current_user, {UserRole.DOCTOR})


def require_patient(current_user: CurrentUserClaims) -> None:
    """Require the current user to be a patient."""
    require_roles(current_user, {UserRole.PATIENT})
