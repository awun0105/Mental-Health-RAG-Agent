from collections.abc import Mapping
from typing import cast

from supabase import Client

from app.core.constants import AuditAction
from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONRow, JSONValue
from app.schemas.audit import AuditLogResponse


class AuditRepository(BaseRepository[AuditLogResponse]):
    """Repository for audit_logs table."""

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="audit_logs")

    def _to_model(self, row: Mapping[str, JSONValue]) -> AuditLogResponse:
        """Convert a raw audit_logs row into a response model."""
        return AuditLogResponse.model_validate(dict(row))

    def _rows(self, data: object) -> list[JSONRow]:
        """Convert a Supabase response payload into JSON rows."""
        if not isinstance(data, list):
            return []

        rows: list[JSONRow] = []
        for item in data:
            if isinstance(item, dict):
                rows.append(cast(JSONRow, item))

        return rows

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[AuditLogResponse]:
        """List audit logs for a user, newest first."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list audit logs by user") from exc

        return [self._to_model(row) for row in self._rows(result.data)]

    async def list_by_action(
        self,
        action: AuditAction,
        limit: int = 50,
    ) -> list[AuditLogResponse]:
        """List audit logs for a specific action, newest first."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("action", action.value)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list audit logs by action") from exc

        return [self._to_model(row) for row in self._rows(result.data)]

    async def list_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> list[AuditLogResponse]:
        """List audit logs for a specific resource, newest first."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("resource_type", resource_type)
                .eq("resource_id", resource_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list audit logs by resource") from exc

        return [self._to_model(row) for row in self._rows(result.data)]
