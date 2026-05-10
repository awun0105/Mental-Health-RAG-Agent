from datetime import UTC, datetime, timedelta
from typing import ClassVar

from app.core.exceptions import ForbiddenError
from app.db.repositories.permission_repo import PermissionRepository
from app.db.repositories.user_role_repo import UserRoleRepository


class AuthorizationService:
    """Resolve and enforce permissions and roles for the current user.

    Backed by two Postgres RPCs:

      * ``get_user_permission_codes`` — joins ``permissions`` ⋈
        ``role_permissions`` ⋈ ``user_roles`` and returns the codes
        granted to the user. Used for route-level
        :func:`require_permission` checks.
      * ``get_user_role_names`` — joins ``roles`` ⋈ ``user_roles`` and
        returns the role names held by the user. Used for service-layer
        resource scoping (e.g. patient-vs-doctor branching in
        ``SessionService.get_session``) so resource checks no longer
        depend on the legacy ``users.role`` / JWT ``role`` claim.

    Both lookups are protected by a small in-memory TTL cache (5 minutes
    by default). The cache is process-local — same pattern as
    ``AuthService._pending_tokens`` — and is intentionally not Redis-backed
    because the MVP runs single-process. Mutations to user roles or role
    permissions should call :meth:`invalidate_cache` so the next request
    re-resolves both the user's effective permissions and roles.
    """

    # Class-level so the caches are shared across request-scoped service
    # instances within the same process.
    _cache: ClassVar[dict[str, tuple[set[str], datetime]]] = {}
    _role_cache: ClassVar[dict[str, tuple[set[str], datetime]]] = {}

    DEFAULT_TTL_SECONDS: ClassVar[int] = 300

    # Stable ordering for ``get_primary_role_name``. Roles outside this
    # list fall back to alphabetical order so the result is deterministic.
    _ROLE_PRIORITY: ClassVar[tuple[str, ...]] = ("admin", "doctor", "patient")

    def __init__(
        self,
        permission_repo: PermissionRepository,
        user_role_repo: UserRoleRepository,
        cache_ttl_seconds: int | None = None,
    ) -> None:
        self._permission_repo = permission_repo
        self._user_role_repo = user_role_repo
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

    async def get_user_role_names(self, user_id: str) -> set[str]:
        """Return the set of role names assigned to ``user_id``.

        Reads from the in-memory cache when fresh; otherwise resolves via
        the ``get_user_role_names`` RPC and caches the result.
        """
        cached = self._role_cache.get(user_id)
        now = datetime.now(UTC)
        if cached is not None:
            roles, cached_at = cached
            if now - cached_at < timedelta(seconds=self._cache_ttl_seconds):
                return roles

        names = await self._user_role_repo.get_role_names_for_user(user_id)
        roles = set(names)
        self._role_cache[user_id] = (roles, now)
        return roles

    async def get_primary_role_name(self, user_id: str) -> str | None:
        """Return a single canonical role name for ``user_id``, or ``None``.

        Used for audit logging where a single string column captures the
        actor's role at event time. Resolution order:

        1. ``admin`` if held.
        2. ``doctor`` if held.
        3. ``patient`` if held.
        4. The alphabetically-first remaining role, if any.
        5. ``None`` when the user holds no roles at all.
        """
        roles = await self.get_user_role_names(user_id)
        if not roles:
            return None
        for priority_role in self._ROLE_PRIORITY:
            if priority_role in roles:
                return priority_role
        return min(roles)

    def invalidate_cache(self, user_id: str) -> None:
        """Drop the cached permission set and role set for a user.

        Call this after assigning or removing a role on a user, or after
        granting or revoking a permission on a role the user holds.
        """
        self._cache.pop(user_id, None)
        self._role_cache.pop(user_id, None)

    @classmethod
    def clear_cache(cls) -> None:
        """Drop the entire process-local caches (test/maintenance helper)."""
        cls._cache.clear()
        cls._role_cache.clear()
