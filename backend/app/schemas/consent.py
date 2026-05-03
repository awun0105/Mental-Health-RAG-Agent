from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConsentAcceptRequest(BaseModel):
    """Request schema for accepting a consent policy version."""

    policy_version: str = Field(min_length=1, max_length=20)


class ConsentResponse(BaseModel):
    """Response schema for a stored consent record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    policy_version: str
    accepted: bool
    accepted_at: datetime


class ConsentStatusResponse(BaseModel):
    """Response schema for current consent status."""

    has_valid_consent: bool
    current_policy_version: str
    latest_accepted_policy_version: str | None = None
