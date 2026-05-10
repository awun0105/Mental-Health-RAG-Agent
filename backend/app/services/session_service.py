from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.constants import AuditAction, SessionStatus, UserRole
from app.core.exceptions import (
    AlreadyExistsError,
    ConsentRequiredError,
    DatabaseError,
    ForbiddenError,
    NotFoundError,
)
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.base import JSONRow
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.session_repo import SessionRepository
from app.schemas.session import CloseReason, SessionListResponse, SessionResponse
from app.services.audit_service import AuditService
from app.services.authorization_service import AuthorizationService


class SessionService:
    """Service for managing patient chat session lifecycle.

    The Sessions CRUD scope (Milestone 3 sub-scope of M5) covers only:
    start, close, get, and list. Message persistence and AI orchestration
    are added in Milestones 4 and 5.
    """

    def __init__(
        self,
        session_repo: SessionRepository,
        consent_repo: ConsentRepository,
        assignment_repo: AssignmentRepository,
        audit_service: AuditService,
        authorization_service: AuthorizationService,
    ) -> None:
        self._session_repo = session_repo
        self._consent_repo = consent_repo
        self._assignment_repo = assignment_repo
        self._audit_service = audit_service
        self._authz = authorization_service

    async def start_session(
        self,
        *,
        user_id: str,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> SessionResponse:
        """Start a new chat session for a patient.

        Enforces:
          * The caller holds the ``patient`` role in ``user_roles``.
          * The caller has accepted the current consent policy version.
          * The caller does not already have another active session.
        """
        role_names = await self._authz.get_user_role_names(user_id)
        if UserRole.PATIENT.value not in role_names:
            raise ForbiddenError("Only patients can start chat sessions")

        has_consent = await self._consent_repo.has_accepted_version(
            user_id=user_id,
            policy_version=settings.current_consent_policy_version,
        )
        if not has_consent:
            raise ConsentRequiredError()

        existing = await self._session_repo.find_active_for_user(user_id=user_id)
        if existing is not None:
            raise AlreadyExistsError(
                resource="Active chat session",
                identifier=existing.id,
            )

        session_data: JSONRow = {
            "user_id": user_id,
            "status": SessionStatus.ACTIVE.value,
            "metadata": dict(metadata) if metadata else {},
        }

        session = await self._session_repo.create(session_data)

        primary_role = await self._authz.get_primary_role_name(user_id)
        await self._audit_service.log_event(
            user_id=user_id,
            role=primary_role,
            action=AuditAction.SESSION_STARTED,
            resource_type="chat_session",
            resource_id=session.id,
            metadata={"role_at_start": primary_role},
            ip_address=ip_address,
        )

        return session

    async def close_session(
        self,
        *,
        session_id: str,
        current_user_id: str,
        reason: CloseReason = "user_end",
        ip_address: str | None = None,
    ) -> SessionResponse:
        """Close an active chat session.

        Idempotent: closing an already-closed session returns the row
        unchanged and does not emit an extra audit event.
        Only the session's owner patient may close it in this scope.
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(resource="Chat session", resource_id=session_id)

        if session.user_id != current_user_id:
            raise ForbiddenError("Only the session owner can close this session")

        if session.status != SessionStatus.ACTIVE:
            return session

        ended_at = datetime.now(timezone.utc).isoformat()
        update_data: JSONRow = {
            "status": SessionStatus.CLOSED.value,
            "ended_at": ended_at,
        }

        updated = await self._session_repo.update(session_id, update_data)
        if updated is None:
            raise DatabaseError("Close session returned no data")

        primary_role = await self._authz.get_primary_role_name(current_user_id)
        await self._audit_service.log_event(
            user_id=current_user_id,
            role=primary_role,
            action=AuditAction.SESSION_CLOSED,
            resource_type="chat_session",
            resource_id=updated.id,
            metadata={"reason": reason},
            ip_address=ip_address,
        )

        return updated

    async def get_session(
        self,
        *,
        session_id: str,
        current_user_id: str,
    ) -> SessionResponse:
        """Return a single session, enforcing RBAC.

        Roles are resolved from the ``user_roles`` junction (via
        ``AuthorizationService``) rather than from the legacy ``users.role``
        column or the JWT claim:

        * Patient: must be the owner.
        * Doctor: must have an active assignment to the session's patient.
        * Admin: not authorised in this scope (deferred to M5).
        """
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(resource="Chat session", resource_id=session_id)

        role_names = await self._authz.get_user_role_names(current_user_id)

        if UserRole.PATIENT.value in role_names:
            if session.user_id != current_user_id:
                raise ForbiddenError("Patients can only access their own sessions")
            return session

        if UserRole.DOCTOR.value in role_names:
            is_assigned = await self._assignment_repo.is_assigned(
                doctor_id=current_user_id,
                patient_id=session.user_id,
            )
            if not is_assigned:
                raise ForbiddenError("Doctor is not assigned to this patient")
            return session

        raise ForbiddenError("Not allowed to access chat sessions")

    async def list_sessions_for_user(
        self,
        *,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> SessionListResponse:
        """List a user's own sessions, newest first."""
        items = await self._session_repo.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        return SessionListResponse(items=items, limit=limit, offset=offset)
