-- =============================================================================
-- Mental Health Sovereign Agentic AI Platform
-- Application Database Schema — Milestone 2
-- =============================================================================
--
-- Scope:
-- - Application DB only: Supabase/PostgreSQL
-- - Does NOT include Qdrant vector collections
-- - Does NOT include DSM-5/treatment knowledge ingestion
-- - Does NOT include Langfuse trace storage
--
-- Core tables:
-- 1. users
-- 2. doctor_assignments
-- 3. consent_records
-- 4. chat_sessions
-- 5. chat_messages
-- 6. clinical_profiles
-- 7. stress_risk_scores
-- 8. audit_logs
--
-- Authorization model for MVP:
-- - Backend FastAPI enforces JWT, role, and doctor-patient assignment checks.
-- - Production-grade RLS policies are deferred to later hardening.
--
-- =============================================================================


-- =============================================================================
-- 0. Extensions
-- =============================================================================

-- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Case-insensitive email type.
-- This avoids separate accounts for User@Email.com and user@email.com.
CREATE EXTENSION IF NOT EXISTS citext;


-- =============================================================================
-- 1. Utility function: updated_at trigger
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- 2. users
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Supabase Auth mapping
    auth_user_id UUID,

    email CITEXT UNIQUE NOT NULL,
    password_hash VARCHAR(255),

    full_name VARCHAR(255) NOT NULL,

    role VARCHAR(20) NOT NULL
        CHECK (role IN ('patient', 'doctor', 'admin')),

    auth_provider VARCHAR(50) NOT NULL DEFAULT 'local'
        CHECK (auth_provider IN ('local', 'google')),

    provider_user_id VARCHAR(255),
    avatar_url TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT users_google_provider_requires_provider_user_id
        CHECK (
            auth_provider != 'google'
            OR provider_user_id IS NOT NULL
        )
);

DROP TRIGGER IF EXISTS trg_users_set_updated_at ON users;

CREATE TRIGGER trg_users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_users_role
ON users(role);

CREATE INDEX IF NOT EXISTS idx_users_is_active
ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_users_auth_provider
ON users(auth_provider);

CREATE UNIQUE INDEX IF NOT EXISTS unique_users_provider_identity
ON users(auth_provider, provider_user_id)
WHERE provider_user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS unique_users_auth_user_id
ON users(auth_user_id)
WHERE auth_user_id IS NOT NULL;

COMMENT ON TABLE users IS
'Application-level users table. Source of truth for role, auth provider, Supabase Auth mapping, active status, consent, assignments, and app JWT subject.';

COMMENT ON COLUMN users.password_hash IS
'Bcrypt password hash for local users. Nullable for Google OAuth users. Never expose through API responses.';


-- =============================================================================
-- 3. doctor_assignments
-- =============================================================================

CREATE TABLE IF NOT EXISTS doctor_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    doctor_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    assigned_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT doctor_assignments_no_self_assignment
        CHECK (doctor_id <> patient_id)
);

CREATE INDEX IF NOT EXISTS idx_doctor_assignments_doctor
ON doctor_assignments(doctor_id)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_doctor_assignments_patient
ON doctor_assignments(patient_id)
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_doctor_assignments_assigned_by
ON doctor_assignments(assigned_by);

CREATE INDEX IF NOT EXISTS idx_doctor_assignments_created_at
ON doctor_assignments(created_at);

CREATE UNIQUE INDEX IF NOT EXISTS unique_active_doctor_patient_assignment
ON doctor_assignments(doctor_id, patient_id)
WHERE is_active = TRUE;


COMMENT ON TABLE doctor_assignments IS
'Access-control relationship table. Doctors can access patient clinical data only when an active assignment exists.';


-- =============================================================================
-- 4. consent_records
-- =============================================================================

CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    policy_version VARCHAR(20) NOT NULL,
    accepted BOOLEAN NOT NULL DEFAULT TRUE,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT consent_records_policy_version_not_empty
        CHECK (char_length(trim(policy_version)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS unique_user_policy_version_consent
ON consent_records(user_id, policy_version);

CREATE INDEX IF NOT EXISTS idx_consent_records_user
ON consent_records(user_id);

CREATE INDEX IF NOT EXISTS idx_consent_records_user_accepted_at
ON consent_records(user_id, accepted_at DESC);

CREATE INDEX IF NOT EXISTS idx_consent_records_policy_version
ON consent_records(policy_version);


COMMENT ON TABLE consent_records IS
'Versioned consent acceptance records. Users must accept the current consent policy version before using protected workflows.';


-- =============================================================================
-- 5. chat_sessions
-- =============================================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'closed', 'timeout')),

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    CONSTRAINT chat_sessions_ended_at_after_started_at
        CHECK (
            ended_at IS NULL
            OR ended_at >= started_at
        ),

    CONSTRAINT chat_sessions_metadata_is_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
ON chat_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_status
ON chat_sessions(status);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_started_at
ON chat_sessions(user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_started_at
ON chat_sessions(started_at DESC);


COMMENT ON TABLE chat_sessions IS
'Patient-facing chat session metadata. Session messages are stored in chat_messages.';


-- =============================================================================
-- 6. chat_messages
-- =============================================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL
        CHECK (role IN ('user', 'assistant', 'system')),

    content TEXT NOT NULL,

    safety_flag BOOLEAN NOT NULL DEFAULT FALSE,

    safety_severity VARCHAR(20) NOT NULL DEFAULT 'none'
        CHECK (safety_severity IN ('none', 'low', 'medium', 'high', 'critical')),

    trace_id VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chat_messages_content_not_empty
        CHECK (char_length(trim(content)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session
ON chat_messages(session_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created_at
ON chat_messages(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_chat_messages_safety_flag
ON chat_messages(safety_flag)
WHERE safety_flag = TRUE;

CREATE INDEX IF NOT EXISTS idx_chat_messages_safety_severity
ON chat_messages(safety_severity);

CREATE INDEX IF NOT EXISTS idx_chat_messages_trace_id
ON chat_messages(trace_id)
WHERE trace_id IS NOT NULL;


COMMENT ON TABLE chat_messages IS
'Raw patient-facing chat messages. Sensitive data. Access must be controlled by backend role and assignment checks.';


-- =============================================================================
-- 7. clinical_profiles
-- =============================================================================

CREATE TABLE IF NOT EXISTS clinical_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    summary TEXT NOT NULL,

    symptoms JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_markers JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_snippets JSONB NOT NULL DEFAULT '[]'::jsonb,

    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT clinical_profiles_summary_not_empty
        CHECK (char_length(trim(summary)) > 0),

    CONSTRAINT clinical_profiles_symptoms_is_array
        CHECK (jsonb_typeof(symptoms) = 'array'),

    CONSTRAINT clinical_profiles_risk_markers_is_array
        CHECK (jsonb_typeof(risk_markers) = 'array'),

    CONSTRAINT clinical_profiles_evidence_snippets_is_array
        CHECK (jsonb_typeof(evidence_snippets) = 'array')
);

CREATE UNIQUE INDEX IF NOT EXISTS unique_clinical_profile_per_session
ON clinical_profiles(session_id);

CREATE INDEX IF NOT EXISTS idx_clinical_profiles_patient
ON clinical_profiles(patient_id);

CREATE INDEX IF NOT EXISTS idx_clinical_profiles_patient_generated_at
ON clinical_profiles(patient_id, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_clinical_profiles_generated_at
ON clinical_profiles(generated_at DESC);


COMMENT ON TABLE clinical_profiles IS
'Doctor-facing AI-generated clinical profile created after session closure. Must never be exposed through patient-facing APIs.';

COMMENT ON COLUMN clinical_profiles.evidence_snippets IS
'Short supporting snippets for doctor review. Prefer snippets over exposing full raw chat by default.';


-- =============================================================================
-- 8. stress_risk_scores
-- =============================================================================

CREATE TABLE IF NOT EXISTS stress_risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    score INTEGER NOT NULL
        CHECK (score >= 0 AND score <= 100),

    severity VARCHAR(20) NOT NULL
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),

    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT stress_risk_scores_evidence_is_object
        CHECK (jsonb_typeof(evidence) = 'object')
);

CREATE UNIQUE INDEX IF NOT EXISTS unique_stress_risk_score_per_session
ON stress_risk_scores(session_id);

CREATE INDEX IF NOT EXISTS idx_stress_risk_scores_patient
ON stress_risk_scores(patient_id);

CREATE INDEX IF NOT EXISTS idx_stress_risk_scores_patient_calculated_at
ON stress_risk_scores(patient_id, calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_stress_risk_scores_severity
ON stress_risk_scores(severity);

CREATE INDEX IF NOT EXISTS idx_stress_risk_scores_score
ON stress_risk_scores(score);


COMMENT ON TABLE stress_risk_scores IS
'Session-level stress/risk scoring for doctor dashboard and patient-safe trend display.';


-- =============================================================================
-- 9. audit_logs
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    role VARCHAR(20)
        CHECK (
            role IS NULL
            OR role IN ('patient', 'doctor', 'admin', 'system')
        ),

    action VARCHAR(100) NOT NULL,

    resource_type VARCHAR(100),
    resource_id VARCHAR(255),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    ip_address VARCHAR(45),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT audit_logs_action_not_empty
        CHECK (char_length(trim(action)) > 0),

    CONSTRAINT audit_logs_metadata_is_object
        CHECK (jsonb_typeof(metadata) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user
ON audit_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action
ON audit_logs(action);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource
ON audit_logs(resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
ON audit_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created_at
ON audit_logs(user_id, created_at DESC);


COMMENT ON TABLE audit_logs IS
'Application audit trail for sensitive actions, auth events, consent, assignments, clinical access, and system events.';

GRANT USAGE ON SCHEMA public TO service_role;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO service_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO service_role;


-- =============================================================================
-- 9.5. RBAC tables (User ↔ Role ↔ Permission)
-- =============================================================================
--
-- These tables introduce a full role/permission model alongside the
-- legacy ``users.role`` VARCHAR column. ``users.role`` is intentionally
-- kept during the transition so that service-layer ownership and
-- assignment checks (and the JWT ``role`` claim) continue to work. A
-- future migration will drop the column once resource-level policies
-- no longer depend on it.
--
-- Companion files:
--   * ``supabase/migrations/202605110002_rbac_core.sql``
--   * ``supabase/seeds/202605110003_rbac_seed.sql``
--   * ``supabase/migrations/202605110004_rbac_backfill_user_roles.sql``
--

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


CREATE OR REPLACE FUNCTION get_user_permission_codes(p_user_id UUID)
RETURNS TABLE(code VARCHAR) AS $$
    SELECT DISTINCT p.code
    FROM permissions p
    JOIN role_permissions rp ON rp.permission_id = p.id
    JOIN user_roles ur ON ur.role_id = rp.role_id
    WHERE ur.user_id = p_user_id;
$$ LANGUAGE sql STABLE;


GRANT SELECT, INSERT, UPDATE, DELETE
ON roles, permissions, user_roles, role_permissions
TO service_role;

GRANT EXECUTE ON FUNCTION get_user_permission_codes(UUID) TO service_role;


-- Phase 6 PR A — resolve role names from user_roles for the service layer.
CREATE OR REPLACE FUNCTION get_user_role_names(p_user_id UUID)
RETURNS TABLE(name VARCHAR) AS $$
    SELECT r.name
    FROM roles r
    JOIN user_roles ur ON ur.role_id = r.id
    WHERE ur.user_id = p_user_id;
$$ LANGUAGE sql STABLE;

GRANT EXECUTE ON FUNCTION get_user_role_names(UUID) TO service_role;


-- =============================================================================
-- 10. Optional sanity-check comments
-- =============================================================================
--
-- Expected backend authorization rules:
--
-- 1. Patient:
--    - Can access own chat_sessions and chat_messages.
--    - Cannot access clinical_profiles.
--
-- 2. Doctor:
--    - Can access patient-facing derived clinical data only for assigned patients.
--    - Assignment check:
--      EXISTS active doctor_assignments where
--      doctor_id = current_user.id AND patient_id = requested_patient_id.
--
-- 3. Admin:
--    - Can manage users and doctor_assignments.
--    - Does not automatically get raw chat access unless policy/API explicitly allows it.
--
-- 4. Audit:
--    - Login, registration, consent acceptance, assignment creation/deactivation,
--      doctor profile access, crisis workflow activation, and clinical profile generation
--      should be recorded in audit_logs.
--
-- =============================================================================
