-- =============================================================================
-- Mental Health Sovereign Agentic AI Platform
-- RBAC Data Migration — backfill user_roles from legacy users.role
-- =============================================================================
--
-- One-shot data migration: every existing user gets a row in
-- ``user_roles`` mirroring their legacy ``users.role`` value. Idempotent
-- via ``ON CONFLICT DO NOTHING``.
--
-- ``users.role`` is intentionally kept during the transition so that
-- service-layer ownership/assignment checks and the JWT ``role`` claim
-- continue to work. A future Phase 6 migration will drop the column.
--
-- Apply order:
--   1. ``schema.sql``
--   2. ``rbac_migration.sql``
--   3. ``rbac_seed.sql``
--   4. ``rbac_data_migration.sql`` (this file)
--
-- =============================================================================

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name = u.role
ON CONFLICT (user_id, role_id) DO NOTHING;
