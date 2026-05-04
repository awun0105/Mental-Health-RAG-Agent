"""API-layer tests for /api/v1/auth/* endpoints.

These tests exercise the full DI chain:

    HTTP request -> FastAPI route -> AuthService -> UserRepository -> FakeSupabase
"""

from __future__ import annotations

from app.core.constants import UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers


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
