from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import MessageRole, SafetySeverity


class MessageCreate(BaseModel):
    """Server-side schema for inserting a chat_messages row.

    This schema is used by the message repository and by future agent
    pipelines (Milestone 4/5). It is not exposed via any HTTP route in
    the Sessions CRUD scope.
    """

    session_id: str
    role: MessageRole
    content: str = Field(min_length=1)
    safety_flag: bool = False
    safety_severity: SafetySeverity = SafetySeverity.NONE
    trace_id: str | None = None


class MessageResponse(BaseModel):
    """Response schema for a single chat_messages row."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: MessageRole
    content: str
    safety_flag: bool
    safety_severity: SafetySeverity
    trace_id: str | None = None
    created_at: datetime
