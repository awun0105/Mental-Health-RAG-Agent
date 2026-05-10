-- =============================================================================
-- Mental Health Sovereign Agentic AI Platform
-- RBAC Seed — system roles, permissions, and role→permission mappings
-- =============================================================================
--
-- Seeds the three system roles (``admin``, ``doctor``, ``patient``), a
-- focused set of application permissions, and the role→permission
-- mappings required for Milestone 2.
--
-- Resource-level checks (ownership, doctor↔patient assignment) remain
-- in the service layer; permission codes here only express "is this
-- caller allowed to attempt the operation at all?".
--
-- Idempotent: re-running this file is safe.
--
-- Apply after ``supabase/migrations/202605110002_rbac_core.sql``.
--
-- =============================================================================


-- =============================================================================
-- 1. System roles
-- =============================================================================

INSERT INTO roles (name, display_name, description, is_system) VALUES
    ('admin',   'Administrator', 'Platform administrator with full management access.', TRUE),
    ('doctor',  'Doctor',        'Licensed clinician with access to assigned patients.', TRUE),
    ('patient', 'Patient',       'End user receiving mental-health support.',            TRUE)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description  = EXCLUDED.description,
    is_system    = EXCLUDED.is_system;


-- =============================================================================
-- 2. Permissions
-- =============================================================================

INSERT INTO permissions (code, module, action, description) VALUES
    -- auth
    ('auth:me',                  'auth',       'me',          'Read own authenticated user claims'),

    -- users
    ('user:create',              'user',       'create',      'Create application users'),
    ('user:read',                'user',       'read',        'Read application users'),
    ('user:update',              'user',       'update',      'Update application users'),
    ('user:delete',              'user',       'delete',      'Deactivate or delete application users'),

    -- roles
    ('role:read',                'role',       'read',        'List roles'),
    ('role:assign',              'role',       'assign',      'Assign or remove roles on users'),

    -- permissions
    ('permission:read',          'permission', 'read',        'List permissions'),
    ('permission:assign',        'permission', 'assign',      'Grant or revoke permissions on roles'),

    -- doctor-patient assignments
    ('assignment:create',        'assignment', 'create',      'Create a doctor-patient assignment'),
    ('assignment:read',          'assignment', 'read',        'Read doctor-patient assignments'),
    ('assignment:deactivate',    'assignment', 'deactivate',  'Deactivate a doctor-patient assignment'),

    -- chat sessions
    ('session:create',           'session',    'create',      'Start a chat session'),
    ('session:read',             'session',    'read',        'Read chat sessions (resource-scoped in service layer)'),
    ('session:close',            'session',    'close',       'Close a chat session'),

    -- patient data
    ('patient:read',             'patient',    'read',        'Read patient data (resource-scoped in service layer)'),

    -- consent
    ('consent:accept',           'consent',    'accept',      'Accept a consent policy version'),
    ('consent:read_status',      'consent',    'read_status', 'Read own consent acceptance status')
ON CONFLICT (code) DO UPDATE SET
    module      = EXCLUDED.module,
    action      = EXCLUDED.action,
    description = EXCLUDED.description;


-- =============================================================================
-- 3. Role → Permission mappings
-- =============================================================================

-- admin: all seeded permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- doctor: auth:me, assignment:read, session:read, patient:read, consent:read_status
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p
    ON p.code IN (
        'auth:me',
        'assignment:read',
        'session:read',
        'patient:read',
        'consent:read_status'
    )
WHERE r.name = 'doctor'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- patient: auth:me, session:create, session:read, session:close,
--          consent:accept, consent:read_status
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p
    ON p.code IN (
        'auth:me',
        'session:create',
        'session:read',
        'session:close',
        'consent:accept',
        'consent:read_status'
    )
WHERE r.name = 'patient'
ON CONFLICT (role_id, permission_id) DO NOTHING;
