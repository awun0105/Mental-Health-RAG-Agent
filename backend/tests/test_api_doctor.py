"""API-layer tests for /api/v1/doctor/* endpoints."""

from __future__ import annotations

from app.core.constants import UserRole
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, make_user_row
from tests.fakes.fake_supabase import FakeSupabase


def test_my_patients_as_patient_returns_403(client: TestClient) -> None:
    """Only doctors can call /doctor/my-patients."""
    headers = auth_headers(role=UserRole.PATIENT)

    response = client.get("/api/v1/doctor/my-patients", headers=headers)

    assert response.status_code == 403


def test_my_patients_as_doctor_returns_assignments(
    client: TestClient,
    fake_db: FakeSupabase,
) -> None:
    """Doctor sees only the assignments where they are the doctor side."""
    doctor_row = make_user_row(role=UserRole.DOCTOR, email="dr@example.com")
    other_doctor_row = make_user_row(role=UserRole.DOCTOR, email="dr2@example.com")
    patient_row = make_user_row(role=UserRole.PATIENT, email="pat@example.com")
    fake_db.tables.setdefault("users", []).extend(
        [doctor_row, other_doctor_row, patient_row],
    )

    admin_headers = auth_headers(role=UserRole.ADMIN, user_id="admin-d")
    create_mine = client.post(
        "/api/v1/admin/assignments",
        json={"doctor_id": doctor_row["id"], "patient_id": patient_row["id"]},
        headers=admin_headers,
    )
    assert create_mine.status_code == 200
    create_other = client.post(
        "/api/v1/admin/assignments",
        json={"doctor_id": other_doctor_row["id"], "patient_id": patient_row["id"]},
        headers=admin_headers,
    )
    assert create_other.status_code == 200

    doctor_headers = auth_headers(
        user_id=doctor_row["id"],
        email=doctor_row["email"],
        role=UserRole.DOCTOR,
    )

    response = client.get("/api/v1/doctor/my-patients", headers=doctor_headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["doctor_id"] == doctor_row["id"]
    assert rows[0]["patient_id"] == patient_row["id"]
