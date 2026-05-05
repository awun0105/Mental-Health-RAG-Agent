import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from supabase import Client

from app.core.config import settings
from app.core.constants import AuditAction, AuthProvider, UserRole
from app.core.exceptions import (
    AlreadyExistsError,
    DatabaseError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.db.repositories.base import JSONRow, JSONValue
from app.db.repositories.user_repo import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.audit_service import AuditService

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for local + Google authentication and JWT minting.

    Google OAuth uses Supabase as a proxy: ``sign_in_with_oauth`` returns
    a Google login URL, and after the user completes the Google flow
    Supabase redirects back to the backend callback. ``handle_google_callback``
    exchanges the Supabase auth code for a Supabase session, then maps
    the Supabase user onto a row in the application's ``users`` table.

    Account linking policy is **Verify-first**: if a Google login arrives
    for an email that already has a local password account, the login is
    rejected. The user must first log in with their password and then
    explicitly link Google through a separate (future) endpoint.
    """

    # _pending_tokens stores app JWTs keyed by short-lived one-time auth
    # codes. The Supabase callback redirects the browser to the frontend
    # with this auth code in the query string; the frontend then POSTs it
    # to /auth/google/exchange to trade it for the actual JWT, so the JWT
    # never appears in a URL or browser history.
    #
    # ClassVar so it's shared across request-scoped AuthService instances
    # within the same process. Production deployments running multiple
    # processes need a shared store (e.g. Redis), but the MVP is single
    # process. Tokens have a short TTL and are popped on first use.
    _pending_tokens: ClassVar[dict[str, tuple[TokenResponse, datetime]]] = {}
    _PENDING_TOKEN_TTL_SECONDS: ClassVar[int] = 60

    def __init__(
        self,
        user_repo: UserRepository,
        supabase: Client,
        audit_service: AuditService,
    ) -> None:
        self._user_repo = user_repo
        self._supabase = supabase
        self._audit_service = audit_service

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

    # ─── Google OAuth ────────────────────────────────────────────────────────

    def get_google_oauth_url(self) -> str:
        """Return the Google OAuth URL via Supabase's OAuth proxy.

        Supabase generates a URL with the appropriate ``client_id`` and
        scopes for the configured Google provider. After the user signs
        in on Google, Supabase redirects to ``redirect_to`` with a one
        time auth code that the backend exchanges below.
        """
        callback_url = f"{settings.backend_url}/api/v1/auth/google/callback"
        try:
            response = self._supabase.auth.sign_in_with_oauth(
                {
                    "provider": "google",
                    "options": {"redirect_to": callback_url},
                },
            )
        except Exception as exc:
            raise DatabaseError("Failed to generate Google OAuth URL") from exc

        url = getattr(response, "url", None)
        if not isinstance(url, str) or not url:
            raise DatabaseError("Supabase returned no Google OAuth URL")
        return url

    async def handle_google_callback(self, code: str) -> tuple[str, str]:
        """Exchange a Supabase auth code, resolve the user, return a one-time auth code.

        Steps:

        1. Exchange the Supabase auth code for a Supabase session and user.
        2. Lookup the application user by ``(provider=google, provider_user_id=sub)``.
        3. If not found, lookup by email:
           - If a local password account exists with that email, reject
             the login (Verify-first policy). The user must log in with
             their password first and then link Google explicitly.
           - If a different Google account already owns the email, also reject.
           - Otherwise, create a new patient user with ``auth_provider=google``.
        4. Mint an application JWT, audit the login, store the JWT in
           ``_pending_tokens`` keyed by a fresh one-time auth code, and
           return the auth code plus the user's display name so the
           callback route can build a redirect URL for the frontend.
        """
        supabase_user = self._exchange_supabase_code(code)
        google_email = supabase_user.email
        google_sub = supabase_user.id
        if not isinstance(google_email, str) or not google_email:
            raise DatabaseError("Supabase user has no email")
        if not isinstance(google_sub, str) or not google_sub:
            raise DatabaseError("Supabase user has no id")

        metadata: dict[str, Any] = {}
        raw_metadata = getattr(supabase_user, "user_metadata", None)
        if isinstance(raw_metadata, dict):
            metadata = raw_metadata

        existing = await self._user_repo.get_by_provider_identity(
            AuthProvider.GOOGLE,
            google_sub,
        )

        if existing is not None:
            user = self._row_to_user_response(existing)
        else:
            user = await self._create_or_reject_google_user(
                email=google_email,
                google_sub=google_sub,
                metadata=metadata,
            )

        # Mirror the local-login is_active guard (auth_service.login above).
        # Without this, a user deactivated by an admin can simply complete
        # the Google OAuth dance again and silently regain a valid app JWT,
        # bypassing the admin's ability to revoke access.
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")

        access_token = self.create_access_token(
            subject=user.id,
            email=str(user.email),
            role=user.role.value,
        )
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user,
        )

        await self._audit_service.log_event(
            user_id=user.id,
            role=user.role.value,
            action=AuditAction.USER_LOGIN,
            resource_type="user",
            resource_id=user.id,
            metadata={"method": "google"},
        )

        auth_code = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(
            seconds=self._PENDING_TOKEN_TTL_SECONDS,
        )
        AuthService._pending_tokens[auth_code] = (token_response, expires_at)

        return (auth_code, user.full_name)

    def exchange_auth_code(self, auth_code: str) -> TokenResponse:
        """Trade a one-time auth code for the underlying app JWT.

        The auth code is single-use and short-lived (60s). On any miss —
        unknown code, expired entry, or already-used code — raise
        ``UnauthorizedError`` with a generic message so an attacker
        cannot distinguish the cases.
        """
        self._sweep_expired_pending_tokens()
        entry = AuthService._pending_tokens.pop(auth_code, None)
        if entry is None:
            raise UnauthorizedError("Invalid or expired auth code")
        token_response, expires_at = entry
        if datetime.now(UTC) > expires_at:
            raise UnauthorizedError("Invalid or expired auth code")
        return token_response

    def _exchange_supabase_code(self, code: str) -> Any:
        """Wrap supabase auth.exchange_code_for_session with our error type.

        ``CodeExchangeParams`` is a strict TypedDict that requires
        ``auth_code``, ``code_verifier``, and ``redirect_to``. The PKCE
        verifier is only used when initiating the flow client-side; for
        a server-initiated flow it falls back to storage at runtime, so
        an empty string is safe here. ``redirect_to`` mirrors the URL
        passed to ``sign_in_with_oauth``.
        """
        callback_url = f"{settings.backend_url}/api/v1/auth/google/callback"
        try:
            session_response = self._supabase.auth.exchange_code_for_session(
                {
                    "auth_code": code,
                    "code_verifier": "",
                    "redirect_to": callback_url,
                },
            )
        except Exception as exc:
            raise UnauthorizedError("Google login failed") from exc

        supabase_user = getattr(session_response, "user", None)
        if supabase_user is None:
            raise UnauthorizedError("Google login failed")
        return supabase_user

    async def _create_or_reject_google_user(
        self,
        *,
        email: str,
        google_sub: str,
        metadata: dict[str, Any],
    ) -> UserResponse:
        """Create a new Google user, or reject if email collides (Verify-first)."""
        existing_by_email = await self._user_repo.get_by_email(email)
        if existing_by_email is not None:
            existing_provider = existing_by_email.get("auth_provider")
            if existing_provider == AuthProvider.LOCAL.value:
                raise AlreadyExistsError(
                    resource="Email",
                    identifier=(
                        f"{email} (registered with password — log in with "
                        "password and link Google from your profile)"
                    ),
                )
            raise AlreadyExistsError(
                resource="Email",
                identifier=f"{email} (already linked to another Google account)",
            )

        full_name = self._extract_full_name(metadata, fallback=email)
        avatar_url = self._extract_avatar_url(metadata)

        new_user_data: JSONRow = {
            "email": email,
            "password_hash": None,
            "full_name": full_name,
            "role": UserRole.PATIENT.value,
            "auth_provider": AuthProvider.GOOGLE.value,
            "provider_user_id": google_sub,
            "avatar_url": avatar_url,
            "is_active": True,
        }
        user = await self._user_repo.create(new_user_data)

        await self._audit_service.log_event(
            user_id=user.id,
            role=user.role.value,
            action=AuditAction.USER_REGISTERED,
            resource_type="user",
            resource_id=user.id,
            metadata={"method": "google"},
        )
        return user

    @staticmethod
    def _extract_full_name(metadata: dict[str, Any], *, fallback: str) -> str:
        """Pick the best display name from Google's user_metadata payload."""
        for key in ("full_name", "name"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return fallback

    @staticmethod
    def _extract_avatar_url(metadata: dict[str, Any]) -> str | None:
        """Pick the avatar URL from Google's user_metadata payload."""
        for key in ("avatar_url", "picture"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    @classmethod
    def _sweep_expired_pending_tokens(cls) -> None:
        """Drop expired entries so the in-memory store doesn't grow unboundedly."""
        now = datetime.now(UTC)
        expired = [code for code, (_, exp) in cls._pending_tokens.items() if now > exp]
        for code in expired:
            cls._pending_tokens.pop(code, None)

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
