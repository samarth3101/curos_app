-- ============================================================
-- PostgreSQL Initialization Script
-- ============================================================
-- This runs on first container start (docker-entrypoint-initdb.d).
-- Creates required extensions and initial schema placeholders.
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable case-insensitive text
CREATE EXTENSION IF NOT EXISTS "citext";

-- Enable trigram indexing (for search)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Cortex OI database initialized at %', NOW();
END $$;
