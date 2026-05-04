from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Generic, TypeAlias, TypeVar, cast

from supabase import Client

from app.core.exceptions import DatabaseError

JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]

JSONRow: TypeAlias = dict[str, JSONValue]

ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[ModelT]):
    """Base repository for Supabase table access."""

    def __init__(self, db: Client, table_name: str) -> None:
        self._db: Client = db
        self._table_name: str = table_name

    @abstractmethod
    def _to_model(self, row: Mapping[str, JSONValue]) -> ModelT:
        """Convert a raw database row into a typed schema/model."""
        raise NotImplementedError

    def _first_row(self, data: object) -> JSONRow | None:
        """Return the first row from a Supabase response payload."""
        if not isinstance(data, list) or not data:
            return None

        first_item: object = data[0]
        if not isinstance(first_item, dict):
            return None

        return cast(JSONRow, first_item)

    def _rows(self, data: object) -> list[JSONRow]:
        """Return all rows from a Supabase response payload.

        Returns an empty list when the payload is missing or malformed,
        so callers can iterate safely without nil-checks.
        """
        if not isinstance(data, list):
            return []

        rows: list[JSONRow] = []
        for item in data:
            if isinstance(item, dict):
                rows.append(cast(JSONRow, item))

        return rows

    async def get_by_id(self, record_id: str) -> ModelT | None:
        """Fetch one record by primary key."""
        try:
            result = self._db.table(self._table_name).select("*").eq("id", record_id).execute()
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch {self._table_name} by id") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)

    async def create(self, data: JSONRow) -> ModelT:
        """Insert one record and return the created model."""
        try:
            result = self._db.table(self._table_name).insert(data).execute()
        except Exception as exc:
            raise DatabaseError(f"Failed to create {self._table_name} record") from exc

        row = self._first_row(result.data)
        if row is None:
            raise DatabaseError(f"Create {self._table_name} returned no data")

        return self._to_model(row)

    async def update(self, record_id: str, data: JSONRow) -> ModelT | None:
        """Update one record by primary key and return the updated model."""
        try:
            result = self._db.table(self._table_name).update(data).eq("id", record_id).execute()
        except Exception as exc:
            raise DatabaseError(f"Failed to update {self._table_name} record") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)

    async def delete(self, record_id: str) -> bool:
        """Delete one record by primary key."""
        try:
            result = self._db.table(self._table_name).delete().eq("id", record_id).execute()
        except Exception as exc:
            raise DatabaseError(f"Failed to delete {self._table_name} record") from exc

        return bool(result.data)
