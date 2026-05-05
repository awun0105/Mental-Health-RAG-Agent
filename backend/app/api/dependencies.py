from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.core.constants import UserRole
from app.core.security import (
    CurrentUserClaims,
    decode_access_token,
    require_admin,
    require_doctor,
    require_patient,
    require_roles,
)
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.message_repo import MessageRepository
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.user_repo import UserRepository
from app.db.supabase_client import get_supabase_client
from app.services.assignment_service import AssignmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.consent_service import ConsentService
from app.services.session_service import SessionService

bearer_scheme = HTTPBearer(auto_error=True)


def get_supabase() -> Client:
    """Return the shared Supabase client."""
    return get_supabase_client()


def get_user_repo(
    db: Annotated[Client, Depends(get_supabase)],
) -> UserRepository:
    """Return a user repository instance."""
    return UserRepository(db=db)


def get_consent_repo(
    db: Annotated[Client, Depends(get_supabase)],
) -> ConsentRepository:
    """Return a consent repository instance."""
    return ConsentRepository(db=db)


def get_audit_repo(
    db: Annotated[Client, Depends(get_supabase)],
) -> AuditRepository:
    """Return an audit repository instance."""
    return AuditRepository(db=db)


def get_assignment_repo(
    db: Annotated[Client, Depends(get_supabase)],
) -> AssignmentRepository:
    """Return an assignment repository instance."""
    return AssignmentRepository(db=db)


def get_session_repo(
    db: Annotated[Client, Depends(get_supabase)],
) -> SessionRepository:
    """Return a session repository instance."""
    return SessionRepository(db=db)


def get_message_repo(
    db: Annotated[Client, Depends(get_supabase)],
) -> MessageRepository:
    """Return a message repository instance."""
    return MessageRepository(db=db)


def get_audit_service(
    audit_repo: Annotated[AuditRepository, Depends(get_audit_repo)],
) -> AuditService:
    """Return an audit service instance."""
    return AuditService(audit_repo=audit_repo)


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    supabase: Annotated[Client, Depends(get_supabase)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> AuthService:
    """Return an auth service instance."""
    return AuthService(
        user_repo=user_repo,
        supabase=supabase,
        audit_service=audit_service,
    )


def get_consent_service(
    consent_repo: Annotated[ConsentRepository, Depends(get_consent_repo)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> ConsentService:
    """Return a consent service instance."""
    return ConsentService(
        consent_repo=consent_repo,
        audit_service=audit_service,
    )


def get_assignment_service(
    assignment_repo: Annotated[AssignmentRepository, Depends(get_assignment_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> AssignmentService:
    """Return an assignment service instance."""
    return AssignmentService(
        assignment_repo=assignment_repo,
        user_repo=user_repo,
        audit_service=audit_service,
    )


def get_session_service(
    session_repo: Annotated[SessionRepository, Depends(get_session_repo)],
    consent_repo: Annotated[ConsentRepository, Depends(get_consent_repo)],
    assignment_repo: Annotated[AssignmentRepository, Depends(get_assignment_repo)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> SessionService:
    """Return a session service instance."""
    return SessionService(
        session_repo=session_repo,
        consent_repo=consent_repo,
        assignment_repo=assignment_repo,
        audit_service=audit_service,
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
) -> CurrentUserClaims:
    """Return current authenticated user claims from bearer token."""
    return decode_access_token(credentials.credentials)


def require_current_admin(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    """Require current user to be an admin."""
    require_admin(current_user)
    return current_user


def require_current_doctor(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    """Require current user to be a doctor."""
    require_doctor(current_user)
    return current_user


def require_current_patient(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    """Require current user to be a patient."""
    require_patient(current_user)
    return current_user


def require_current_doctor_or_admin(
    current_user: Annotated[CurrentUserClaims, Depends(get_current_user)],
) -> CurrentUserClaims:
    """Require current user to be a doctor or admin."""
    require_roles(current_user, {UserRole.DOCTOR, UserRole.ADMIN})
    return current_user
