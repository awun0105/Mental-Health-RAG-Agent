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
--   1. ``202605110001_initial_schema.sql``
--   2. ``202605110002_rbac_core.sql``
--   3. ``../seeds/202605110003_rbac_seed.sql``
--   4. ``202605110004_rbac_backfill_user_roles.sql`` (this file)
--
-- =============================================================================

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name = u.role
ON CONFLICT (user_id, role_id) DO NOTHING;
