from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_message_service, require_permission
from app.core.security import CurrentUserClaims
from app.schemas.message import (
    MessageListResponse,
    MessageResponse,
    PatientMessageCreateRequest,
)
from app.services.message_service import MessageService

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])


@router.get("", response_model=MessageListResponse)
async def list_session_messages(
    session_id: str,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("message:read")),
    ],
    message_service: Annotated[MessageService, Depends(get_message_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MessageListResponse:
    """List messages for the current patient's own session."""
    return await message_service.list_messages_for_session(
        session_id=session_id,
        current_user_id=current_user.user_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=MessageResponse, status_code=201)
async def create_patient_message(
    session_id: str,
    payload: PatientMessageCreateRequest,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("message:create")),
    ],
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> MessageResponse:
    """Create a patient-authored message in an active owned session."""
    return await message_service.create_patient_message(
        session_id=session_id,
        current_user_id=current_user.user_id,
        content=payload.content,
    )
