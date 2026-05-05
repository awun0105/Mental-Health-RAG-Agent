"""Service-level tests for the Google OAuth flow on AuthService.

These tests exercise the three new methods added in task DB-2.27 step A:

* ``get_google_oauth_url`` — wraps Supabase's OAuth proxy.
* ``handle_google_callback`` — exchanges a Supabase auth code, looks up
  or creates the application user, and stores the JWT under a one-time
  auth code.
* ``exchange_auth_code`` — trades the one-time auth code for the JWT.

The Verify-first account-linking policy is exercised here as well: a
Google login arriving for an email that already has a local password
account must be rejected so an attacker cannot take over the account by
controlling the matching Google address.
"""

from __future__ import annotations

import pytest
from app.core.config import settings
from app.core.constants import AuditAction, AuthProvider, UserRole
from app.core.exceptions import AlreadyExistsError, UnauthorizedError
from app.services.auth_service import AuthService
from jose import jwt

from tests.conftest import make_user_row
from tests.fakes.fake_supabase import FakeSupabase, make_fake_supabase_user


def test_get_google_oauth_url_returns_supabase_url(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """``get_google_oauth_url`` returns the URL the Supabase stub gave us."""
    fake_db.auth.next_oauth_url = "https://accounts.google.com/o/oauth2/auth?test=1"

    url = auth_service.get_google_oauth_url()

    assert url == "https://accounts.google.com/o/oauth2/auth?test=1"
    assert fake_db.auth.last_oauth_options is not None
    assert "redirect_to" in fake_db.auth.last_oauth_options
    assert fake_db.auth.last_oauth_options["redirect_to"].endswith(
        "/api/v1/auth/google/callback",
    )


@pytest.mark.asyncio
async def test_handle_google_callback_creates_new_patient_for_unknown_email(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """An unknown Google email becomes a new patient + USER_REGISTERED audit."""
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-001",
        email="newuser@example.com",
        full_name="New Google User",
    )

    auth_code, user_name = await auth_service.handle_google_callback("supabase-code")

    assert isinstance(auth_code, str) and auth_code
    assert user_name == "New Google User"

    users = fake_db.all_rows("users")
    assert len(users) == 1
    created = users[0]
    assert created["email"] == "newuser@example.com"
    assert created["auth_provider"] == AuthProvider.GOOGLE.value
    assert created["provider_user_id"] == "google-sub-001"
    assert created["role"] == UserRole.PATIENT.value
    assert created["password_hash"] is None

    audits = fake_db.all_rows("audit_logs")
    actions = [a["action"] for a in audits]
    assert AuditAction.USER_REGISTERED.value in actions
    assert AuditAction.USER_LOGIN.value in actions
    login_event = next(a for a in audits if a["action"] == AuditAction.USER_LOGIN.value)
    assert login_event["metadata"] == {"method": "google"}
    assert login_event["role"] == UserRole.PATIENT.value


@pytest.mark.asyncio
async def test_handle_google_callback_reuses_existing_google_user(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """A returning Google user reuses their existing row and only logs USER_LOGIN."""
    existing = make_user_row(
        role=UserRole.PATIENT,
        email="returning@example.com",
        full_name="Returning User",
        auth_provider=AuthProvider.GOOGLE,
        password_hash="",  # Google users have no password hash
    )
    existing["provider_user_id"] = "google-sub-002"
    fake_db.seed("users", [existing])
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-002",
        email="returning@example.com",
        full_name="Returning User",
    )

    auth_code, user_name = await auth_service.handle_google_callback("any-code")

    assert auth_code
    assert user_name == "Returning User"
    # The repo must NOT create a duplicate row for an existing Google identity.
    assert len(fake_db.all_rows("users")) == 1

    audits = fake_db.all_rows("audit_logs")
    actions = [a["action"] for a in audits]
    assert AuditAction.USER_REGISTERED.value not in actions
    assert actions.count(AuditAction.USER_LOGIN.value) == 1


@pytest.mark.asyncio
async def test_handle_google_callback_rejects_email_owned_by_local_account(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """Verify-first: reject Google login when email belongs to a local password account."""
    fake_db.seed(
        "users",
        [
            make_user_row(
                role=UserRole.PATIENT,
                email="conflict@example.com",
                full_name="Local Account",
                auth_provider=AuthProvider.LOCAL,
            ),
        ],
    )
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-003",
        email="conflict@example.com",
    )

    with pytest.raises(AlreadyExistsError) as excinfo:
        await auth_service.handle_google_callback("any-code")

    # The error message must steer the user toward password login + manual link,
    # not silently take over the existing account.
    assert "log in with password" in excinfo.value.message
    assert excinfo.value.status_code == 409

    # No user was created and no successful login was logged.
    users = fake_db.all_rows("users")
    assert len(users) == 1
    assert users[0]["auth_provider"] == AuthProvider.LOCAL.value
    audits = fake_db.all_rows("audit_logs")
    assert AuditAction.USER_LOGIN.value not in [a["action"] for a in audits]


@pytest.mark.asyncio
async def test_handle_google_callback_rejects_existing_google_email_with_different_sub(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """Defensive: same email already linked to a different Google sub must be rejected."""
    existing = make_user_row(
        role=UserRole.PATIENT,
        email="taken@example.com",
        auth_provider=AuthProvider.GOOGLE,
        password_hash="",
    )
    existing["provider_user_id"] = "google-sub-original"
    fake_db.seed("users", [existing])
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-imposter",
        email="taken@example.com",
    )

    with pytest.raises(AlreadyExistsError):
        await auth_service.handle_google_callback("any-code")

    assert len(fake_db.all_rows("users")) == 1


@pytest.mark.asyncio
async def test_handle_google_callback_wraps_supabase_failure(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """A failing Supabase exchange surfaces as UnauthorizedError, not a raw 500."""
    fake_db.auth.exchange_should_fail = True

    with pytest.raises(UnauthorizedError):
        await auth_service.handle_google_callback("doesnt-matter")


@pytest.mark.asyncio
async def test_exchange_auth_code_returns_token_once(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """The auth code is single-use: the second exchange must fail."""
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-once",
        email="once@example.com",
    )
    auth_code, _ = await auth_service.handle_google_callback("supabase-code")

    token_response = auth_service.exchange_auth_code(auth_code)

    decoded = jwt.decode(
        token_response.access_token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert decoded["email"] == "once@example.com"
    assert decoded["role"] == UserRole.PATIENT.value
    assert token_response.user.email == "once@example.com"

    with pytest.raises(UnauthorizedError):
        auth_service.exchange_auth_code(auth_code)


def test_exchange_auth_code_rejects_unknown_code(auth_service: AuthService) -> None:
    """An auth code never minted by ``handle_google_callback`` is rejected."""
    with pytest.raises(UnauthorizedError):
        auth_service.exchange_auth_code("never-minted")


@pytest.mark.asyncio
async def test_handle_google_callback_rejects_returning_inactive_user(
    auth_service: AuthService,
    fake_db: FakeSupabase,
) -> None:
    """A deactivated Google user must NOT be able to re-login via Google.

    Regression for the Devin Review finding on PR #15: without an
    explicit ``is_active`` check on the returning-user branch, an admin
    deactivating a Google user (``is_active=false``) is silently
    bypassed because the user just completes the Google OAuth flow
    again and a fresh JWT is minted.
    """
    existing = make_user_row(
        role=UserRole.PATIENT,
        email="deactivated@example.com",
        full_name="Deactivated Google User",
        auth_provider=AuthProvider.GOOGLE,
        password_hash="",
    )
    existing["provider_user_id"] = "google-sub-deactivated"
    existing["is_active"] = False
    fake_db.seed("users", [existing])
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-deactivated",
        email="deactivated@example.com",
    )

    with pytest.raises(UnauthorizedError) as excinfo:
        await auth_service.handle_google_callback("any-code")

    assert "inactive" in str(excinfo.value).lower()
    # And no JWT was stashed in the pending-tokens map for a deactivated user.
    assert AuthService._pending_tokens == {}
    # And no USER_LOGIN audit was emitted (deactivated users don't "log in").
    actions = [a["action"] for a in fake_db.all_rows("audit_logs")]
    assert AuditAction.USER_LOGIN.value not in actions


@pytest.mark.asyncio
async def test_oauth_uses_ephemeral_client_so_db_state_is_isolated(
    user_repo: object,
    audit_service: object,
    fake_db: FakeSupabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OAuth calls must NOT pollute the shared service-role DB client.

    Regression for the live-Supabase ``42501 permission denied for
    table users`` bug observed during the Google OAuth smoke test:
    ``supabase-py`` keeps a single auth state per ``Client`` instance,
    and ``auth.exchange_code_for_session`` swaps the client over to the
    newly issued user JWT (role ``authenticated``). If the same client
    is reused for ``db.table('users')`` reads afterwards, PostgREST
    rejects the query because the user JWT does not have RLS
    permissions on the ``users`` table.

    The fix is for ``AuthService`` to mint a fresh ephemeral Supabase
    client for OAuth-only operations so the injected service-role
    client used by repositories keeps its original auth state. This
    test verifies that contract: when ``handle_google_callback`` runs,
    ``create_client`` is called with the configured Supabase URL and
    key (i.e. a NEW client is built), and the OAuth call lands on that
    client — not on the injected ``self._supabase``.
    """
    # Build a separate FakeSupabase to act as the "ephemeral OAuth client".
    oauth_client = FakeSupabase()
    oauth_client.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-iso",
        email="iso@example.com",
    )

    # Track that create_client gets called with the configured URL+key.
    create_client_calls: list[tuple[str, str]] = []

    def fake_create_client(url: str, key: str) -> FakeSupabase:
        create_client_calls.append((url, key))
        return oauth_client

    monkeypatch.setattr(
        "app.services.auth_service.create_client",
        fake_create_client,
    )

    # Construct an AuthService whose injected client (``fake_db``) is
    # DIFFERENT from the OAuth ephemeral client. If AuthService
    # incorrectly used self._supabase.auth.exchange_code_for_session,
    # the call would go to ``fake_db`` and fail because no callback
    # user is configured there.
    AuthService._pending_tokens.clear()
    service = AuthService(
        user_repo=user_repo,  # type: ignore[arg-type]
        supabase=fake_db,  # type: ignore[arg-type]
        audit_service=audit_service,  # type: ignore[arg-type]
    )

    auth_code, _user_name = await service.handle_google_callback("any-code")
    assert isinstance(auth_code, str) and auth_code

    # OAuth must hit the ephemeral client only.
    assert oauth_client.auth.last_exchange_code == "any-code"
    assert fake_db.auth.last_exchange_code is None
    # And create_client was invoked with the actual Supabase config.
    assert create_client_calls
    url, key = create_client_calls[0]
    assert url == settings.supabase_url
    assert key == settings.supabase_key
