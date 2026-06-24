-- Identity Service Extensions
-- Living Atlas of Indonesian Mystery Culture
-- Add missing PostgreSQL extensions for full-text search and analytics

CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
