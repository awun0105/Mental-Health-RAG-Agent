from collections.abc import Mapping

from supabase import Client

from app.core.constants import SessionStatus
from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONValue
from app.schemas.session import SessionResponse


class SessionRepository(BaseRepository[SessionResponse]):
    """Repository for chat_sessions table."""

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="chat_sessions")

    def _to_model(self, row: Mapping[str, JSONValue]) -> SessionResponse:
        """Convert a raw chat_sessions row into a response model."""
        return SessionResponse.model_validate(dict(row))

    async def find_active_for_user(self, user_id: str) -> SessionResponse | None:
        """Return the user's currently active session, if any."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .eq("status", SessionStatus.ACTIVE.value)
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch active session for user") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)

    async def list_by_user(
        self,
        user_id: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SessionResponse]:
        """Return a user's sessions ordered by ``started_at`` descending."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("started_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list sessions for user") from exc

        return [self._to_model(row) for row in self._rows(result.data)]
