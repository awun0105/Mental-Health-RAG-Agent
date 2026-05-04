"""In-memory stand-in for the supabase Client used in repository unit tests.

This intentionally implements only the chain API actually used by the
repositories in this codebase, namely:

    client.table(name).select(...).eq(...).order(...).limit(...).execute()
    client.table(name).insert(data).execute()
    client.table(name).update(data).eq(...).execute()
    client.table(name).delete().eq(...).execute()

It is **not** a full reimplementation of supabase-py. If a repository
starts using a method that this fake does not support, the call will
raise ``NotImplementedError`` so the gap is visible immediately.
"""

from __future__ import annotations

from copy import deepcopy
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


class FakeSupabase:
    """In-memory Supabase stand-in.

    Repositories accept a ``supabase.Client``; ``FakeSupabase`` only needs
    to expose ``.table(name)``, so it can be passed in at construction
    time. Tests get a clean, isolated store per fixture invocation.
    """

    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {}

    def table(self, name: str) -> _FakeQuery:
        return _FakeQuery(self, name)

    def seed(self, name: str, rows: list[dict[str, Any]]) -> None:
        """Insert pre-built rows directly into the in-memory table."""
        self.tables.setdefault(name, []).extend(deepcopy(rows))

    def all_rows(self, name: str) -> list[dict[str, Any]]:
        """Return a copy of all rows in a table (for assertions)."""
        return [deepcopy(r) for r in self.tables.get(name, [])]
