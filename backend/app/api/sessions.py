from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import (
    get_session_service,
    require_permission,
)
from app.core.security import CurrentUserClaims
from app.schemas.session import (
    SessionCloseRequest,
    SessionListResponse,
    SessionResponse,
    SessionStartRequest,
)
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def start_session(
    payload: SessionStartRequest,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("session:create")),
    ],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """Start a new chat session for the current patient.

    Requires the ``session:create`` permission (granted to ``patient``).
    The service layer additionally enforces consent acceptance and
    "patient role only" semantics.
    """
    return await session_service.start_session(
        user_id=current_user.user_id,
        role=current_user.role.value,
        metadata=payload.metadata,
        ip_address=request.client.host if request.client is not None else None,
    )


@router.post("/{session_id}/close", response_model=SessionResponse)
async def close_session(
    session_id: str,
    payload: SessionCloseRequest,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("session:close")),
    ],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """Close a chat session owned by the current patient.

    Requires the ``session:close`` permission (granted to ``patient``).
    The service layer enforces "only the session owner can close it".
    """
    return await session_service.close_session(
        session_id=session_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role.value,
        reason=payload.reason,
        ip_address=request.client.host if request.client is not None else None,
    )


@router.get("/me", response_model=SessionListResponse)
async def list_my_sessions(
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("session:read")),
    ],
    session_service: Annotated[SessionService, Depends(get_session_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SessionListResponse:
    """List the current patient's own sessions, newest first.

    Requires the ``session:read`` permission. The result is hard-scoped
    to ``current_user.user_id`` in the service layer regardless of role.
    """
    return await session_service.list_sessions_for_user(
        user_id=current_user.user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("session:read")),
    ],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionResponse:
    """Return a session by id.

    Requires the ``session:read`` permission. Resource-level RBAC
    (patient ownership / doctor assignment) is enforced inside
    ``SessionService.get_session``.
    """
    return await session_service.get_session(
        session_id=session_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role.value,
    )
