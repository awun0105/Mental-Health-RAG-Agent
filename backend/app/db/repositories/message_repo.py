from collections.abc import Mapping

from supabase import Client

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONValue
from app.schemas.message import MessageResponse


class MessageRepository(BaseRepository[MessageResponse]):
    """Repository for chat_messages table.

    The Sessions CRUD scope does not expose a write/read HTTP route for
    messages. The repository is included here so that the agent pipelines
    introduced in Milestones 4 and 5 can persist messages without further
    refactoring.
    """

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="chat_messages")

    def _to_model(self, row: Mapping[str, JSONValue]) -> MessageResponse:
        """Convert a raw chat_messages row into a response model."""
        return MessageResponse.model_validate(dict(row))

    async def list_for_session(
        self,
        session_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MessageResponse]:
        """Return messages for a session ordered by ``created_at`` ascending."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list messages for session") from exc

        return [self._to_model(row) for row in self._rows(result.data)]
