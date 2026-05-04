"""Tests for AssignmentService create + ensure_doctor_can_access_patient."""

from __future__ import annotations

import pytest
from app.core.constants import UserRole
from app.core.exceptions import ForbiddenError
from app.schemas.assignment import AssignmentCreateRequest
from app.services.assignment_service import AssignmentService

from tests.conftest import make_user_row
from tests.fakes.fake_supabase import FakeSupabase


async def test_create_assignment_is_idempotent_for_existing_active(
    assignment_service: AssignmentService,
    fake_db: FakeSupabase,
) -> None:
    """A second create for an already-active doctor↔patient pair returns the same row."""
    doctor = make_user_row(role=UserRole.DOCTOR, full_name="Dr A")
    patient = make_user_row(role=UserRole.PATIENT, full_name="Pat A")
    fake_db.seed("users", [doctor, patient])

    payload = AssignmentCreateRequest(
        doctor_id=doctor["id"],
        patient_id=patient["id"],
    )

    first = await assignment_service.create_assignment(
        payload=payload,
        assigned_by="admin-1",
        assigned_by_role=UserRole.ADMIN.value,
    )
    second = await assignment_service.create_assignment(
        payload=payload,
        assigned_by="admin-1",
        assigned_by_role=UserRole.ADMIN.value,
    )

    assert first.id == second.id

    rows = fake_db.all_rows("doctor_assignments")
    assert len(rows) == 1
    assert rows[0]["is_active"] is True

    audit_rows = fake_db.all_rows("audit_logs")
    # Only the first call writes an audit event; idempotent return must not double-log.
    assert len(audit_rows) == 1
    assert audit_rows[0]["role"] == UserRole.ADMIN.value
    assert audit_rows[0]["action"] == "doctor_assignment_created"


async def test_ensure_doctor_can_access_patient_blocks_unassigned(
    assignment_service: AssignmentService,
    fake_db: FakeSupabase,
) -> None:
    """A doctor without an active assignment to the patient is blocked with 403."""
    doctor = make_user_row(role=UserRole.DOCTOR)
    patient = make_user_row(role=UserRole.PATIENT)
    fake_db.seed("users", [doctor, patient])

    # No assignment seeded -> access must be denied.
    with pytest.raises(ForbiddenError):
        await assignment_service.ensure_doctor_can_access_patient(
            doctor_id=doctor["id"],
            patient_id=patient["id"],
        )

    # After creating the assignment, the same call must succeed.
    await assignment_service.create_assignment(
        payload=AssignmentCreateRequest(
            doctor_id=doctor["id"],
            patient_id=patient["id"],
        ),
        assigned_by="admin-1",
        assigned_by_role=UserRole.ADMIN.value,
    )

    # Should not raise now.
    await assignment_service.ensure_doctor_can_access_patient(
        doctor_id=doctor["id"],
        patient_id=patient["id"],
    )
