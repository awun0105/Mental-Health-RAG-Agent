from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import AuditAction


class AuditLogCreate(BaseModel):
    """Internal schema for creating an audit log entry."""

    user_id: str | None = None
    role: str | None = None
    action: AuditAction
    resource_type: str | None = None
    resource_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    ip_address: str | None = None


class AuditLogResponse(BaseModel):
    """Response schema for audit log records."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    role: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, object]
    ip_address: str | None = None
    created_at: datetime
