from collections.abc import Mapping
from typing import cast

from supabase import Client

from app.core.constants import AuthProvider, UserRole
from app.core.exceptions import DatabaseError
from app.db.repositories.base import BaseRepository, JSONRow, JSONValue
from app.schemas.user import UserResponse


class UserRepository(BaseRepository[UserResponse]):
    """Repository for application users.

    This repository owns all direct database access for the `users` table.
    """

    def __init__(self, db: Client) -> None:
        super().__init__(db=db, table_name="users")

    def _to_model(self, row: Mapping[str, JSONValue]) -> UserResponse:
        """Convert a raw users row into a public user response model."""
        return UserResponse.model_validate(dict(row))

    def _rows(self, data: object) -> list[JSONRow]:
        """Convert a Supabase response payload into a list of JSON rows."""
        if not isinstance(data, list):
            return []

        rows: list[JSONRow] = []
        for item in data:
            if isinstance(item, dict):
                rows.append(cast(JSONRow, item))

        return rows

    async def get_by_email(self, email: str) -> JSONRow | None:
        """Fetch raw user data by email.

        This returns a raw row because auth login needs `password_hash`,
        which must not be exposed through UserResponse.
        """
        try:
            result = self._db.table(self._table_name).select("*").eq("email", email).execute()
        except Exception as exc:
            raise DatabaseError("Failed to fetch user by email") from exc

        return self._first_row(result.data)

    async def email_exists(self, email: str) -> bool:
        """Return True when a user with the given email already exists."""
        try:
            result = (
                self._db.table(self._table_name).select("id").eq("email", email).limit(1).execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to check whether email exists") from exc

        return self._first_row(result.data) is not None

    async def get_by_auth_user_id(self, auth_user_id: str) -> JSONRow | None:
        """Fetch raw user data by Supabase Auth user ID."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("auth_user_id", auth_user_id)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch user by Supabase Auth user ID") from exc

        return self._first_row(result.data)

    async def get_by_provider_identity(
        self,
        auth_provider: AuthProvider,
        provider_user_id: str,
    ) -> JSONRow | None:
        """Fetch raw user data by OAuth provider and provider user ID."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("auth_provider", auth_provider.value)
                .eq("provider_user_id", provider_user_id)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to fetch user by provider identity") from exc

        return self._first_row(result.data)

    async def list_by_role(self, role: UserRole) -> list[UserResponse]:
        """List active users with a specific role."""
        try:
            result = (
                self._db.table(self._table_name)
                .select("*")
                .eq("role", role.value)
                .eq("is_active", True)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to list users by role") from exc

        return [self._to_model(row) for row in self._rows(result.data)]

    async def deactivate(self, user_id: str) -> UserResponse | None:
        """Soft-deactivate a user account."""
        return await self.update(user_id, {"is_active": False})
