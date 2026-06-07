-- =============================================================================
-- Supabase Free-Tier Keepalive RPC
-- =============================================================================
--
-- Purpose:
-- - Allow GitHub Actions to create a tiny amount of Supabase activity without
--   depending on a locally running FastAPI backend.
-- - Use the public anon key with a narrow RPC instead of storing service_role
--   credentials in GitHub Actions.
--
-- Apply after the core schema and RBAC migrations.
-- =============================================================================

CREATE TABLE IF NOT EXISTS keepalive_pings (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'github-actions',
    pinged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT keepalive_pings_source_not_empty
        CHECK (char_length(trim(source)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_keepalive_pings_pinged_at
ON keepalive_pings(pinged_at DESC);

ALTER TABLE keepalive_pings ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE keepalive_pings FROM anon;
REVOKE ALL ON TABLE keepalive_pings FROM authenticated;

COMMENT ON TABLE keepalive_pings IS
'Low-risk activity table used by scheduled keepalive automation for local-development Supabase projects.';

CREATE OR REPLACE FUNCTION public.keepalive_ping(p_source TEXT DEFAULT 'github-actions')
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    inserted_id BIGINT;
    normalized_source TEXT;
BEGIN
    normalized_source := COALESCE(NULLIF(trim(p_source), ''), 'github-actions');

    INSERT INTO keepalive_pings(source)
    VALUES (normalized_source)
    RETURNING id INTO inserted_id;

    RETURN jsonb_build_object(
        'ok', true,
        'id', inserted_id,
        'source', normalized_source,
        'pinged_at', NOW()
    );
END;
$$;

REVOKE ALL ON FUNCTION public.keepalive_ping(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.keepalive_ping(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION public.keepalive_ping(TEXT) TO authenticated;
