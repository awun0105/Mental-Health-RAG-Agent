"""API-layer tests for /api/v1/admin/roles* and /api/v1/admin/permissions* endpoints."""

from __future__ import annotations

from app.core.constants import UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user_row, seed_rbac_tables
from tests.fakes.fake_supabase import FakeSupabase


def test_list_roles_requires_role_read_permission(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Patient bearer token is rejected; admin can list roles."""
    seed_rbac_tables(fake_db)

    forbidden = client.get(
        "/api/v1/admin/roles",
        headers=auth_headers(role=UserRole.PATIENT),
    )
    assert forbidden.status_code == 403

    allowed = client.get(
        "/api/v1/admin/roles",
        headers=auth_headers(user_id="admin-1", role=UserRole.ADMIN),
    )
    assert allowed.status_code == 200

    body = allowed.json()
    role_names = {row["name"] for row in body}
    assert {"admin", "doctor", "patient"}.issubset(role_names)


def test_list_permissions_requires_permission_read(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Patient cannot list permissions; admin can."""
    seed_rbac_tables(fake_db)

    forbidden = client.get(
        "/api/v1/admin/permissions",
        headers=auth_headers(role=UserRole.PATIENT),
    )
    assert forbidden.status_code == 403

    allowed = client.get(
        "/api/v1/admin/permissions",
        headers=auth_headers(user_id="admin-1", role=UserRole.ADMIN),
    )
    assert allowed.status_code == 200

    codes = {row["code"] for row in allowed.json()}
    assert "auth:me" in codes
    assert "role:assign" in codes


def test_assign_role_to_user_writes_user_role_row_and_audit(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Admin assigns a role; ``user_roles`` is updated and an audit log is written."""
    ids = seed_rbac_tables(fake_db)
    target_user = make_user_row(role=UserRole.PATIENT)
    fake_db.tables.setdefault("users", []).append(target_user)

    response = client.post(
        f"/api/v1/admin/users/{target_user['id']}/roles/{ids['roles']['doctor']}",
        headers=auth_headers(user_id="admin-1", role=UserRole.ADMIN),
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "user_id": target_user["id"],
        "role_id": ids["roles"]["doctor"],
        "status": "assigned",
    }

    user_role_rows = fake_db.tables.get("user_roles", [])
    assert any(
        r["user_id"] == target_user["id"] and r["role_id"] == ids["roles"]["doctor"]
        for r in user_role_rows
    )

    audit_rows = fake_db.tables.get("audit_logs", [])
    assert audit_rows[-1]["action"] == "role_assigned"
    assert audit_rows[-1]["user_id"] == "admin-1"


def test_assign_role_rejects_unknown_role(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Assigning a non-existent role returns 404."""
    seed_rbac_tables(fake_db)
    target_user = make_user_row(role=UserRole.PATIENT)
    fake_db.tables.setdefault("users", []).append(target_user)

    response = client.post(
        f"/api/v1/admin/users/{target_user['id']}/roles/non-existent",
        headers=auth_headers(user_id="admin-1", role=UserRole.ADMIN),
    )

    assert response.status_code == 404


def test_remove_role_removes_user_role_row_and_audits(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Admin removes a previously assigned role."""
    ids = seed_rbac_tables(fake_db)
    target_user = make_user_row(role=UserRole.PATIENT)
    fake_db.tables.setdefault("users", []).append(target_user)

    headers = auth_headers(user_id="admin-1", role=UserRole.ADMIN)
    create = client.post(
        f"/api/v1/admin/users/{target_user['id']}/roles/{ids['roles']['doctor']}",
        headers=headers,
    )
    assert create.status_code == 201

    delete = client.delete(
        f"/api/v1/admin/users/{target_user['id']}/roles/{ids['roles']['doctor']}",
        headers=headers,
    )

    assert delete.status_code == 200
    body = delete.json()
    assert body["status"] == "removed"

    user_role_rows = fake_db.tables.get("user_roles", [])
    assert not any(
        r["user_id"] == target_user["id"] and r["role_id"] == ids["roles"]["doctor"]
        for r in user_role_rows
    )

    audit_rows = fake_db.tables.get("audit_logs", [])
    assert audit_rows[-1]["action"] == "role_removed"


def test_assign_permission_writes_role_permission_row_and_audits(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Admin grants a permission to a role and an audit log is written."""
    ids = seed_rbac_tables(fake_db)

    fake_db.tables["role_permissions"] = [
        rp
        for rp in fake_db.tables.get("role_permissions", [])
        if not (
            rp["role_id"] == ids["roles"]["doctor"]
            and rp["permission_id"] == ids["permissions"]["session:create"]
        )
    ]

    response = client.post(
        f"/api/v1/admin/roles/{ids['roles']['doctor']}/permissions/{ids['permissions']['session:create']}",
        headers=auth_headers(user_id="admin-1", role=UserRole.ADMIN),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "assigned"

    role_permissions = fake_db.tables.get("role_permissions", [])
    assert any(
        r["role_id"] == ids["roles"]["doctor"]
        and r["permission_id"] == ids["permissions"]["session:create"]
        for r in role_permissions
    )

    audit_rows = fake_db.tables.get("audit_logs", [])
    assert audit_rows[-1]["action"] == "permission_assigned"


def test_assign_permission_rejects_unknown_permission(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Assigning a missing permission returns 404."""
    ids = seed_rbac_tables(fake_db)

    response = client.post(
        f"/api/v1/admin/roles/{ids['roles']['doctor']}/permissions/non-existent",
        headers=auth_headers(user_id="admin-1", role=UserRole.ADMIN),
    )

    assert response.status_code == 404


def test_remove_permission_revokes_grant(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Admin revokes a permission previously granted to a role."""
    ids = seed_rbac_tables(fake_db)
    headers = auth_headers(user_id="admin-1", role=UserRole.ADMIN)

    response = client.delete(
        f"/api/v1/admin/roles/{ids['roles']['doctor']}/permissions/{ids['permissions']['session:read']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "removed"

    role_permissions = fake_db.tables.get("role_permissions", [])
    assert not any(
        r["role_id"] == ids["roles"]["doctor"]
        and r["permission_id"] == ids["permissions"]["session:read"]
        for r in role_permissions
    )

    audit_rows = fake_db.tables.get("audit_logs", [])
    assert audit_rows[-1]["action"] == "permission_removed"


def test_admin_can_create_user_with_role(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """``POST /api/v1/admin/users`` provisions a user and links a user_roles row."""
    ids = seed_rbac_tables(fake_db)

    response = client.post(
        "/api/v1/admin/users",
        json={
            "email": "newdoc@example.com",
            "password": "S3cret!Password",
            "full_name": "New Doctor",
            "role_name": "doctor",
        },
        headers=auth_headers(user_id="admin-1", role=UserRole.ADMIN),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newdoc@example.com"
    assert body["role"] == "doctor"
    new_user_id = body["id"]

    user_role_rows = fake_db.tables.get("user_roles", [])
    assert any(
        r["user_id"] == new_user_id and r["role_id"] == ids["roles"]["doctor"]
        for r in user_role_rows
    )


def test_resource_level_check_still_blocks_other_users_session(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Resource-level ownership in ``SessionService`` still applies after RBAC refactor.

    Two patients exist. Patient A has ``session:read`` (from the patient
    role) and tries to fetch Patient B's session via ``GET /sessions/{id}``.
    The route-level permission check passes (both are patients), but the
    service layer must reject the read because A does not own the session.
    """
    patient_a = make_user_row(role=UserRole.PATIENT, email="a@example.com")
    patient_b = make_user_row(role=UserRole.PATIENT, email="b@example.com")
    fake_db.tables.setdefault("users", []).extend([patient_a, patient_b])

    session_b = {
        "id": "session-b",
        "user_id": patient_b["id"],
        "status": "active",
        "started_at": "2025-01-01T00:00:00+00:00",
        "ended_at": None,
        "consent_id": None,
        "metadata": {},
        "created_at": "2025-01-01T00:00:00+00:00",
        "updated_at": "2025-01-01T00:00:00+00:00",
    }
    fake_db.tables.setdefault("chat_sessions", []).append(session_b)

    response = client.get(
        f"/api/v1/sessions/{session_b['id']}",
        headers=auth_headers(user_id=patient_a["id"], role=UserRole.PATIENT),
    )

    assert response.status_code == 403
