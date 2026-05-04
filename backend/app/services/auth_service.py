from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.core.config import settings
from app.core.constants import AuthProvider
from app.core.exceptions import (
    AlreadyExistsError,
    DatabaseError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.db.repositories.base import JSONRow, JSONValue
from app.db.repositories.user_repo import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for local authentication and JWT creation."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def register(self, payload: UserCreate) -> UserResponse:
        """Register a local user."""
        email_exists = await self._user_repo.email_exists(payload.email)
        if email_exists:
            raise AlreadyExistsError(resource="User", identifier=payload.email)

        password_hash = self.hash_password(payload.password)

        user_data: JSONRow = {
            "email": str(payload.email),
            "password_hash": password_hash,
            "full_name": payload.full_name,
            "role": payload.role.value,
            "auth_provider": AuthProvider.LOCAL.value,
            "is_active": True,
        }

        return await self._user_repo.create(user_data)

    async def login(self, payload: UserLogin) -> TokenResponse:
        """Login a local user and return an access token."""
        user_row = await self._user_repo.get_by_email(str(payload.email))
        if user_row is None:
            raise InvalidCredentialsError()

        password_hash = user_row.get("password_hash")
        if not isinstance(password_hash, str) or not password_hash:
            raise DatabaseError("User row missing password_hash")

        if not self.verify_password(payload.password, password_hash):
            raise InvalidCredentialsError()

        is_active = user_row.get("is_active")
        if not isinstance(is_active, bool):
            raise DatabaseError("User row missing is_active")
        if not is_active:
            raise UnauthorizedError("User account is inactive")

        user = self._row_to_user_response(user_row)

        access_token = self.create_access_token(
            subject=user.id,
            email=str(user.email),
            role=user.role.value,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user,
        )

    def hash_password(self, password: str) -> str:
        """Hash a plain-text password."""
        return str(password_context.hash(password))

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        """Verify a plain-text password against a password hash."""
        return bool(password_context.verify(plain_password, password_hash))

    def create_access_token(
        self,
        subject: str,
        email: str,
        role: str,
    ) -> str:
        """Create a signed JWT access token."""
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.jwt_expiration_minutes,
        )

        payload: dict[str, JSONValue] = {
            "sub": subject,
            "email": email,
            "role": role,
            "exp": int(expires_at.timestamp()),
        }

        return str(
            jwt.encode(
                payload,
                settings.jwt_secret_key,
                algorithm=settings.jwt_algorithm,
            ),
        )

    def _row_to_user_response(self, row: JSONRow) -> UserResponse:
        """Convert a raw users row into a public user response.

        Wraps Pydantic validation errors as DatabaseError so a malformed
        row from Supabase surfaces as a 500 with a clear message instead
        of a raw validation traceback.
        """
        try:
            return UserResponse.model_validate(dict(row))
        except ValidationError as exc:
            raise DatabaseError("Invalid user row shape") from exc
