from collections.abc import Mapping

from supabase import Client

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONValue
from app.schemas.rbac import PermissionResponse


class PermissionRepository(BaseRepository[PermissionResponse]):
    """Repository for the ``permissions`` table."""

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="permissions")

    def _to_model(self, row: Mapping[str, JSONValue]) -> PermissionResponse:
        """Convert a raw permissions row into a public response model."""
        return PermissionResponse.model_validate(dict(row))

    async def list_all(self) -> list[PermissionResponse]:
        """List every permission, ordered by ``code``."""
        try:
            result = self._db.table(self._table_name).select("*").order("code").execute()
        except Exception as exc:
            raise DatabaseError("Failed to list permissions") from exc

        return [self._to_model(row) for row in self._rows(result.data)]

    async def get_permission_codes_for_user(self, user_id: str) -> list[str]:
        """Return the distinct permission codes effective for a user.

        Calls the ``get_user_permission_codes`` RPC function in Postgres,
        which performs the ``permissions`` ⋈ ``role_permissions`` ⋈
        ``user_roles`` join and returns one ``code`` per row.
        """
        try:
            result = self._db.rpc(
                "get_user_permission_codes",
                {"p_user_id": user_id},
            ).execute()
        except Exception as exc:
            raise DatabaseError("Failed to resolve user permissions") from exc

        codes: list[str] = []
        data = result.data
        if not isinstance(data, list):
            return codes

        for row in data:
            if isinstance(row, dict):
                code = row.get("code")
                if isinstance(code, str) and code:
                    codes.append(code)
            elif isinstance(row, str) and row:
                codes.append(row)

        return codes
