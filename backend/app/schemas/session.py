from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import SessionStatus


class SessionStartRequest(BaseModel):
    """Request schema for starting a new chat session.

    The body is optional. If provided, ``metadata`` is stored as-is on the
    session row to give the frontend a place to attach UI hints (e.g. preferred
    locale, entry point). It MUST be a JSON object so the database CHECK
    constraint ``chat_sessions_metadata_is_object`` is satisfied.
    """

    metadata: dict[str, Any] = Field(default_factory=dict)


CloseReason = Literal["user_end", "intent_end", "inactivity"]


class SessionCloseRequest(BaseModel):
    """Request schema for closing an existing chat session.

    ``reason`` defaults to ``user_end`` when callers omit it. The value is
    persisted in the audit log so future automation (Milestone 4/5 inactivity
    timeout, intent-detection close) can reuse this contract.
    """

    reason: CloseReason = "user_end"


class SessionResponse(BaseModel):
    """Response schema for a single chat_sessions row."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    status: SessionStatus
    started_at: datetime
    ended_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionListResponse(BaseModel):
    """Response schema for a paginated list of sessions."""

    items: list[SessionResponse]
    limit: int
    offset: int
