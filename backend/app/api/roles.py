from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import (
    get_audit_service,
    get_authorization_service,
    get_permission_repo,
    get_role_permission_repo,
    get_role_repo,
    get_user_repo,
    get_user_role_repo,
    require_permission,
)
from app.core.constants import AuditAction
from app.core.exceptions import NotFoundError
from app.core.security import CurrentUserClaims
from app.db.repositories.permission_repo import PermissionRepository
from app.db.repositories.role_permission_repo import RolePermissionRepository
from app.db.repositories.role_repo import RoleRepository
from app.db.repositories.user_repo import UserRepository
from app.db.repositories.user_role_repo import UserRoleRepository
from app.schemas.rbac import PermissionResponse, RoleResponse
from app.services.audit_service import AuditService
from app.services.authorization_service import AuthorizationService

router = APIRouter(prefix="/admin", tags=["admin-rbac"])


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    _: Annotated[
        CurrentUserClaims,
        Depends(require_permission("role:read")),
    ],
    role_repo: Annotated[RoleRepository, Depends(get_role_repo)],
) -> list[RoleResponse]:
    """List every role registered in the system."""
    return await role_repo.list_all()


@router.post(
    "/users/{user_id}/roles/{role_id}",
    status_code=201,
)
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("role:assign")),
    ],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    role_repo: Annotated[RoleRepository, Depends(get_role_repo)],
    user_role_repo: Annotated[UserRoleRepository, Depends(get_user_role_repo)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    authz: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> dict[str, str]:
    """Assign a role to a user.

    Requires the ``role:assign`` permission.
    """
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise NotFoundError(resource="User", resource_id=user_id)

    role = await role_repo.get_by_id(role_id)
    if role is None:
        raise NotFoundError(resource="Role", resource_id=role_id)

    await user_role_repo.assign_role(
        user_id=user_id,
        role_id=role_id,
        assigned_by=current_user.user_id,
    )
    authz.invalidate_cache(user_id)

    await audit_service.log_event(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action=AuditAction.ROLE_ASSIGNED,
        resource_type="user_role",
        resource_id=f"{user_id}:{role_id}",
        metadata={
            "user_id": user_id,
            "role_id": role_id,
            "role_name": role.name,
        },
        ip_address=request.client.host if request.client is not None else None,
    )

    return {"user_id": user_id, "role_id": role_id, "status": "assigned"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("role:assign")),
    ],
    user_role_repo: Annotated[UserRoleRepository, Depends(get_user_role_repo)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    authz: Annotated[AuthorizationService, Depends(get_authorization_service)],
) -> dict[str, str]:
    """Remove a role from a user.

    Requires the ``role:assign`` permission.
    """
    removed = await user_role_repo.remove_role(user_id=user_id, role_id=role_id)
    if not removed:
        raise NotFoundError(
            resource="user_role",
            resource_id=f"{user_id}:{role_id}",
        )

    authz.invalidate_cache(user_id)

    await audit_service.log_event(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action=AuditAction.ROLE_REMOVED,
        resource_type="user_role",
        resource_id=f"{user_id}:{role_id}",
        metadata={"user_id": user_id, "role_id": role_id},
        ip_address=request.client.host if request.client is not None else None,
    )

    return {"user_id": user_id, "role_id": role_id, "status": "removed"}


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    _: Annotated[
        CurrentUserClaims,
        Depends(require_permission("permission:read")),
    ],
    permission_repo: Annotated[
        PermissionRepository,
        Depends(get_permission_repo),
    ],
) -> list[PermissionResponse]:
    """List every permission registered in the system."""
    return await permission_repo.list_all()


@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    status_code=201,
)
async def assign_permission_to_role(
    role_id: str,
    permission_id: str,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("permission:assign")),
    ],
    role_repo: Annotated[RoleRepository, Depends(get_role_repo)],
    permission_repo: Annotated[
        PermissionRepository,
        Depends(get_permission_repo),
    ],
    role_permission_repo: Annotated[
        RolePermissionRepository,
        Depends(get_role_permission_repo),
    ],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> dict[str, str]:
    """Grant a permission to a role.

    Requires the ``permission:assign`` permission. The cache is NOT
    invalidated per-user because mapping affects every user holding
    this role; downstream lookups will refresh on TTL expiry. Operators
    needing immediate effect can restart the API process.
    """
    role = await role_repo.get_by_id(role_id)
    if role is None:
        raise NotFoundError(resource="Role", resource_id=role_id)

    permission = await permission_repo.get_by_id(permission_id)
    if permission is None:
        raise NotFoundError(resource="Permission", resource_id=permission_id)

    await role_permission_repo.assign_permission(
        role_id=role_id,
        permission_id=permission_id,
        granted_by=current_user.user_id,
    )

    await audit_service.log_event(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action=AuditAction.PERMISSION_ASSIGNED,
        resource_type="role_permission",
        resource_id=f"{role_id}:{permission_id}",
        metadata={
            "role_id": role_id,
            "permission_id": permission_id,
            "permission_code": permission.code,
        },
        ip_address=request.client.host if request.client is not None else None,
    )

    return {
        "role_id": role_id,
        "permission_id": permission_id,
        "status": "assigned",
    }


@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    request: Request,
    current_user: Annotated[
        CurrentUserClaims,
        Depends(require_permission("permission:assign")),
    ],
    role_permission_repo: Annotated[
        RolePermissionRepository,
        Depends(get_role_permission_repo),
    ],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> dict[str, str]:
    """Revoke a permission from a role.

    Requires the ``permission:assign`` permission.
    """
    removed = await role_permission_repo.remove_permission(
        role_id=role_id,
        permission_id=permission_id,
    )
    if not removed:
        raise NotFoundError(
            resource="role_permission",
            resource_id=f"{role_id}:{permission_id}",
        )

    await audit_service.log_event(
        user_id=current_user.user_id,
        role=current_user.role.value,
        action=AuditAction.PERMISSION_REMOVED,
        resource_type="role_permission",
        resource_id=f"{role_id}:{permission_id}",
        metadata={"role_id": role_id, "permission_id": permission_id},
        ip_address=request.client.host if request.client is not None else None,
    )

    return {
        "role_id": role_id,
        "permission_id": permission_id,
        "status": "removed",
    }
