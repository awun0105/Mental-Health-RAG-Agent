from app.core.config import settings
from app.core.constants import AuditAction
from app.db.repositories.base import JSONRow
from app.db.repositories.consent_repo import ConsentRepository
from app.schemas.consent import (
    ConsentAcceptRequest,
    ConsentResponse,
    ConsentStatusResponse,
)
from app.services.audit_service import AuditService


class ConsentService:
    """Service for managing user consent records."""

    def __init__(
        self,
        consent_repo: ConsentRepository,
        audit_service: AuditService,
    ) -> None:
        self._consent_repo = consent_repo
        self._audit_service = audit_service

    async def accept_consent(
        self,
        user_id: str,
        payload: ConsentAcceptRequest,
        ip_address: str | None = None,
    ) -> ConsentResponse:
        """Accept a consent policy version for a user."""
        consent_data: JSONRow = {
            "user_id": user_id,
            "policy_version": payload.policy_version,
            "accepted": True,
        }

        consent = await self._consent_repo.create(consent_data)

        await self._audit_service.log_event(
            user_id=user_id,
            action=AuditAction.CONSENT_ACCEPTED,
            resource_type="consent_record",
            resource_id=consent.id,
            metadata={
                "policy_version": payload.policy_version,
                "accepted": True,
            },
            ip_address=ip_address,
        )

        return consent

    async def get_status(self, user_id: str) -> ConsentStatusResponse:
        """Return whether the user has accepted the current policy version."""
        current_policy_version = settings.current_consent_policy_version

        has_valid_consent = await self._consent_repo.has_accepted_version(
            user_id=user_id,
            policy_version=current_policy_version,
        )

        latest = await self._consent_repo.get_latest_by_user(user_id=user_id)

        latest_accepted_policy_version: str | None = None
        if latest is not None and latest.accepted:
            latest_accepted_policy_version = latest.policy_version

        return ConsentStatusResponse(
            has_valid_consent=has_valid_consent,
            current_policy_version=current_policy_version,
            latest_accepted_policy_version=latest_accepted_policy_version,
        )
