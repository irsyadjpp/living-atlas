CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS knowledge;

DO $$
BEGIN
    CREATE TYPE content.story_type AS ENUM (
        'investigation',
        'personal_experience',
        'folklore',
        'urban_legend',
        'historical',
        'cultural',
        'ritual',
        'mythology',
        'podcast_discussion'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE knowledge.evidence_level AS ENUM (
        'direct',
        'derived',
        'inferred',
        'generated'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS content.stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(500) UNIQUE,
    title TEXT NOT NULL,
    summary TEXT,
    story_type content.story_type NOT NULL,
    confidence_score NUMERIC(5, 2),
    canonical_source_video_id UUID,
    status VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content.story_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID,
    CONSTRAINT fk_story_versions_story
        FOREIGN KEY (story_id)
        REFERENCES content.stories (id)
);

CREATE TABLE IF NOT EXISTS content.story_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL,
    transcript_segment_id UUID,
    evidence_level knowledge.evidence_level NOT NULL,
    confidence_score NUMERIC(5, 2),
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT fk_story_evidence_story
        FOREIGN KEY (story_id)
        REFERENCES content.stories (id)
);

CREATE INDEX IF NOT EXISTS idx_story_versions_story_id
    ON content.story_versions (story_id);

CREATE INDEX IF NOT EXISTS idx_story_versions_story_id_version_number
    ON content.story_versions (story_id, version_number DESC);

CREATE INDEX IF NOT EXISTS idx_story_evidence_story_id
    ON content.story_evidence (story_id);
