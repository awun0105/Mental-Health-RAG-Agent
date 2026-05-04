"""API-layer tests for /api/v1/auth/* endpoints.

These tests exercise the full DI chain:

    HTTP request -> FastAPI route -> AuthService -> UserRepository -> FakeSupabase
"""

from __future__ import annotations

from app.core.constants import AuthProvider, UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user_row
from tests.fakes.fake_supabase import FakeSupabase, make_fake_supabase_user


def _register_payload(
    *,
    email: str = "alice@example.com",
    password: str = "correct horse battery staple",
    full_name: str = "Alice Example",
) -> dict[str, object]:
    """Build the public registration body. ``role`` is intentionally absent.

    Public self-registration is patient-only at the backend; doctor and
    admin roles are not selectable through this endpoint.
    """
    return {
        "email": email,
        "password": password,
        "full_name": full_name,
    }


def test_register_returns_user_response(client: TestClient) -> None:
    """POST /auth/register creates a new user and returns its public profile."""
    response = client.post("/api/v1/auth/register", json=_register_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "patient"
    assert "password_hash" not in body


def test_register_ignores_role_field_for_admin_escalation(client: TestClient) -> None:
    """Sending ``role=admin`` in the body must NOT escalate the new user.

    Public self-registration is patient-only. Pydantic drops unknown fields
    on ``PublicUserRegister``, and the route hard-codes ``role=patient``
    before delegating to the service. Both layers must agree that no value
    in the body can result in an admin or doctor account.
    """
    payload = {
        **_register_payload(email="evil@example.com"),
        "role": "admin",
    }
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "patient", (
        "Public /auth/register must always create patients, even when the "
        f"client passes role=admin in the body. Got role={body['role']!r}."
    )


def test_register_ignores_role_field_for_doctor_escalation(client: TestClient) -> None:
    """Same guard for ``role=doctor`` — must downgrade silently to patient."""
    payload = {
        **_register_payload(email="fakedoc@example.com"),
        "role": "doctor",
    }
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    assert response.json()["role"] == "patient"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    """Registering with an already-used email surfaces ConflictError as 409."""
    payload = _register_payload(email="dup@example.com")
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_returns_token_and_user(client: TestClient) -> None:
    """POST /auth/login returns a Bearer token plus the user payload after register."""
    register_payload = _register_payload(email="bob@example.com", password="pa55word!!")
    register = client.post("/api/v1/auth/register", json=register_payload)
    assert register.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "pa55word!!"},
    )

    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "bob@example.com"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    """Wrong password must surface UnauthorizedError as 401."""
    register_payload = _register_payload(email="carol@example.com", password="rightpw99")
    client.post("/api/v1/auth/register", json=register_payload)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "WRONGwrongwrong"},
    )

    assert response.status_code == 401


def test_me_without_token_returns_401(client: TestClient) -> None:
    """Calling /auth/me without a Bearer token must be rejected at the dependency layer."""
    response = client.get("/api/v1/auth/me")

    assert response.status_code in (401, 403)


def test_me_with_valid_token_returns_claims(client: TestClient) -> None:
    """A valid Bearer token resolves to the decoded CurrentUserClaims payload."""
    headers = auth_headers(
        user_id="uid-42",
        email="dora@example.com",
        role=UserRole.PATIENT,
    )

    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "uid-42"
    assert body["email"] == "dora@example.com"
    assert body["role"] == "patient"


# ─── Google OAuth routes ─────────────────────────────────────────────────────


def test_google_login_url_returns_supabase_url(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """GET /auth/google returns the URL Supabase generated for the OAuth flow."""
    fake_db.auth.next_oauth_url = "https://accounts.google.com/o/oauth2/auth?route=1"

    response = client.get("/api/v1/auth/google")

    assert response.status_code == 200
    assert response.json() == {
        "url": "https://accounts.google.com/o/oauth2/auth?route=1",
    }


def test_google_callback_redirects_to_frontend_with_auth_code(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """A successful Google login redirects to the frontend with an opaque auth code."""
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-route",
        email="route@example.com",
        full_name="Route User",
    )

    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "supabase-code"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 307)
    location = response.headers["location"]
    assert "auth_code=" in location
    assert "user_name=" in location
    # The actual JWT must NEVER appear in the URL.
    assert "access_token=" not in location
    assert "Bearer" not in location


def test_google_callback_redirects_with_error_when_email_belongs_to_local_account(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Verify-first reject must produce a redirect with ``google_error`` set."""
    fake_db.seed(
        "users",
        [
            make_user_row(
                role=UserRole.PATIENT,
                email="conflict@example.com",
                auth_provider=AuthProvider.LOCAL,
            ),
        ],
    )
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-conflict",
        email="conflict@example.com",
    )

    response = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "supabase-code"},
        follow_redirects=False,
    )

    assert response.status_code in (302, 307)
    location = response.headers["location"]
    assert "google_error=" in location
    assert "auth_code=" not in location


def test_google_exchange_returns_token_for_valid_code(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """POST /auth/google/exchange trades the one-time code for a real JWT."""
    fake_db.auth.next_callback_user = make_fake_supabase_user(
        user_id="google-sub-exchange",
        email="exchange@example.com",
        full_name="Exchange User",
    )
    callback = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "supabase-code"},
        follow_redirects=False,
    )
    assert callback.status_code in (302, 307)
    location = callback.headers["location"]
    auth_code = location.split("auth_code=", 1)[1].split("&", 1)[0]

    response = client.post(
        "/api/v1/auth/google/exchange",
        json={"auth_code": auth_code},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "exchange@example.com"
    assert body["user"]["auth_provider"] == "google"


def test_google_exchange_rejects_unknown_code(client: TestClient) -> None:
    """A completely unknown auth code must be rejected with 401."""
    response = client.post(
        "/api/v1/auth/google/exchange",
        json={"auth_code": "never-issued-by-this-server"},
    )

    assert response.status_code == 401
