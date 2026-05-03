from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import MessageRole, SafetySeverity, SessionStatus


class ChatSessionResponse(BaseModel):
    """Response schema for patient chat sessions."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    """Response schema for chat messages."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: MessageRole
    content: str
    safety_flag: bool
    safety_severity: SafetySeverity
    trace_id: str | None = None
    created_at: datetime
