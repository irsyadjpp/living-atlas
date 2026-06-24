-- Source Domain Schema
-- Living Atlas of Indonesian Mystery Culture
-- Complete source ingestion and evidence tracking

-- Create source schema
CREATE SCHEMA IF NOT EXISTS source;

-- ============================================================
-- ENUMS
-- ============================================================

DO $$
BEGIN
    CREATE TYPE source.platform_type AS ENUM (
        'youtube',
        'spotify',
        'apple_podcast',
        'rss',
        'book',
        'website',
        'manual'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE source.asset_type AS ENUM (
        'video',
        'audio',
        'thumbnail',
        'subtitle',
        'transcript',
        'image',
        'pdf'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE source.transcript_type AS ENUM (
        'human_subtitle',
        'auto_subtitle',
        'whisperx',
        'edited'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE source.job_status AS ENUM (
        'pending',
        'running',
        'completed',
        'failed',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- CHANNELS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform source.platform_type NOT NULL,
    platform_channel_id VARCHAR(255) NOT NULL,
    slug VARCHAR(255),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    country_code VARCHAR(10),
    language_code VARCHAR(20),
    channel_url TEXT,
    custom_url TEXT,
    avatar_url TEXT,
    banner_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    version BIGINT NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_channels_platform_channel UNIQUE(platform, platform_channel_id)
);

CREATE INDEX IF NOT EXISTS idx_channels_platform ON source.channels(platform);
CREATE INDEX IF NOT EXISTS idx_channels_name ON source.channels USING GIN(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_channels_metadata ON source.channels USING GIN(metadata);

-- ============================================================
-- CHANNEL SNAPSHOTS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.channel_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL,
    subscriber_count BIGINT,
    video_count BIGINT,
    view_count BIGINT,
    metadata JSONB DEFAULT '{}',
    snapshot_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_channel_snapshots_channel FOREIGN KEY(channel_id) REFERENCES source.channels(id)
) PARTITION BY RANGE(snapshot_at);

-- ============================================================
-- PLAYLISTS
-- ============================================================

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
    CONSTRAINT fk_playlist_channel FOREIGN KEY(channel_id) REFERENCES source.channels(id),
    CONSTRAINT uq_playlist_platform UNIQUE(platform_playlist_id)
);

-- ============================================================
-- VIDEOS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL,
    playlist_id UUID,
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
    current_payload_version_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    version BIGINT NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_platform_video UNIQUE(platform_video_id),
    CONSTRAINT fk_video_channel FOREIGN KEY(channel_id) REFERENCES source.channels(id)
);

CREATE INDEX IF NOT EXISTS idx_videos_published ON source.videos(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_channel ON source.videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_metadata ON source.videos USING GIN(metadata);

-- ============================================================
-- VIDEO PAYLOAD VERSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.video_payload_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    payload_hash TEXT NOT NULL,
    extractor_name VARCHAR(100),
    extractor_version VARCHAR(100),
    payload JSONB NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_payload_video FOREIGN KEY(video_id) REFERENCES source.videos(id)
);

CREATE INDEX IF NOT EXISTS idx_payload_video ON source.video_payload_versions(video_id);
CREATE INDEX IF NOT EXISTS idx_payload_json ON source.video_payload_versions USING GIN(payload jsonb_path_ops);

-- ============================================================
-- VIDEO FORMATS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.video_formats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payload_version_id UUID NOT NULL,
    format_id VARCHAR(50),
    ext VARCHAR(20),
    resolution VARCHAR(100),
    fps INTEGER,
    vcodec TEXT,
    acodec TEXT,
    filesize BIGINT,
    metadata JSONB
);

-- ============================================================
-- VIDEO CHAPTERS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.video_chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    start_seconds NUMERIC(12,3),
    end_seconds NUMERIC(12,3),
    title TEXT NOT NULL
);

-- ============================================================
-- VIDEO TAGS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.video_tags (
    video_id UUID NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY(video_id, tag)
);

-- ============================================================
-- THUMBNAILS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.video_thumbnails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    thumbnail_url TEXT,
    width INTEGER,
    height INTEGER,
    preference INTEGER,
    metadata JSONB
);

-- ============================================================
-- ASSETS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID,
    asset_type source.asset_type NOT NULL,
    storage_path TEXT NOT NULL,
    mime_type TEXT,
    checksum TEXT,
    file_size BIGINT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SUBTITLE TRACKS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.subtitle_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    language_code VARCHAR(20),
    is_auto_generated BOOLEAN,
    subtitle_url TEXT,
    subtitle_format VARCHAR(20),
    metadata JSONB
);

-- ============================================================
-- TRANSCRIPTS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    transcript_type source.transcript_type NOT NULL,
    language_code VARCHAR(20),
    version_number INTEGER NOT NULL,
    checksum TEXT,
    word_count INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SPEAKERS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.speakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    speaker_name TEXT,
    speaker_type VARCHAR(100),
    confidence_score NUMERIC(5,2),
    metadata JSONB
);

-- ============================================================
-- TRANSCRIPT SEGMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.transcript_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID NOT NULL,
    speaker_id UUID,
    start_seconds NUMERIC(12,3),
    end_seconds NUMERIC(12,3),
    content TEXT NOT NULL,
    embedding_status VARCHAR(50),
    metadata JSONB,
    CONSTRAINT fk_segment_transcript FOREIGN KEY(transcript_id) REFERENCES source.transcripts(id)
);

CREATE INDEX IF NOT EXISTS idx_segment_transcript ON source.transcript_segments(transcript_id);
CREATE INDEX IF NOT EXISTS idx_segment_speaker ON source.transcript_segments(speaker_id);

-- ============================================================
-- COMMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.video_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    platform_comment_id VARCHAR(255),
    parent_comment_id VARCHAR(255),
    author_name TEXT,
    author_channel_id TEXT,
    content TEXT,
    like_count BIGINT,
    published_at TIMESTAMPTZ,
    metadata JSONB
) PARTITION BY HASH(video_id);

-- ============================================================
-- INGESTION JOBS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(100),
    target_id UUID,
    status source.job_status NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB
);

-- ============================================================
-- EXTRACTION JOBS
-- ============================================================

CREATE TABLE IF NOT EXISTS source.extraction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID,
    model_name VARCHAR(255),
    model_version VARCHAR(255),
    status source.job_status,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB
);
