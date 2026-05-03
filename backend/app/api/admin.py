from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import (
    get_assignment_service,
    require_current_admin,
    require_current_doctor,
)
from app.core.security import CurrentUserClaims
from app.schemas.assignment import AssignmentCreateRequest, AssignmentResponse
from app.services.assignment_service import AssignmentService

router = APIRouter(tags=["admin"])


@router.post(
    "/admin/assignments",
    response_model=AssignmentResponse,
)
async def create_assignment(
    payload: AssignmentCreateRequest,
    request: Request,
    current_user: Annotated[CurrentUserClaims, Depends(require_current_admin)],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
) -> AssignmentResponse:
    """Create a doctor-patient assignment.

    Only admins can create assignments.
    """
    return await assignment_service.create_assignment(
        payload=payload,
        assigned_by=current_user.user_id,
        ip_address=request.client.host if request.client is not None else None,
    )


@router.patch(
    "/admin/assignments/{assignment_id}/deactivate",
    response_model=AssignmentResponse,
)
async def deactivate_assignment(
    assignment_id: str,
    request: Request,
    current_user: Annotated[CurrentUserClaims, Depends(require_current_admin)],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
) -> AssignmentResponse:
    """Deactivate a doctor-patient assignment.

    Only admins can deactivate assignments.
    """
    return await assignment_service.deactivate_assignment(
        assignment_id=assignment_id,
        deactivated_by=current_user.user_id,
        ip_address=request.client.host if request.client is not None else None,
    )


@router.get(
    "/doctor/my-patients",
    response_model=list[AssignmentResponse],
)
async def list_my_patients(
    current_user: Annotated[CurrentUserClaims, Depends(require_current_doctor)],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
) -> list[AssignmentResponse]:
    """List active patient assignments for the current doctor."""
    return await assignment_service.list_patients_for_doctor(
        doctor_id=current_user.user_id,
    )
