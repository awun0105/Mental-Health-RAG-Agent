from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import (
    get_assignment_service,
    get_audit_service,
    get_auth_service,
    get_authorization_service,
    get_role_repo,
    get_user_role_repo,
    require_permission,
)
from app.core.constants import AuditAction, UserRole
from app.core.exceptions import NotFoundError
from app.core.security import CurrentUserClaims
from app.db.repositories.role_repo import RoleRepository
from app.db.repositories.user_role_repo import UserRoleRepository
from app.schemas.assignment import AssignmentCreateRequest, AssignmentResponse
from app.schemas.rbac import AdminUserCreateRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.authorization_service import AuthorizationService

router = APIRouter(tags=["admin"])


def _coerce_legacy_role(role_name: str) -> UserRole:
    """Map a role name to the legacy ``users.role`` enum value.

    The legacy column only accepts ``patient``, ``doctor`` or ``admin``.
    Custom roles defined in the ``roles`` table fall back to
    ``UserRole.PATIENT`` so the row insert respects the column's CHECK
    constraint while the new ``user_roles`` row carries the real
    permission grant.
    """
    try:
        return UserRole(role_name)
    except ValueError:
        return UserRole.PATIENT


@router.post(
    "/admin/assignments",
    response_model=AssignmentResponse,
)
async def create_assignment(
    payload: AssignmentCreateRequest,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("assignment:create")),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
) -> AssignmentResponse:
    """Create a doctor-patient assignment.

    Requires the ``assignment:create`` permission (granted to ``admin``).
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
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("assignment:deactivate")),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
) -> AssignmentResponse:
    """Deactivate a doctor-patient assignment.

    Requires the ``assignment:deactivate`` permission (granted to ``admin``).
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
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("patient:read")),
    ],
    assignment_service: Annotated[
        AssignmentService,
        Depends(get_assignment_service),
    ],
) -> list[AssignmentResponse]:
    """List active patient assignments for the current doctor.

    Requires the ``patient:read`` permission (granted to ``doctor`` and
    ``admin``). The resource-level scope (``doctor_id == current_user``)
    is enforced inside ``AssignmentService``.
    """
    return await assignment_service.list_patients_for_doctor(
        doctor_id=current_user.user_id,
    )


@router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=201,
)
async def admin_create_user(
    payload: AdminUserCreateRequest,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("user:create")),
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repo)],
    user_role_repo: Annotated[UserRoleRepository, Depends(get_user_role_repo)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    authz: Annotated[
        AuthorizationService,
        Depends(get_authorization_service),
    ],
) -> UserResponse:
    """Provision a new user with the given role assignment.

    Requires the ``user:create`` permission (granted to ``admin``). The
    legacy ``users.role`` column is set from ``role_name`` for backward
    compatibility, and a row is also added to ``user_roles`` so the new
    user immediately resolves the expected permissions through the new
    RBAC pipeline.
    """
    role = await role_repo.get_by_name(payload.role_name)
    if role is None:
        raise NotFoundError(resource="Role", resource_id=payload.role_name)

    legacy_role = _coerce_legacy_role(role.name)

    user_data = UserCreate(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=legacy_role,
    )
    user = await auth_service.register(user_data)

    await user_role_repo.assign_role(
        user_id=user.id,
        role_id=role.id,
        assigned_by=current_user.user_id,
    )
    authz.invalidate_cache(user.id)

    actor_role = await authz.get_primary_role_name(current_user.user_id)
    await audit_service.log_event(
        user_id=current_user.user_id,
        role=actor_role,
        action=AuditAction.ROLE_ASSIGNED,
        resource_type="user_role",
        resource_id=f"{user.id}:{role.id}",
        metadata={
            "user_id": user.id,
            "role_id": role.id,
            "role_name": role.name,
            "via": "admin_create_user",
        },
        ip_address=request.client.host if request.client is not None else None,
    )

    return user
