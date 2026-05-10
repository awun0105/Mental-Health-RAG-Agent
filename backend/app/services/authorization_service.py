from datetime import UTC, datetime, timedelta
from typing import ClassVar

from app.core.exceptions import ForbiddenError
from app.db.repositories.assignment_repo import AssignmentRepository
from app.db.repositories.permission_repo import PermissionRepository


class AuthorizationService:
    """Resolve and enforce permissions for the current user.

    Backed by the ``permissions`` ⋈ ``role_permissions`` ⋈ ``user_roles``
    join exposed via the ``get_user_permission_codes`` Postgres RPC.

    A simple in-memory TTL cache (5 minutes by default) avoids hitting
    the database on every request. The cache is process-local — same
    pattern as ``AuthService._pending_tokens`` — and is intentionally
    not Redis-backed because the MVP runs single-process. Mutations to
    user roles or role permissions should call ``invalidate_cache`` so
    the next request re-resolves the user's effective permissions.
    """

    # Class-level so the cache is shared across request-scoped service
    # instances within the same process.
    _cache: ClassVar[dict[str, tuple[set[str], datetime]]] = {}

    DEFAULT_TTL_SECONDS: ClassVar[int] = 300

    def __init__(
        self,
        permission_repo: PermissionRepository,
        assignment_repo: AssignmentRepository,
        cache_ttl_seconds: int | None = None,
    ) -> None:
        self._permission_repo = permission_repo
        self._assignment_repo = assignment_repo
        self._cache_ttl_seconds: int = (
            cache_ttl_seconds if cache_ttl_seconds is not None else self.DEFAULT_TTL_SECONDS
        )

    async def get_user_permissions(self, user_id: str) -> set[str]:
        """Return the set of permission codes effective for ``user_id``.

        Reads from the in-memory cache when fresh; otherwise resolves via
        the ``get_user_permission_codes`` RPC and caches the result.
        """
        cached = self._cache.get(user_id)
        now = datetime.now(UTC)
        if cached is not None:
            permissions, cached_at = cached
            if now - cached_at < timedelta(seconds=self._cache_ttl_seconds):
                return permissions

        codes = await self._permission_repo.get_permission_codes_for_user(user_id)
        permissions = set(codes)
        self._cache[user_id] = (permissions, now)
        return permissions

    async def require_permission(
        self,
        user_id: str,
        permission_code: str,
    ) -> None:
        """Raise ``ForbiddenError`` if ``user_id`` lacks ``permission_code``."""
        permissions = await self.get_user_permissions(user_id)
        if permission_code not in permissions:
            raise ForbiddenError(f"Missing permission: {permission_code}")

    def invalidate_cache(self, user_id: str) -> None:
        """Drop the cached permission set for a user.

        Call this after assigning or removing a role on a user, or after
        granting or revoking a permission on a role the user holds.
        """
        self._cache.pop(user_id, None)

    @classmethod
    def clear_cache(cls) -> None:
        """Drop the entire process-local cache (test/maintenance helper)."""
        cls._cache.clear()
