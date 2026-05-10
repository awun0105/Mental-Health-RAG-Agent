from collections.abc import Mapping

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONValue
from app.schemas.rbac import RoleResponse
from supabase import Client


class RoleRepository(BaseRepository[RoleResponse]):
    """Repository for the ``roles`` table."""

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="roles")

    def _to_model(self, row: Mapping[str, JSONValue]) -> RoleResponse:
        """Convert a raw roles row into a public response model."""
        return RoleResponse.model_validate(dict(row))

    async def get_by_name(self, name: str) -> RoleResponse | None:
        """Fetch a role by its unique ``name`` (e.g. ``admin``)."""
        try:
            result = (
                self._db.table(self._table_name).select("*").eq("name", name).limit(1).execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch role by name") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)

    async def list_all(self) -> list[RoleResponse]:
        """List every role, ordered by ``name``."""
        try:
            result = self._db.table(self._table_name).select("*").order("name").execute()
        except Exception as exc:
            raise DatabaseError("Failed to list roles") from exc

        return [self._to_model(row) for row in self._rows(result.data)]
