from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleResponse(BaseModel):
    """Public response schema for a role record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str
    description: str | None = None
    is_system: bool
    created_at: datetime
    updated_at: datetime


class PermissionResponse(BaseModel):
    """Public response schema for a permission record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    module: str
    action: str
    description: str | None = None


class UserRoleAssignRequest(BaseModel):
    """Request body for assigning a role to a user."""

    user_id: str = Field(min_length=1)
    role_id: str = Field(min_length=1)


class RolePermissionAssignRequest(BaseModel):
    """Request body for granting a permission to a role."""

    role_id: str = Field(min_length=1)
    permission_id: str = Field(min_length=1)


class AdminUserCreateRequest(BaseModel):
    """Request body for the admin user-create endpoint.

    The admin chooses the user's role by name (``admin``, ``doctor``,
    ``patient`` or any custom role registered in the ``roles`` table).
    """

    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role_name: str = Field(min_length=1, max_length=50)
