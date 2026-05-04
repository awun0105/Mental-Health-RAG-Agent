from typing import Any

from app.core.constants import AuditAction
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.base import JSONRow, JSONValue


class AuditService:
    """Service responsible for writing audit logs in a consistent way."""

    def __init__(self, audit_repo: AuditRepository) -> None:
        self._audit_repo = audit_repo

    async def log_event(
        self,
        *,
        user_id: str | None,
        action: AuditAction,
        role: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Create an audit log entry.

        This method should be the only way to write audit logs.

        ``role`` is the role of the actor at the time of the event
        (``patient``, ``doctor``, ``admin``, ``system`` or ``None``).
        It is recorded alongside ``user_id`` so that downstream dashboards
        can filter audit events by role without joining ``users``.
        """

        safe_metadata: dict[str, JSONValue] | None = None
        if metadata is not None:
            safe_metadata = self._sanitize_metadata(metadata)

        data: JSONRow = {
            "user_id": user_id,
            "role": role,
            "action": action.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metadata": safe_metadata,
            "ip_address": ip_address,
        }

        # fire-and-forget style (no return needed)
        await self._audit_repo.create(data)

    def _sanitize_metadata(
        self,
        metadata: dict[str, Any],
    ) -> dict[str, JSONValue]:
        """Sanitize metadata to ensure it is JSON-safe and does not leak sensitive data."""

        sanitized: dict[str, JSONValue] = {}

        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                sanitized[key] = value
            else:
                # fallback to string representation
                sanitized[key] = str(value)

        return sanitized
