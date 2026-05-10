-- =============================================================================
-- Mental Health Sovereign Agentic AI Platform
-- RBAC Migration — User ↔ Role ↔ Permission tables
-- =============================================================================
--
-- Adds the four core RBAC tables and a helper RPC function used by the
-- application authorization service:
--
--   1. roles
--   2. permissions
--   3. user_roles      (junction)
--   4. role_permissions (junction)
--   + get_user_permission_codes(p_user_id UUID) RPC
--
-- This migration is additive. ``users.role`` is intentionally NOT dropped
-- here — see ``rbac_data_migration.sql`` for the user→role migration and
-- the future Phase 6 column-drop migration.
--
-- Apply order:
--   1. ``schema.sql``               (base tables + ``set_updated_at``)
--   2. ``rbac_migration.sql``       (this file)
--   3. ``rbac_seed.sql``            (system roles + permissions)
--   4. ``rbac_data_migration.sql``  (backfill ``user_roles`` from ``users.role``)
--
-- =============================================================================


-- =============================================================================
-- 1. roles
-- =============================================================================

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    is_system BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT roles_name_not_empty
        CHECK (char_length(trim(name)) > 0),
    CONSTRAINT roles_display_name_not_empty
        CHECK (char_length(trim(display_name)) > 0)
);

DROP TRIGGER IF EXISTS trg_roles_set_updated_at ON roles;

CREATE TRIGGER trg_roles_set_updated_at
BEFORE UPDATE ON roles
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_roles_is_system
ON roles(is_system);

COMMENT ON TABLE roles IS
'Application roles. System roles (admin, doctor, patient) are seeded with is_system=TRUE and must not be deleted.';


-- =============================================================================
-- 2. permissions
-- =============================================================================

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(100) NOT NULL UNIQUE,
    module VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT permissions_code_not_empty
        CHECK (char_length(trim(code)) > 0),
    CONSTRAINT permissions_module_not_empty
        CHECK (char_length(trim(module)) > 0),
    CONSTRAINT permissions_action_not_empty
        CHECK (char_length(trim(action)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_permissions_module
ON permissions(module);

COMMENT ON TABLE permissions IS
'Application permissions. Each row is a single (module, action) pair identified by a unique code such as "session:read".';


-- =============================================================================
-- 3. user_roles (junction)
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_user_roles_user_id
ON user_roles(user_id);

CREATE INDEX IF NOT EXISTS idx_user_roles_role_id
ON user_roles(role_id);

COMMENT ON TABLE user_roles IS
'Junction between users and roles. A user may hold multiple roles concurrently.';


-- =============================================================================
-- 4. role_permissions (junction)
-- =============================================================================

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,

    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_role_permissions_role_id
ON role_permissions(role_id);

CREATE INDEX IF NOT EXISTS idx_role_permissions_permission_id
ON role_permissions(permission_id);

COMMENT ON TABLE role_permissions IS
'Junction between roles and permissions. A role may grant any number of permissions.';


-- =============================================================================
-- 5. RPC: resolve effective permission codes for a user
-- =============================================================================
--
-- PostgREST does not perform arbitrary multi-table JOINs cleanly. The
-- application's ``PermissionRepository`` calls this function via
-- ``client.rpc("get_user_permission_codes", {"p_user_id": user_id})``
-- to resolve all permission codes a user inherits through their roles.

CREATE OR REPLACE FUNCTION get_user_permission_codes(p_user_id UUID)
RETURNS TABLE(code VARCHAR) AS $$
    SELECT DISTINCT p.code
    FROM permissions p
    JOIN role_permissions rp ON rp.permission_id = p.id
    JOIN user_roles ur ON ur.role_id = rp.role_id
    WHERE ur.user_id = p_user_id;
$$ LANGUAGE sql STABLE;

COMMENT ON FUNCTION get_user_permission_codes(UUID) IS
'Return the distinct permission codes inherited by a user through user_roles → role_permissions → permissions.';


-- =============================================================================
-- 6. Grants for service_role
-- =============================================================================
--
-- Mirror the existing pattern at the bottom of ``schema.sql``: the
-- backend connects with the Supabase service-role key and bypasses RLS.

GRANT SELECT, INSERT, UPDATE, DELETE
ON roles, permissions, user_roles, role_permissions
TO service_role;

GRANT EXECUTE ON FUNCTION get_user_permission_codes(UUID) TO service_role;
