from app.core.constants import AuditAction, UserRole
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.base import JSONRow
from app.db.repositories.user_repo import UserRepository
from app.schemas.assignment import AssignmentCreateRequest, AssignmentResponse
from app.services.audit_service import AuditService


class AssignmentService:
    """Service for managing doctor-patient assignments."""

    def __init__(
        self,
        assignment_repo: AssignmentRepository,
        user_repo: UserRepository,
        audit_service: AuditService,
    ) -> None:
        self._assignment_repo = assignment_repo
        self._user_repo = user_repo
        self._audit_service = audit_service

    async def create_assignment(
        self,
        payload: AssignmentCreateRequest,
        assigned_by: str,
        ip_address: str | None = None,
    ) -> AssignmentResponse:
        """Create a doctor-patient assignment."""
        doctor = await self._user_repo.get_by_id(payload.doctor_id)
        if doctor is None:
            raise NotFoundError(resource="Doctor", resource_id=payload.doctor_id)

        if doctor.role != UserRole.DOCTOR:
            raise ForbiddenError("Assigned doctor_id must belong to a doctor user")

        patient = await self._user_repo.get_by_id(payload.patient_id)
        if patient is None:
            raise NotFoundError(resource="Patient", resource_id=payload.patient_id)

        if patient.role != UserRole.PATIENT:
            raise ForbiddenError("Assigned patient_id must belong to a patient user")

        existing_assignment = await self._assignment_repo.get_active_assignment(
            doctor_id=payload.doctor_id,
            patient_id=payload.patient_id,
        )
        if existing_assignment is not None:
            return existing_assignment

        assignment_data: JSONRow = {
            "doctor_id": payload.doctor_id,
            "patient_id": payload.patient_id,
            "assigned_by": assigned_by,
            "is_active": True,
        }

        assignment = await self._assignment_repo.create(assignment_data)

        await self._audit_service.log_event(
            user_id=assigned_by,
            action=AuditAction.DOCTOR_ASSIGNMENT_CREATED,
            resource_type="doctor_assignment",
            resource_id=assignment.id,
            metadata={
                "doctor_id": payload.doctor_id,
                "patient_id": payload.patient_id,
            },
            ip_address=ip_address,
        )

        return assignment

    async def deactivate_assignment(
        self,
        assignment_id: str,
        deactivated_by: str,
        ip_address: str | None = None,
    ) -> AssignmentResponse:
        """Deactivate a doctor-patient assignment."""
        assignment = await self._assignment_repo.deactivate(assignment_id)
        if assignment is None:
            raise NotFoundError(
                resource="Doctor assignment",
                resource_id=assignment_id,
            )

        await self._audit_service.log_event(
            user_id=deactivated_by,
            action=AuditAction.ASSIGNMENT_DEACTIVATED,
            resource_type="doctor_assignment",
            resource_id=assignment.id,
            metadata={
                "doctor_id": assignment.doctor_id,
                "patient_id": assignment.patient_id,
            },
            ip_address=ip_address,
        )

        return assignment

    async def ensure_doctor_can_access_patient(
        self,
        doctor_id: str,
        patient_id: str,
    ) -> None:
        """Raise ForbiddenError if doctor is not assigned to patient."""
        is_assigned = await self._assignment_repo.is_assigned(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        if not is_assigned:
            raise ForbiddenError("Doctor is not assigned to this patient")

    async def list_patients_for_doctor(
        self,
        doctor_id: str,
    ) -> list[AssignmentResponse]:
        """List active patient assignments for a doctor."""
        return await self._assignment_repo.list_patients_for_doctor(
            doctor_id=doctor_id,
        )

    async def list_doctors_for_patient(
        self,
        patient_id: str,
    ) -> list[AssignmentResponse]:
        """List active doctor assignments for a patient."""
        return await self._assignment_repo.list_doctors_for_patient(
            patient_id=patient_id,
        )
