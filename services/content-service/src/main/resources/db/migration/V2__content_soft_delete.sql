-- Content Service Soft Delete Fields
-- Living Atlas of Indonesian Mystery Culture
-- Add soft delete fields to content tables to align with ddl.md specification

-- Add soft delete fields to content.stories
ALTER TABLE content.stories 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by UUID,
ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- Add soft delete fields to content.story_versions
ALTER TABLE content.story_versions 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by UUID,
ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- Add soft delete fields to content.story_evidence
ALTER TABLE content.story_evidence 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by UUID,
ADD COLUMN IF NOT EXISTS version BIGINT NOT NULL DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
