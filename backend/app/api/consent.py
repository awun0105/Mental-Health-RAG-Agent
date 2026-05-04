from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_consent_service, get_current_user
from app.core.security import CurrentUserClaims
from app.schemas.consent import (
    ConsentAcceptRequest,
    ConsentResponse,
    ConsentStatusResponse,
)
from app.services.consent_service import ConsentService

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("/accept", response_model=ConsentResponse)
async def accept_consent(
    payload: ConsentAcceptRequest,
    request: Request,
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
) -> ConsentResponse:
    """Accept a consent policy version for the current user."""
    return await consent_service.accept_consent(
        user_id=current_user.user_id,
        payload=payload,
        role=current_user.role.value,
        ip_address=request.client.host if request.client is not None else None,
    )


@router.get("/status", response_model=ConsentStatusResponse)
async def get_consent_status(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
) -> ConsentStatusResponse:
    """Return the current user's consent status."""
    return await consent_service.get_status(user_id=current_user.user_id)
