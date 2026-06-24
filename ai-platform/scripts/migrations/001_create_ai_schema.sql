
-- ============================================================
-- AI Platform - Enrichment & Article Services Schema
-- PRD v2.0 Compliance
-- ============================================================

-- Create ai schema if not exists
CREATE SCHEMA IF NOT EXISTS ai;

-- ============================================================
-- Enrichment Service Tables
-- ============================================================

-- enrichment_runs: Track enrichment pipeline execution per video
CREATE TABLE IF NOT EXISTS ai.enrichment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID,
    video_id UUID NOT NULL,
    transcript_id UUID,
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC(10,6),
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ai.enrichment_runs IS 'Track enrichment pipeline execution per video with LLM usage and costs';

-- prompt_versions: Versioned prompts for LLM extractors
CREATE TABLE IF NOT EXISTS ai.prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    few_shot_examples JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    notes TEXT,
    CONSTRAINT uq_prompt_name_version UNIQUE(prompt_name, version)
);

COMMENT ON TABLE ai.prompt_versions IS 'Versioned prompts for LLM extractors with A/B testing support';

-- ============================================================
-- Article Service Tables
-- ============================================================

-- article_drafts: Main table for generated article drafts
CREATE TABLE IF NOT EXISTS ai.article_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_type VARCHAR(50) NOT NULL 
        CHECK (article_type IN ('narrative', 'knowledge', 'news', 'creative')),
    title TEXT NOT NULL,
    slug VARCHAR(500) UNIQUE,
    content_markdown TEXT NOT NULL,
    seo_metadata JSONB NOT NULL DEFAULT '{}',
    source_story_ids UUID[] NOT NULL DEFAULT '{}',
    source_video_ids UUID[] NOT NULL DEFAULT '{}',
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    quality_score NUMERIC(5,2),
    quality_issues JSONB DEFAULT '[]',
    review_status VARCHAR(50) NOT NULL DEFAULT 'pending_review'
        CHECK (review_status IN ('pending_review', 'approved', 'rejected', 'needs_revision')),
    reviewer_id UUID,
    review_notes TEXT,
    published_content_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    version BIGINT NOT NULL DEFAULT 1
);

COMMENT ON TABLE ai.article_drafts IS 'Main table for generated article drafts pending curator review';

-- article_draft_versions: Version history for article drafts
CREATE TABLE IF NOT EXISTS ai.article_draft_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_draft_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    content_markdown TEXT NOT NULL,
    seo_metadata JSONB,
    quality_score NUMERIC(5,2),
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    CONSTRAINT fk_draft_version
        FOREIGN KEY(article_draft_id) REFERENCES ai.article_drafts(id)
);

COMMENT ON TABLE ai.article_draft_versions IS 'Version history for article drafts with change tracking';

-- cost_tracking: Track total costs per video across all pipeline stages
CREATE TABLE IF NOT EXISTS ai.cost_tracking (
    video_id UUID PRIMARY KEY,
    extraction_cost_usd NUMERIC(10,6) DEFAULT 0,
    enrichment_cost_usd NUMERIC(10,6) DEFAULT 0,
    embedding_cost_usd NUMERIC(10,6) DEFAULT 0,
    article_cost_usd NUMERIC(10,6) DEFAULT 0,
    total_cost_usd NUMERIC(10,6) DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ai.cost_tracking IS 'Track total third-party API costs per video across all pipeline stages';

-- ============================================================
-- Indexes for Performance
-- ============================================================

-- enrichment_runs indexes
CREATE INDEX IF NOT EXISTS idx_enrichment_runs_video_id ON ai.enrichment_runs(video_id);
CREATE INDEX IF NOT EXISTS idx_enrichment_runs_status ON ai.enrichment_runs(status);
CREATE INDEX IF NOT EXISTS idx_enrichment_runs_created_at ON ai.enrichment_runs(created_at);

-- prompt_versions indexes
CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON ai.prompt_versions(prompt_name);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON ai.prompt_versions(is_active) WHERE is_active = true;

-- article_drafts indexes
CREATE INDEX IF NOT EXISTS idx_article_drafts_review_status ON ai.article_drafts(review_status);
CREATE INDEX IF NOT EXISTS idx_article_drafts_article_type ON ai.article_drafts(article_type);
CREATE INDEX IF NOT EXISTS idx_article_drafts_quality_score ON ai.article_drafts(quality_score);
CREATE INDEX IF NOT EXISTS idx_article_drafts_created_at ON ai.article_drafts(created_at);

-- article_draft_versions indexes
CREATE INDEX IF NOT EXISTS idx_article_draft_versions_draft_id ON ai.article_draft_versions(article_draft_id);
