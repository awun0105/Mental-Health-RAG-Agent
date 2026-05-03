from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssignmentCreateRequest(BaseModel):
    """Request schema for creating a doctor-patient assignment."""

    doctor_id: str
    patient_id: str


class AssignmentResponse(BaseModel):
    """Response schema for doctor-patient assignment records."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    patient_id: str
    assigned_by: str
    is_active: bool
    created_at: datetime
