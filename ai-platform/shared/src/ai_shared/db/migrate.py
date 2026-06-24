"""Database migration script — creates all schemas, enums, and tables.

Updated for PRD v2.0:
- Removed: source.assets, source.speakers, source.video_formats, source.video_comments
- Removed: source.extraction_jobs, ai.extraction_results, ai.embeddings (pgvector)
- Removed: content.*, culture.*, research.*, analytics.*, system.* schemas
- Added: source.channel_configs, source.playlist_videos
- Added: ai.extraction_runs, ai.enrichment_runs, ai.prompt_versions
- Added: ai.embedding_runs, ai.article_drafts, ai.article_draft_versions
- Added: ai.pipeline_runs, ai.pipeline_failed_jobs, ai.cost_tracking
- Simplified: source.transcripts, source.transcript_segments (no speaker)
- Simplified: knowledge.claims, knowledge.assertions (no complex entity tables)

Run: python -m ai_shared.db.migrate
"""

import asyncio
import structlog
from ai_shared.config import ServiceConfig
from ai_shared.database import Database

logger = structlog.get_logger(__name__)

DDL = """
-- ============================================================
-- AI Platform v2.0 — Full DDL Migration
-- ============================================================

-- 6.1 Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 6.2 Schemas
CREATE SCHEMA IF NOT EXISTS source;
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS governance;

-- 6.3 Enums
CREATE TYPE IF NOT EXISTS source.platform_type AS ENUM ('youtube', 'manual');

CREATE TYPE IF NOT EXISTS source.job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');

CREATE TYPE IF NOT EXISTS knowledge.evidence_level AS ENUM ('direct', 'derived', 'inferred', 'generated');

-- ============================================================
-- 6.4 Source Schema Tables (Ingestion + Extraction)
-- ============================================================

-- source.channels
CREATE TABLE IF NOT EXISTS source.channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform source.platform_type NOT NULL,
    platform_channel_id VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    language_code VARCHAR(20),
    channel_url TEXT,
    avatar_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_channels_platform_channel UNIQUE(platform, platform_channel_id)
);

-- source.channel_configs (per-channel configuration)
CREATE TABLE IF NOT EXISTS source.channel_configs (
    channel_id UUID PRIMARY KEY,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    min_duration_seconds INTEGER DEFAULT 120,
    max_videos_per_crawl INTEGER DEFAULT 50,
    crawl_frequency VARCHAR(50) DEFAULT 'weekly',
    language_filter VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_channel_config_channel
        FOREIGN KEY(channel_id) REFERENCES source.channels(id)
);

-- source.channel_snapshots
CREATE TABLE IF NOT EXISTS source.channel_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL,
    subscriber_count BIGINT,
    video_count BIGINT,
    view_count BIGINT,
    metadata JSONB DEFAULT '{}',
    snapshot_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- source.playlists
CREATE TABLE IF NOT EXISTS source.playlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL,
    platform_playlist_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    playlist_url TEXT,
    video_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_playlist_platform UNIQUE(platform_playlist_id)
);

-- source.playlist_videos (junction table, replaces playlist_id in videos)
CREATE TABLE IF NOT EXISTS source.playlist_videos (
    playlist_id UUID NOT NULL,
    video_id UUID NOT NULL,
    position INTEGER,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY(playlist_id, video_id)
);

-- source.videos (central video registry)
CREATE TABLE IF NOT EXISTS source.videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL,
    platform_video_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    language_code VARCHAR(20),
    published_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    view_count BIGINT,
    like_count BIGINT,
    comment_count BIGINT,
    video_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_platform_video UNIQUE(platform_video_id)
);

-- source.video_payload_versions (immutable raw YT-DLP output)
CREATE TABLE IF NOT EXISTS source.video_payload_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    payload_hash TEXT NOT NULL,
    payload JSONB NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- source.video_chapters
CREATE TABLE IF NOT EXISTS source.video_chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    start_seconds NUMERIC(12,3),
    end_seconds NUMERIC(12,3),
    title TEXT NOT NULL
);

-- source.video_tags
CREATE TABLE IF NOT EXISTS source.video_tags (
    video_id UUID NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY(video_id, tag)
);

-- source.video_thumbnails
CREATE TABLE IF NOT EXISTS source.video_thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    thumbnail_url TEXT,
    width INTEGER,
    height INTEGER,
    preference INTEGER
);

-- source.subtitle_tracks (TEXT content — NOT files)
CREATE TABLE IF NOT EXISTS source.subtitle_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    language_code VARCHAR(20),
    is_auto_generated BOOLEAN,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- source.transcripts (versioned, immutable — NO speaker info)
CREATE TABLE IF NOT EXISTS source.transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('youtube_subtitle', 'google_stt', 'assemblyai', 'deepgram')),
    language_code VARCHAR(20),
    version_number INTEGER NOT NULL,
    word_count INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- source.transcript_segments (NO speaker column)
CREATE TABLE IF NOT EXISTS source.transcript_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID NOT NULL,
    start_seconds NUMERIC(12,3),
    end_seconds NUMERIC(12,3),
    content TEXT NOT NULL,
    confidence NUMERIC(5,3),
    embedding_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}'
);

-- source.ingestion_jobs
CREATE TABLE IF NOT EXISTS source.ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(100),
    target_id UUID,
    status source.job_status NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- ============================================================
-- 6.5 Knowledge Schema Tables (Enrichment)
-- ============================================================

-- knowledge.claims
CREATE TABLE IF NOT EXISTS knowledge.claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(100),
    confidence_score NUMERIC(5,2),
    extraction_method VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'unverified',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- knowledge.claim_sources
CREATE TABLE IF NOT EXISTS knowledge.claim_sources (
    claim_id UUID NOT NULL,
    transcript_segment_id UUID NOT NULL,
    evidence_level knowledge.evidence_level NOT NULL,
    confidence_score NUMERIC(5,2),
    PRIMARY KEY(claim_id, transcript_segment_id)
);

-- knowledge.assertions (subject-predicate-object triples)
CREATE TABLE IF NOT EXISTS knowledge.assertions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_entity_name TEXT NOT NULL,
    predicate VARCHAR(100) NOT NULL,
    object_entity_name TEXT,
    object_value TEXT,
    confidence_score NUMERIC(5,2),
    status VARCHAR(50) DEFAULT 'candidate',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- knowledge.contradictions
CREATE TABLE IF NOT EXISTS knowledge.contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_name TEXT NOT NULL,
    contradiction_type VARCHAR(100),
    description TEXT,
    severity VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 6.6 AI Schema Tables (Pipeline, Jobs, Costs, Prompts, Articles)
-- ============================================================

-- ai.extraction_runs (replaces old extraction_results)
CREATE TABLE IF NOT EXISTS ai.extraction_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID,
    video_id UUID NOT NULL,
    subtitle_track_id UUID,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('youtube_subtitle', 'google_stt', 'assemblyai', 'deepgram')),
    detected_language VARCHAR(20),
    processing_seconds INTEGER,
    word_count INTEGER,
    avg_confidence NUMERIC(5,3),
    low_confidence_segments INTEGER,
    cost_usd NUMERIC(10,6),
    status source.job_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ai.enrichment_runs
CREATE TABLE IF NOT EXISTS ai.enrichment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID,
    video_id UUID NOT NULL,
    transcript_id UUID NOT NULL,
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50),
    entity_count INTEGER DEFAULT 0,
    claim_count INTEGER DEFAULT 0,
    theme_count INTEGER DEFAULT 0,
    motif_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost_usd NUMERIC(10,6),
    status source.job_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ai.prompt_versions
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

-- ai.embedding_runs
CREATE TABLE IF NOT EXISTS ai.embedding_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID,
    document_type VARCHAR(100) NOT NULL,
    document_id UUID NOT NULL,
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER,
    cost_usd NUMERIC(10,6),
    weaviate_collection VARCHAR(100) NOT NULL,
    status source.job_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ai.article_drafts (staging table — waits for curator approval)
CREATE TABLE IF NOT EXISTS ai.article_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_type VARCHAR(50) NOT NULL CHECK (article_type IN ('narrative', 'knowledge', 'news', 'creative')),
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

-- ai.article_draft_versions
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

-- ai.pipeline_runs (orchestration state machine)
CREATE TABLE IF NOT EXISTS ai.pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(100) NOT NULL,
    pipeline_version VARCHAR(50),
    trigger_type VARCHAR(50) NOT NULL CHECK (trigger_type IN ('manual', 'scheduled', 'event')),
    trigger_reference UUID,
    priority VARCHAR(20) NOT NULL DEFAULT 'background',
    status source.job_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    total_cost_usd NUMERIC(10,6),
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ai.pipeline_failed_jobs (Dead Letter Queue)
CREATE TABLE IF NOT EXISTS ai.pipeline_failed_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID
);

-- ai.cost_tracking (per video)
CREATE TABLE IF NOT EXISTS ai.cost_tracking (
    video_id UUID PRIMARY KEY,
    extraction_cost_usd NUMERIC(10,6) DEFAULT 0,
    enrichment_cost_usd NUMERIC(10,6) DEFAULT 0,
    embedding_cost_usd NUMERIC(10,6) DEFAULT 0,
    article_cost_usd NUMERIC(10,6) DEFAULT 0,
    total_cost_usd NUMERIC(10,6) DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 6.7 Governance Schema Tables
-- ============================================================

-- governance.lineage (data provenance chain)
CREATE TABLE IF NOT EXISTS governance.lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def run_migration():
    """Execute all DDL statements."""
    config = ServiceConfig()
    db = Database(config)
    await db.connect()

    logger.info("migration_started")

    try:
        # Split DDL into individual statements and execute
        statements = [s.strip() for s in DDL.split(";") if s.strip()]
        total = len(statements)

        for i, stmt in enumerate(statements, 1):
            try:
                await db.execute(stmt + ";")
                if i % 10 == 0:
                    logger.info("migration_progress", completed=i, total=total)
            except Exception as e:
                # Log but continue — many are "IF NOT EXISTS" so duplicates are ok
                logger.warning("migration_statement_warning", index=i, error=str(e))

        logger.info("migration_completed", total_statements=total)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(run_migration())