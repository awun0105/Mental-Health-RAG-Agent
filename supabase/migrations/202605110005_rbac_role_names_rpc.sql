-- ============================================================================
-- Phase 6 (PR A) — get_user_role_names RPC
-- ----------------------------------------------------------------------------
-- Resolves a user's role NAMES (not just permission codes) by joining
-- ``user_roles`` against ``roles``. Phase 1 only added the permission-code
-- RPC; this Phase-6 step also exposes the role names so service-layer
-- resource checks (session ownership, doctor-patient assignment) can stop
-- reading ``users.role`` / ``CurrentUserClaims.role`` and instead resolve
-- the actor's roles from the canonical ``user_roles`` junction.
--
-- The function is ``STABLE`` (no writes), parameterless besides the user id,
-- and intentionally returns each role at most once via the FK uniqueness on
-- ``user_roles(user_id, role_id)``.
--
-- Apply order: 202605110002_rbac_core.sql
-- -> ../seeds/202605110003_rbac_seed.sql
-- -> 202605110004_rbac_backfill_user_roles.sql
-- -> 202605110005_rbac_role_names_rpc.sql.
-- ============================================================================

CREATE OR REPLACE FUNCTION get_user_role_names(p_user_id UUID)
RETURNS TABLE(name VARCHAR) AS $$
    SELECT r.name
    FROM roles r
    JOIN user_roles ur ON ur.role_id = r.id
    WHERE ur.user_id = p_user_id;
$$ LANGUAGE sql STABLE;

GRANT EXECUTE ON FUNCTION get_user_role_names(UUID) TO service_role;
