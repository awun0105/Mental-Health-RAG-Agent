from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_consent_service, require_permission
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
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("consent:accept")),
    ],
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
) -> ConsentResponse:
    """Accept a consent policy version for the current user.

    Requires the ``consent:accept`` permission.
    """
    return await consent_service.accept_consent(
        user_id=current_user.user_id,
        payload=payload,
        ip_address=request.client.host if request.client is not None else None,
    )


@router.get("/status", response_model=ConsentStatusResponse)
async def get_consent_status(
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("consent:read_status")),
    ],
    consent_service: Annotated[ConsentService, Depends(get_consent_service)],
) -> ConsentStatusResponse:
    """Return the current user's consent status.

    Requires the ``consent:read_status`` permission.
    """
    return await consent_service.get_status(user_id=current_user.user_id)
