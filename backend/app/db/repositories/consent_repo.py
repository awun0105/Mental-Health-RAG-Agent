from collections.abc import Mapping

from supabase import Client

from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONValue
from app.schemas.consent import ConsentResponse


class ConsentRepository(BaseRepository[ConsentResponse]):
    """Repository for consent_records table."""

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="consent_records")

    def _to_model(self, row: Mapping[str, JSONValue]) -> ConsentResponse:
        """Convert a raw consent_records row into a response model."""
        return ConsentResponse.model_validate(dict(row))

    async def get_latest_by_user(self, user_id: str) -> ConsentResponse | None:
        """Return the most recent consent record for a user."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("accepted_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch latest consent record") from exc

        row = self._first_row(result.data)
        if row is None:
            return None

        return self._to_model(row)

    async def has_accepted_version(self, user_id: str, policy_version: str) -> bool:
        """Return True when a user has accepted a specific policy version."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("id")
                .eq("user_id", user_id)
                .eq("policy_version", policy_version)
                .eq("accepted", True)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to check consent policy version") from exc

        return self._first_row(result.data) is not None

    async def list_by_user(self, user_id: str) -> list[ConsentResponse]:
        """List all consent records for a user, newest first."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("accepted_at", desc=True)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list consent records") from exc

        return [self._to_model(row) for row in self._rows(result.data)]
