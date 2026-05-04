"""Tests for AuditService.log_event role + metadata sanitization."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.constants import AuditAction, UserRole
from app.services.audit_service import AuditService

from tests.fakes.fake_supabase import FakeSupabase


async def test_log_event_persists_role_and_sanitizes_metadata(
    audit_service: AuditService,
    fake_db: FakeSupabase,
) -> None:
    """`role` ends up in the audit_logs row and non-JSON-safe values get stringified."""
    not_json_safe = datetime(2025, 1, 1, tzinfo=UTC)

    await audit_service.log_event(
        user_id="actor-1",
        role=UserRole.ADMIN.value,
        action=AuditAction.ADMIN_CONFIG_CHANGE,
        resource_type="settings",
        resource_id="sett-1",
        metadata={
            "string": "ok",
            "number": 42,
            "flag": True,
            "ts": not_json_safe,  # datetime is not JSON-safe -> sanitized to str
        },
        ip_address="10.0.0.1",
    )

    rows = fake_db.all_rows("audit_logs")
    assert len(rows) == 1
    row = rows[0]

    assert row["user_id"] == "actor-1"
    assert row["role"] == UserRole.ADMIN.value
    assert row["action"] == "admin_config_change"
    assert row["resource_type"] == "settings"
    assert row["resource_id"] == "sett-1"
    assert row["ip_address"] == "10.0.0.1"

    metadata = row["metadata"]
    assert metadata["string"] == "ok"
    assert metadata["number"] == 42
    assert metadata["flag"] is True
    assert isinstance(metadata["ts"], str)  # datetime stringified
