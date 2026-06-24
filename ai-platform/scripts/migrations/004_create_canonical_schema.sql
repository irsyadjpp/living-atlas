-- ============================================================
-- Database Schema for Canonical Story Storage
-- PRD v2.0 Compliance - Updated Architecture
-- Focus: Knowledge Extraction, NOT Media Archive
-- ============================================================

-- Create schema for canonical stories if not exists
CREATE SCHEMA IF NOT EXISTS canonical;

-- ============================================================
-- Canonical Story Storage
-- ============================================================

-- Main canonical story table
CREATE TABLE IF NOT EXISTS canonical.stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Story metadata
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    story_type VARCHAR(50) NOT NULL,
    primary_culture VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    time_period VARCHAR(100),
    confidence NUMERIC(5,2) NOT NULL,
    
    -- Source tracking
    source_video_id UUID NOT NULL,
    source_transcript_id UUID NOT NULL,
    extraction_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    extraction_model VARCHAR(100) NOT NULL DEFAULT 'gemini-1.5-flash',
    extraction_version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    
    -- Validation status
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    quality_score NUMERIC(5,2),
    validation_date TIMESTAMPTZ,
    ready_for_graph BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Full canonical JSON
    canonical_data JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT fk_story_video FOREIGN KEY (source_video_id) REFERENCES source.videos(id),
    CONSTRAINT fk_story_transcript FOREIGN KEY (source_transcript_id) REFERENCES source.transcripts(id)
);

COMMENT ON TABLE canonical.stories IS 'Canonical stories - SINGLE SOURCE OF TRUTH for all downstream processing';

-- Indexes for canonical.stories
CREATE INDEX IF NOT EXISTS idx_stories_video_id ON canonical.stories(source_video_id);
CREATE INDEX IF NOT EXISTS idx_stories_type ON canonical.stories(story_type);
CREATE INDEX IF NOT EXISTS idx_stories_culture ON canonical.stories(primary_culture);
CREATE INDEX IF NOT EXISTS idx_stories_region ON canonical.stories(region);
CREATE INDEX IF NOT EXISTS idx_stories_validated ON canonical.stories(is_validated) WHERE is_validated = TRUE;
CREATE INDEX IF NOT EXISTS idx_stories_quality ON canonical.stories(quality_score);
CREATE INDEX IF NOT EXISTS idx_stories_created_at ON canonical.stories(created_at);

-- ============================================================
-- Canonical Story Versions (for A/B testing and re-extraction)
-- ============================================================

CREATE TABLE IF NOT EXISTS canonical.story_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL,
    version VARCHAR(50) NOT NULL,
    
    -- Which model/prompt version was used
    extraction_model VARCHAR(100),
    prompt_version VARCHAR(50),
    
    -- Full canonical JSON for this version
    canonical_data JSONB NOT NULL,
    
    -- Validation results
    quality_score NUMERIC(5,2),
    validation_result JSONB,
    
    -- Change tracking
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_version_story FOREIGN KEY (story_id) REFERENCES canonical.stories(id),
    CONSTRAINT uq_story_version UNIQUE(story_id, version)
);

COMMENT ON TABLE canonical.story_versions IS 'Version history of canonical stories for A/B testing and re-extraction';

-- ============================================================
-- Entity Deduplication Table
-- ============================================================

CREATE TABLE IF NOT EXISTS canonical.canonical_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(50) NOT NULL,
    
    -- All known aliases
    aliases JSONB NOT NULL DEFAULT '[]',
    
    -- Aggregate information from all stories
    description TEXT,
    cultural_significance TEXT,
    first_seen_story_id UUID,
    story_count INTEGER NOT NULL DEFAULT 1,
    
    -- Normalization metadata
    is_canonical BOOLEAN NOT NULL DEFAULT TRUE,
    normalization_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE canonical.canonical_entities IS 'Deduplicated canonical entities with aliases tracking';

