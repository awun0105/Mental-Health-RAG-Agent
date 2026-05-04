"""API-layer tests for /api/v1/admin/* endpoints (RBAC + happy path)."""

from __future__ import annotations

from app.core.constants import UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user_row
from tests.fakes.fake_supabase import FakeSupabase


def test_create_assignment_without_token_returns_401(client: TestClient) -> None:
    """Admin endpoints must reject anonymous calls."""
    response = client.post(
        "/api/v1/admin/assignments",
        json={"doctor_id": "d", "patient_id": "p"},
    )

    assert response.status_code in (401, 403)


def test_create_assignment_as_patient_returns_403(client: TestClient) -> None:
    """A patient bearer token must be rejected by require_current_admin."""
    headers = auth_headers(role=UserRole.PATIENT)

    response = client.post(
        "/api/v1/admin/assignments",
        json={"doctor_id": "d", "patient_id": "p"},
        headers=headers,
    )

    assert response.status_code == 403


def test_create_assignment_as_admin_succeeds(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Admin can create an assignment between a real doctor and patient."""
    doctor_row = make_user_row(role=UserRole.DOCTOR, email="doc@example.com")
    patient_row = make_user_row(role=UserRole.PATIENT, email="pat@example.com")
    fake_db.tables.setdefault("users", []).extend([doctor_row, patient_row])

    headers = auth_headers(
        user_id="admin-1",
        email="admin@example.com",
        role=UserRole.ADMIN,
    )

    response = client.post(
        "/api/v1/admin/assignments",
        json={"doctor_id": doctor_row["id"], "patient_id": patient_row["id"]},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["doctor_id"] == doctor_row["id"]
    assert body["patient_id"] == patient_row["id"]
    assert body["assigned_by"] == "admin-1"
    assert body["is_active"] is True

    assignment_rows = fake_db.tables.get("doctor_assignments", [])
    assert len(assignment_rows) == 1

    audit_rows = fake_db.tables.get("audit_logs", [])
    assert audit_rows[-1]["role"] == "admin"
    assert audit_rows[-1]["action"] == "doctor_assignment_created"


def test_deactivate_assignment_as_admin_succeeds(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Admin can deactivate an existing assignment."""
    doctor_row = make_user_row(role=UserRole.DOCTOR)
    patient_row = make_user_row(role=UserRole.PATIENT)
    fake_db.tables.setdefault("users", []).extend([doctor_row, patient_row])

    admin_headers = auth_headers(
        user_id="admin-2",
        email="admin2@example.com",
        role=UserRole.ADMIN,
    )

    create = client.post(
        "/api/v1/admin/assignments",
        json={"doctor_id": doctor_row["id"], "patient_id": patient_row["id"]},
        headers=admin_headers,
    )
    assert create.status_code == 200
    assignment_id = create.json()["id"]

    deactivate = client.patch(
        f"/api/v1/admin/assignments/{assignment_id}/deactivate",
        headers=admin_headers,
    )

    assert deactivate.status_code == 200
    body = deactivate.json()
    assert body["id"] == assignment_id
    assert body["is_active"] is False
