"""Tests for ConsentService accept + status flow."""

from __future__ import annotations

import pytest
from app.core.config import settings
from app.core.constants import UserRole
from app.schemas.consent import ConsentAcceptRequest
from app.services.authorization_service import AuthorizationService
from app.services.consent_service import ConsentService

from tests.conftest import seed_rbac_tables
from tests.fakes.fake_supabase import FakeSupabase


@pytest.fixture(autouse=True)
def _reset_authz_cache() -> None:
    """Drop the role-name cache between tests; see test_session_service."""
    AuthorizationService.clear_cache()


async def test_accept_consent_creates_record_and_audit_with_role(
    consent_service_with_authz: ConsentService,
    fake_db: FakeSupabase,
) -> None:
    """Accepting writes a consent_records row AND an audit_logs row carrying role.

    Phase 6 PR A: the actor's role is resolved from ``user_roles`` via
    ``AuthorizationService.get_primary_role_name``. The seed below puts
    the user in the ``patient`` role so the audit row carries
    ``UserRole.PATIENT.value`` as before.
    """
    user_id = "user-123"
    policy_version = settings.current_consent_policy_version
    seed_rbac_tables(fake_db, user_role_pairs=[(user_id, UserRole.PATIENT.value)])

    consent = await consent_service_with_authz.accept_consent(
        user_id=user_id,
        payload=ConsentAcceptRequest(policy_version=policy_version),
        ip_address="127.0.0.1",
    )

    assert consent.user_id == user_id
    assert consent.policy_version == policy_version
    assert consent.accepted is True

    consent_rows = fake_db.all_rows("consent_records")
    assert len(consent_rows) == 1
    assert consent_rows[0]["user_id"] == user_id

    audit_rows = fake_db.all_rows("audit_logs")
    assert len(audit_rows) == 1
    assert audit_rows[0]["role"] == UserRole.PATIENT.value
    assert audit_rows[0]["action"] == "consent_accepted"
    assert audit_rows[0]["ip_address"] == "127.0.0.1"
    assert audit_rows[0]["resource_id"] == consent.id


async def test_get_status_reflects_acceptance(
    consent_service: ConsentService,
) -> None:
    """`get_status` flips `has_valid_consent` after an accept of the current version."""
    user_id = "user-456"
    current = settings.current_consent_policy_version

    before = await consent_service.get_status(user_id)
    assert before.has_valid_consent is False
    assert before.latest_accepted_policy_version is None
    assert before.current_policy_version == current

    await consent_service.accept_consent(
        user_id=user_id,
        payload=ConsentAcceptRequest(policy_version=current),
    )

    after = await consent_service.get_status(user_id)
    assert after.has_valid_consent is True
    assert after.latest_accepted_policy_version == current
