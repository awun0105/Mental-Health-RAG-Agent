from app.core.constants import MessageRole, SessionStatus, UserRole
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.repositories.message_repo import MessageRepository
from app.db.repositories.session_repo import SessionRepository
from app.schemas.message import MessageListResponse, MessageResponse
from app.schemas.session import SessionResponse
from app.services.authorization_service import AuthorizationService


class MessageService:
    """Service for patient transcript persistence.

    HR-003 exposes only patient-created messages. Assistant, system, and doctor
    sender roles are reserved for later agent/clinical workflows.
    """

    def __init__(
        self,
        *,
        message_repo: MessageRepository,
        session_repo: SessionRepository,
        authorization_service: AuthorizationService,
    ) -> None:
        self._message_repo = message_repo
        self._session_repo = session_repo
        self._authz = authorization_service

    async def list_messages_for_session(
        self,
        *,
        session_id: str,
        current_user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> MessageListResponse:
        """List messages for an owned patient session."""
        await self._require_patient_session_owner(
            session_id=session_id,
            current_user_id=current_user_id,
        )
        items = await self._message_repo.list_for_session(
            session_id=session_id,
            limit=limit,
            offset=offset,
        )
        return MessageListResponse(items=items, limit=limit, offset=offset)

    async def create_patient_message(
        self,
        *,
        session_id: str,
        current_user_id: str,
        content: str,
    ) -> MessageResponse:
        """Create a patient-authored message in an active owned session."""
        session = await self._require_patient_session_owner(
            session_id=session_id,
            current_user_id=current_user_id,
        )
        if session.status != SessionStatus.ACTIVE:
            raise ForbiddenError("Cannot add messages to a closed session")

        return await self._message_repo.create(
            {
                "session_id": session_id,
                "role": MessageRole.PATIENT.value,
                "content": content,
            },
        )

    async def _require_patient_session_owner(
        self,
        *,
        session_id: str,
        current_user_id: str,
    ) -> SessionResponse:
        session = await self._session_repo.get_by_id(session_id)
        if session is None:
            raise NotFoundError(resource="Chat session", resource_id=session_id)

        role_names = await self._authz.get_user_role_names(current_user_id)
        if UserRole.PATIENT.value not in role_names:
            raise ForbiddenError("Only patients can access patient transcripts in this scope")

        if session.user_id != current_user_id:
            raise ForbiddenError("Patients can only access their own session messages")

        return session
