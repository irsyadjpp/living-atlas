-- Create Source Schema Tables for AI Platform
-- This creates the minimal source schema needed for canonical stories

CREATE TABLE IF NOT EXISTS source.videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL,
    platform_video_id VARCHAR(255) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    view_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_state VARCHAR(50) DEFAULT 'pending'
);

CREATE INDEX idx_source_videos_channel_id ON source.videos(channel_id);
CREATE INDEX idx_source_videos_platform_video_id ON source.videos(platform_video_id);
CREATE INDEX idx_source_videos_published_at ON source.videos(published_at);
CREATE INDEX idx_source_videos_processing_state ON source.videos(processing_state);

CREATE TABLE IF NOT EXISTS source.channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_channel_id VARCHAR(255) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    subscriber_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source.transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES source.videos(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    language_code VARCHAR(10) DEFAULT 'en',
    version_number INTEGER DEFAULT 1,
    word_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_source_transcripts_video_id ON source.transcripts(video_id);
CREATE INDEX idx_source_transcripts_source_type ON source.transcripts(source_type);

CREATE TABLE IF NOT EXISTS source.transcript_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID NOT NULL REFERENCES source.transcripts(id) ON DELETE CASCADE,
    start_seconds DECIMAL(10,2) NOT NULL,
    end_seconds DECIMAL(10,2) NOT NULL,
    content TEXT NOT NULL,
    confidence DECIMAL(3,2),
    embedding_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_source_transcript_segments_transcript_id ON source.transcript_segments(transcript_id);
CREATE INDEX idx_source_transcript_segments_start_seconds ON source.transcript_segments(start_seconds);

-- Add processing state enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'pending' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'video_processing_state')) THEN
        CREATE TYPE video_processing_state AS ENUM ('pending', 'downloading', 'transcribing', 'processing', 'completed', 'failed');
    END IF;
END
$$;

ALTER TABLE source.videos ALTER COLUMN processing_state TYPE video_processing_state USING processing_state::video_processing_state;