CREATE INDEX IF NOT EXISTS idx_canonical_entities_type ON canonical.canonical_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_canonical_entities_aliases ON canonical.canonical_entities USING GIN(aliases);

-- ============================================================
-- Story-Entity Junction Table
-- ============================================================

CREATE TABLE IF NOT EXISTS canonical.story_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL,
    canonical_entity_id UUID NOT NULL,
    
    -- Role in this specific story
    role_in_story TEXT,
    confidence NUMERIC(5,2),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_story_entity_story FOREIGN KEY (story_id) REFERENCES canonical.stories(id),
    CONSTRAINT fk_story_entity_entity FOREIGN KEY (canonical_entity_id) REFERENCES canonical.canonical_entities(id),
    CONSTRAINT uq_story_entity UNIQUE(story_id, canonical_entity_id)
);

COMMENT ON TABLE canonical.story_entities IS 'Junction table linking stories to canonical entities';

-- ============================================================
-- Knowledge Validation Results
-- ============================================================

CREATE TABLE IF NOT EXISTS canonical.validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL,
    story_version VARCHAR(50),
    
    quality_score NUMERIC(5,2),
    ready_for_graph BOOLEAN NOT NULL,
    recommendation VARCHAR(50),
    
    issues JSONB NOT NULL DEFAULT '[]',
    warnings JSONB NOT NULL DEFAULT '[]',
    
    validated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    CONSTRAINT fk_validation_story FOREIGN KEY (story_id) REFERENCES canonical.stories(id)
);

COMMENT ON TABLE canonical.validation_results IS 'Validation results for canonical stories';

-- ============================================================
-- Update existing pipeline_runs table to track canonical story extraction
-- ============================================================

-- Add canonical_story_id to enrichment_runs
ALTER TABLE ai.enrichment_runs 
ADD COLUMN IF NOT EXISTS canonical_story_id UUID;

-- Add index
CREATE INDEX IF NOT EXISTS idx_enrichment_canonical_story ON ai.enrichment_runs(canonical_story_id);

-- ============================================================
-- Update cost_tracking to include canonical extraction costs
-- ============================================================

ALTER TABLE ai.cost_tracking 
ADD COLUMN IF NOT EXISTS canonical_extraction_cost_usd NUMERIC(10,6) DEFAULT 0;

-- Update trigger to recalculate total cost
CREATE OR REPLACE FUNCTION update_total_cost()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total_cost_usd = 
        COALESCE(NEW.extraction_cost_usd, 0) +
        COALESCE(NEW.enrichment_cost_usd, 0) +
        COALESCE(NEW.embedding_cost_usd, 0) +
        COALESCE(NEW.article_cost_usd, 0) +
        COALESCE(NEW.canonical_extraction_cost_usd, 0);
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_update_total_cost
    BEFORE UPDATE ON ai.cost_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_total_cost();

-- ============================================================
-- Update article_drafts to reference canonical stories
-- ============================================================

ALTER TABLE ai.article_drafts 
ADD COLUMN IF NOT EXISTS source_canonical_story_id UUID;

-- Add index
CREATE INDEX IF NOT EXISTS idx_article_canonical_story ON ai.article_drafts(source_canonical_story_id);

-- ============================================================
-- Summary
-- ============================================================

COMMENT ON SCHEMA canonical IS 'Canonical Story Storage - SINGLE SOURCE OF TRUTH for Knowledge Extraction, Graph Construction, and Article Generation';

-- New tables:
--   canonical.stories - Main canonical story storage
--   canonical.story_versions - Version history for A/B testing
--   canonical.canonical_entities - Deduplicated entities
--   canonical.story_entities - Story-entity relationships
--   canonical.validation_results - Validation history

-- Updated tables:
--   ai.enrichment_runs - Added canonical_story_id
--   ai.cost_tracking - Added canonical_extraction_cost_usd
--   ai.article_drafts - Added source_canonical_story_id