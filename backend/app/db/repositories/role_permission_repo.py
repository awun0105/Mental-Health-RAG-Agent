from collections.abc import Mapping
from typing import cast

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONRow, JSONValue
from app.schemas.rbac import PermissionResponse
from supabase import Client


class RolePermissionRepository(BaseRepository[JSONRow]):
    """Repository for the ``role_permissions`` junction table."""

    def __init__(self, db: Client, permission_table: str = "permissions") -> None:
        super().__init__(db=db, table_name="role_permissions")
        self._permission_table = permission_table

    def _to_model(self, row: Mapping[str, JSONValue]) -> JSONRow:
        """Return the raw junction row.

        ``role_permissions`` has no surrogate key; callers consume the
        raw row rather than a Pydantic model.
        """
        return cast(JSONRow, dict(row))

    async def assign_permission(
        self,
        *,
        role_id: str,
        permission_id: str,
        granted_by: str | None = None,
    ) -> JSONRow:
        """Grant a permission to a role. Idempotent: existing pairs are returned unchanged."""
        existing = await self._get_pair(role_id=role_id, permission_id=permission_id)
        if existing is not None:
            return existing

        data: JSONRow = {
            "role_id": role_id,
            "permission_id": permission_id,
            "granted_by": granted_by,
        }
        try:
            result = self._db.table(self._table_name).insert(data).execute()
        except Exception as exc:
            raise DatabaseError("Failed to assign permission to role") from exc

        row = self._first_row(result.data)
        if row is None:
            raise DatabaseError("Assign permission returned no data")
        return row

    async def remove_permission(
        self,
        *,
        role_id: str,
        permission_id: str,
    ) -> bool:
        """Revoke a permission from a role. Returns ``True`` if a row was deleted."""
        try:
            result = (
                self._db.table(self._table_name)
                .delete()
                .eq("role_id", role_id)
                .eq("permission_id", permission_id)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to remove permission from role") from exc

        return bool(result.data)

    async def list_permissions_for_role(self, role_id: str) -> list[PermissionResponse]:
        """Return the permissions granted to a role."""
        try:
            junction = (
                self._db.table(self._table_name)
                .select("permission_id")
                .eq("role_id", role_id)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list permissions for role") from exc

        permission_ids: list[str] = []
        for junction_row in self._rows(junction.data):
            permission_id = junction_row.get("permission_id")
            if isinstance(permission_id, str) and permission_id:
                permission_ids.append(permission_id)

        if not permission_ids:
            return []

        permissions: list[PermissionResponse] = []
        for permission_id in permission_ids:
            try:
                perm_result = (
                    self._db.table(self._permission_table)
                    .select("*")
                    .eq("id", permission_id)
                    .limit(1)
                    .execute()
                )
            except Exception as exc:
                raise DatabaseError("Failed to fetch permission row") from exc

            perm_row = self._first_row(perm_result.data)
            if perm_row is not None:
                permissions.append(PermissionResponse.model_validate(dict(perm_row)))

        return permissions

    async def _get_pair(
        self,
        *,
        role_id: str,
        permission_id: str,
    ) -> JSONRow | None:
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("role_id", role_id)
                .eq("permission_id", permission_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch role_permission pair") from exc

        return self._first_row(result.data)
