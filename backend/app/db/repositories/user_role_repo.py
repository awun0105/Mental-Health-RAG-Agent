from collections.abc import Mapping
from typing import cast

from supabase import Client

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONRow, JSONValue
from app.schemas.rbac import RoleResponse


class UserRoleRepository(BaseRepository[JSONRow]):
    """Repository for the ``user_roles`` junction table."""

    def __init__(self, db: Client, role_table: str = "roles") -> None:
        super().__init__(db=db, table_name="user_roles")
        self._role_table = role_table

    def _to_model(self, row: Mapping[str, JSONValue]) -> JSONRow:
        """Return the raw junction row.

        ``user_roles`` has no surrogate key; callers consume the raw row
        rather than a Pydantic model.
        """
        return cast(JSONRow, dict(row))

    async def assign_role(
        self,
        *,
        user_id: str,
        role_id: str,
        assigned_by: str | None = None,
    ) -> JSONRow:
        """Assign a role to a user. Idempotent: existing pairs are returned unchanged."""
        existing = await self._get_pair(user_id=user_id, role_id=role_id)
        if existing is not None:
            return existing

        data: JSONRow = {
            "user_id": user_id,
            "role_id": role_id,
            "assigned_by": assigned_by,
        }
        try:
            result = self._db.table(self._table_name).insert(data).execute()
        except Exception as exc:
            raise DatabaseError("Failed to assign role to user") from exc

        row = self._first_row(result.data)
        if row is None:
            raise DatabaseError("Assign role returned no data")
        return row

    async def remove_role(self, *, user_id: str, role_id: str) -> bool:
        """Remove a role from a user. Returns ``True`` if a row was deleted."""
        try:
            result = (
                self._db.table(self._table_name)
                .delete()
                .eq("user_id", user_id)
                .eq("role_id", role_id)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to remove role from user") from exc

        return bool(result.data)

    async def get_role_names_for_user(self, user_id: str) -> list[str]:
        """Return the distinct role names assigned to ``user_id``.

        Calls the ``get_user_role_names`` RPC, which performs the
        ``roles`` ⋈ ``user_roles`` join and returns one ``name`` per row.
        Used by ``AuthorizationService`` to resolve roles for service-layer
        resource checks (session ownership, doctor-patient assignment)
        without depending on the legacy ``users.role`` / JWT claim.
        """
        try:
            result = self._db.rpc(
                "get_user_role_names",
                {"p_user_id": user_id},
            ).execute()
        except Exception as exc:
            raise DatabaseError("Failed to resolve user role names") from exc

        names: list[str] = []
        data = result.data
        if not isinstance(data, list):
            return names

        for row in data:
            if isinstance(row, dict):
                name = row.get("name")
                if isinstance(name, str) and name:
                    names.append(name)
            elif isinstance(row, str) and row:
                names.append(row)

        return names

    async def list_roles_for_user(self, user_id: str) -> list[RoleResponse]:
        """Return the user's effective roles by joining via two-step lookup."""
        try:
            junction = (
                self._db.table(self._table_name).select("role_id").eq("user_id", user_id).execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list roles for user") from exc

        role_ids: list[str] = []
        for junction_row in self._rows(junction.data):
            role_id = junction_row.get("role_id")
            if isinstance(role_id, str) and role_id:
                role_ids.append(role_id)

        if not role_ids:
            return []

        roles: list[RoleResponse] = []
        for role_id in role_ids:
            try:
                role_result = (
                    self._db.table(self._role_table)
                    .select("*")
                    .eq("id", role_id)
                    .limit(1)
                    .execute()
                )
            except Exception as exc:
                raise DatabaseError("Failed to fetch role row for user") from exc

            role_row = self._first_row(role_result.data)
            if role_row is not None:
                roles.append(RoleResponse.model_validate(dict(role_row)))

        return roles

    async def _get_pair(self, *, user_id: str, role_id: str) -> JSONRow | None:
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .eq("role_id", role_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch user_role pair") from exc

        return self._first_row(result.data)
