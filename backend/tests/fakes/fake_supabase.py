"""In-memory stand-in for the supabase Client used in repository unit tests.

This intentionally implements only the chain API actually used by the
repositories in this codebase, namely:

    client.table(name).select(...).eq(...).order(...).limit(...).execute()
    client.table(name).select(...).eq(...).order(...).range(start, end).execute()
    client.table(name).insert(data).execute()
    client.table(name).update(data).eq(...).execute()
    client.table(name).delete().eq(...).execute()

It also exposes a small ``auth`` stub that mirrors the two methods used
by ``AuthService`` for Google OAuth:

    client.auth.sign_in_with_oauth({"provider": "google", "options": {...}})
    client.auth.exchange_code_for_session({"auth_code": "..."})

It is **not** a full reimplementation of supabase-py. If a repository or
service starts using a method that this fake does not support, the call
will raise ``NotImplementedError`` so the gap is visible immediately.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


class _FakeResult:
    """Minimal stand-in for ``postgrest.APIResponse``."""

    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    """Mutable query builder that mirrors the supabase chain API."""

    def __init__(self, store: FakeSupabase, table: str) -> None:
        self._store = store
        self._table = table
        self._op: str = ""
        self._eq_filters: list[tuple[str, Any]] = []
        self._order_col: str | None = None
        self._order_desc: bool = False
        self._limit: int | None = None
        self._range: tuple[int, int] | None = None
        self._payload: dict[str, Any] | None = None

    def select(self, *_cols: str) -> _FakeQuery:
        self._op = "select"
        return self

    def insert(self, payload: dict[str, Any]) -> _FakeQuery:
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict[str, Any]) -> _FakeQuery:
        self._op = "update"
        self._payload = payload
        return self

    def delete(self) -> _FakeQuery:
        self._op = "delete"
        return self

    def eq(self, col: str, value: Any) -> _FakeQuery:
        self._eq_filters.append((col, value))
        return self

    def order(self, col: str, *, desc: bool = False) -> _FakeQuery:
        self._order_col = col
        self._order_desc = desc
        return self

    def limit(self, n: int) -> _FakeQuery:
        self._limit = n
        return self

    def range(self, start: int, end: int) -> _FakeQuery:
        """Mirror ``postgrest`` inclusive ``range(start, end)`` pagination."""
        self._range = (start, end)
        return self

    def execute(self) -> _FakeResult:
        rows = self._store.tables.setdefault(self._table, [])

        if self._op == "select":
            return self._execute_select(rows)
        if self._op == "insert":
            return self._execute_insert(rows)
        if self._op == "update":
            return self._execute_update(rows)
        if self._op == "delete":
            return self._execute_delete(rows)

        raise NotImplementedError(f"FakeSupabase does not support op {self._op!r}")

    def _matches(self, row: dict[str, Any]) -> bool:
        return all(row.get(col) == val for col, val in self._eq_filters)

    def _execute_select(self, rows: list[dict[str, Any]]) -> _FakeResult:
        filtered = [r for r in rows if self._matches(r)]
        if self._order_col is not None:
            order_col = self._order_col
            filtered = sorted(
                filtered,
                key=lambda r: r.get(order_col) or "",
                reverse=self._order_desc,
            )
        if self._range is not None:
            start, end = self._range
            filtered = filtered[start : end + 1]
        if self._limit is not None:
            filtered = filtered[: self._limit]
        return _FakeResult([deepcopy(r) for r in filtered])

    def _execute_insert(self, rows: list[dict[str, Any]]) -> _FakeResult:
        if self._payload is None:
            raise ValueError("insert() called without payload")

        now = datetime.now(UTC).isoformat()
        row: dict[str, Any] = dict(self._payload)
        row.setdefault("id", str(uuid4()))
        row.setdefault("created_at", now)

        if self._table == "users":
            row.setdefault("updated_at", now)
        if self._table == "consent_records":
            row.setdefault("accepted_at", now)
        if self._table == "chat_sessions":
            row.setdefault("started_at", now)
            row.setdefault("status", "active")
            row.setdefault("metadata", {})
            row.setdefault("ended_at", None)
        if self._table == "chat_messages":
            row.setdefault("safety_flag", False)
            row.setdefault("safety_severity", "none")
            row.setdefault("trace_id", None)

        rows.append(row)
        return _FakeResult([deepcopy(row)])

    def _execute_update(self, rows: list[dict[str, Any]]) -> _FakeResult:
        if self._payload is None:
            raise ValueError("update() called without payload")

        updated: list[dict[str, Any]] = []
        for r in rows:
            if self._matches(r):
                r.update(self._payload)
                if self._table == "users":
                    r["updated_at"] = datetime.now(UTC).isoformat()
                updated.append(deepcopy(r))
        return _FakeResult(updated)

    def _execute_delete(self, rows: list[dict[str, Any]]) -> _FakeResult:
        kept: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        for r in rows:
            if self._matches(r):
                removed.append(deepcopy(r))
            else:
                kept.append(r)
        self._store.tables[self._table] = kept
        return _FakeResult(removed)


@dataclass
class _FakeSupabaseUser:
    """Minimal stand-in for the ``user`` object on ``AuthResponse``."""

    id: str
    email: str
    user_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class _FakeOAuthResponse:
    """Stand-in for the response of ``auth.sign_in_with_oauth``."""

    url: str
    provider: str = "google"


@dataclass
class _FakeAuthResponse:
    """Stand-in for the response of ``auth.exchange_code_for_session``.

    Only the ``user`` attribute is consumed by ``AuthService``.
    """

    user: _FakeSupabaseUser


class _FakeSupabaseAuth:
    """Stub of ``client.auth`` exposing only the methods we use.

    Tests configure the stub by setting ``next_oauth_url`` (returned by
    ``sign_in_with_oauth``) and ``next_callback_user`` (returned by
    ``exchange_code_for_session``). To simulate a Supabase failure, set
    ``exchange_should_fail = True`` so the call raises ``RuntimeError``.

    This intentionally does NOT validate the input dict shape — that
    contract belongs to the real client; tests only need the response
    side mocked deterministically.
    """

    def __init__(self) -> None:
        self.next_oauth_url: str = "https://accounts.google.com/o/oauth2/auth?fake"
        self.next_callback_user: _FakeSupabaseUser | None = None
        self.exchange_should_fail: bool = False
        self.last_oauth_options: dict[str, Any] | None = None
        self.last_exchange_code: str | None = None

    def sign_in_with_oauth(self, credentials: dict[str, Any]) -> _FakeOAuthResponse:
        self.last_oauth_options = credentials.get("options")
        return _FakeOAuthResponse(url=self.next_oauth_url)

    def exchange_code_for_session(self, params: dict[str, Any]) -> _FakeAuthResponse:
        self.last_exchange_code = params.get("auth_code")
        if self.exchange_should_fail:
            raise RuntimeError("Fake Supabase: exchange_code_for_session forced failure")
        if self.next_callback_user is None:
            raise RuntimeError(
                "Fake Supabase: no callback user configured. Set "
                "fake_db.auth.next_callback_user before calling.",
            )
        return _FakeAuthResponse(user=self.next_callback_user)


class _FakeRPC:
    """Stand-in for ``client.rpc(name, params)``.

    Only ``get_user_permission_codes`` is implemented; it walks the
    in-memory ``user_roles`` ⋈ ``role_permissions`` ⋈ ``permissions``
    join, mirroring the production Postgres function.
    """

    def __init__(self, store: FakeSupabase, name: str, params: dict[str, Any]) -> None:
        self._store = store
        self._name = name
        self._params = params

    def execute(self) -> _FakeResult:
        if self._name != "get_user_permission_codes":
            raise NotImplementedError(
                f"FakeSupabase RPC '{self._name}' is not implemented",
            )

        user_id = self._params.get("p_user_id")
        if not isinstance(user_id, str):
            return _FakeResult([])

        user_roles = self._store.tables.get("user_roles", [])
        role_ids = {
            r.get("role_id")
            for r in user_roles
            if r.get("user_id") == user_id and isinstance(r.get("role_id"), str)
        }
        if not role_ids:
            return _FakeResult([])

        role_permissions = self._store.tables.get("role_permissions", [])
        permission_ids = {
            r.get("permission_id")
            for r in role_permissions
            if r.get("role_id") in role_ids and isinstance(r.get("permission_id"), str)
        }
        if not permission_ids:
            return _FakeResult([])

        permissions = self._store.tables.get("permissions", [])
        codes: list[dict[str, Any]] = []
        seen: set[str] = set()
        for p in permissions:
            if p.get("id") in permission_ids:
                code = p.get("code")
                if isinstance(code, str) and code and code not in seen:
                    codes.append({"code": code})
                    seen.add(code)

        return _FakeResult(codes)


class FakeSupabase:
    """In-memory Supabase stand-in.

    Repositories accept a ``supabase.Client``; ``FakeSupabase`` exposes
    ``.table(name)`` for repository chains and ``.auth`` for the two
    OAuth methods used by ``AuthService``. Tests get a clean, isolated
    store per fixture invocation.
    """

    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {}
        self.auth: _FakeSupabaseAuth = _FakeSupabaseAuth()
        # Records every `_listen_to_auth_events` call AuthService makes
        # to reset the client's auth state back to service_role after
        # a SIGNED_IN event (triggered by exchange_code_for_session).
        # Real supabase-py uses this same private hook to swap the
        # PostgREST Authorization header, so observing the call is a
        # faithful regression for the 42501 bug observed live.
        self.auth_events_received: list[tuple[str, Any]] = []

    def table(self, name: str) -> _FakeQuery:
        return _FakeQuery(self, name)

    def rpc(self, name: str, params: dict[str, Any]) -> _FakeRPC:
        """Stand-in for ``supabase.Client.rpc``."""
        return _FakeRPC(self, name, params)

    def _listen_to_auth_events(self, event: str, session: Any) -> None:
        """Record auth-state-change events emitted by AuthService."""
        self.auth_events_received.append((event, session))

    def seed(self, name: str, rows: list[dict[str, Any]]) -> None:
        """Insert pre-built rows directly into the in-memory table."""
        self.tables.setdefault(name, []).extend(deepcopy(rows))

    def all_rows(self, name: str) -> list[dict[str, Any]]:
        """Return a copy of all rows in a table (for assertions)."""
        return [deepcopy(r) for r in self.tables.get(name, [])]


def make_fake_supabase_user(
    *,
    user_id: str | None = None,
    email: str = "google-user@example.com",
    full_name: str = "Google User",
    avatar_url: str | None = "https://example.com/avatar.png",
    extra_metadata: dict[str, Any] | None = None,
) -> _FakeSupabaseUser:
    """Helper for building a Supabase user object as Google would return it."""
    metadata: dict[str, Any] = {
        "full_name": full_name,
        "name": full_name,
        "email": email,
    }
    if avatar_url is not None:
        metadata["avatar_url"] = avatar_url
        metadata["picture"] = avatar_url
    if extra_metadata:
        metadata.update(extra_metadata)
    return _FakeSupabaseUser(
        id=user_id or str(uuid4()),
        email=email,
        user_metadata=metadata,
    )
