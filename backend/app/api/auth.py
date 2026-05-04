from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service, get_current_user
from app.core.constants import UserRole
from app.core.security import CurrentUserClaims
from app.schemas.user import (
    PublicUserRegister,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    payload: PublicUserRegister,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new patient via public self-registration.

    Only patients may self-register through this endpoint. Doctor and admin
    accounts are provisioned through privileged admin flows so this endpoint
    cannot be used to escalate privileges by passing ``role`` in the body.
    """
    user_data = UserCreate(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=UserRole.PATIENT,
    )
    return await auth_service.register(user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Login a local user and return an app JWT."""
    return await auth_service.login(payload)


@router.get("/me")
async def me(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    """Return current authenticated user claims."""
    return current_user
