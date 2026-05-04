from collections.abc import Mapping

from supabase import Client

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONValue
from app.schemas.assignment import AssignmentResponse


class AssignmentRepository(BaseRepository[AssignmentResponse]):
    """Repository for doctor_assignments table."""

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="doctor_assignments")

    def _to_model(self, row: Mapping[str, JSONValue]) -> AssignmentResponse:
        """Convert a raw doctor_assignments row into a response model."""
        return AssignmentResponse.model_validate(dict(row))

    async def get_active_assignment(
        self,
        doctor_id: str,
        patient_id: str,
    ) -> AssignmentResponse | None:
        """Return the active assignment between a doctor and patient."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("doctor_id", doctor_id)
                .eq("patient_id", patient_id)
                .eq("is_active", True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch active assignment") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)

    async def is_assigned(
        self,
        doctor_id: str,
        patient_id: str,
    ) -> bool:
        """Return True if doctor has an active assignment to patient."""
        assignment = await self.get_active_assignment(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        return assignment is not None

    async def list_patients_for_doctor(
        self,
        doctor_id: str,
    ) -> list[AssignmentResponse]:
        """List active patient assignments for a doctor."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("doctor_id", doctor_id)
                .eq("is_active", True)
                .order("created_at", desc=True)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list patients for doctor") from exc

        return [self._to_model(row) for row in self._rows(result.data)]

    async def list_doctors_for_patient(
        self,
        patient_id: str,
    ) -> list[AssignmentResponse]:
        """List active doctor assignments for a patient."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("patient_id", patient_id)
                .eq("is_active", True)
                .order("created_at", desc=True)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list doctors for patient") from exc

        return [self._to_model(row) for row in self._rows(result.data)]

    async def deactivate(
        self,
        assignment_id: str,
    ) -> AssignmentResponse | None:
        """Deactivate a doctor-patient assignment."""
        try:
            result = (
                self._db.table(self._table_name)
                .update({"is_active": False})
                .eq("id", assignment_id)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to deactivate assignment") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)
