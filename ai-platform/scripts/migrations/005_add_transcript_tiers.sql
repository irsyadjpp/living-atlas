-- Migration 005: Add Transcript Tiers and Manual Review Support
-- This migration adds support for the 4-tier ingestion strategy

-- Add transcript tier columns to source.videos
ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS transcript_tier VARCHAR(20);
-- Values: TIER1_MANUAL, TIER2_AUTO, TIER3_CLOUD, TIER4_MANUAL

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS transcript_quality VARCHAR(20);
-- Values: high, medium, low, pending

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS transcript_quality_score FLOAT DEFAULT NULL;
-- Score: 0.0 - 1.0

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS manual_review_required BOOLEAN DEFAULT FALSE;

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS manual_review_status VARCHAR(20);
-- Values: pending, in_progress, completed, skipped

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS manual_review_notes TEXT;

-- Add transcript source tier to source.transcripts
ALTER TABLE source.transcripts 
ADD COLUMN IF NOT EXISTS source_tier VARCHAR(20);
-- Values: TIER1_MANUAL, TIER2_AUTO, TIER3_CLOUD, TIER4_MANUAL

ALTER TABLE source.transcripts 
ADD COLUMN IF NOT EXISTS quality_score FLOAT DEFAULT NULL;

ALTER TABLE source.transcripts 
ADD COLUMN IF NOT EXISTS transcription_cost_usd DECIMAL(10, 4) DEFAULT NULL;

-- Add indexes for querying by tier and review status
CREATE INDEX IF NOT EXISTS idx_videos_transcript_tier 
ON source.videos(transcript_tier);

CREATE INDEX IF NOT EXISTS idx_videos_manual_review_required 
ON source.videos(manual_review_required) 
WHERE manual_review_required = true;

CREATE INDEX IF NOT EXISTS idx_videos_manual_review_status 
ON source.videos(manual_review_status);

CREATE INDEX IF NOT EXISTS idx_transcripts_source_tier 
ON source.transcripts(source_tier);

-- Add check constraints
ALTER TABLE source.videos 
ADD CONSTRAINT chk_transcript_tier 
CHECK (transcript_tier IN ('TIER1_MANUAL', 'TIER2_AUTO', 'TIER3_CLOUD', 'TIER4_MANUAL', NULL));

ALTER TABLE source.videos 
ADD CONSTRAINT chk_transcript_quality 
CHECK (transcript_quality IN ('high', 'medium', 'low', 'pending', NULL));

ALTER TABLE source.videos 
ADD CONSTRAINT chk_manual_review_status 
CHECK (manual_review_status IN ('pending', 'in_progress', 'completed', 'skipped', NULL));

ALTER TABLE source.videos 
ADD CONSTRAINT chk_quality_score_range 
CHECK (transcript_quality_score IS NULL OR (transcript_quality_score >= 0.0 AND transcript_quality_score <= 1.0));

-- Add comment to document the columns
COMMENT ON COLUMN source.videos.transcript_tier IS 'Ingestion tier used for transcript extraction';
COMMENT ON COLUMN source.videos.transcript_quality IS 'Qualitative assessment of transcript quality';
COMMENT ON COLUMN source.videos.transcript_quality_score IS 'Quantitative quality score (0.0-1.0)';
COMMENT ON COLUMN source.videos.manual_review_required IS 'Whether video requires manual review';
COMMENT ON COLUMN source.videos.manual_review_status IS 'Status of manual review workflow';
COMMENT ON COLUMN source.transcripts.source_tier IS 'Ingestion tier that produced this transcript';
COMMENT ON COLUMN source.transcripts.quality_score IS 'Quality score of transcript (0.0-1.0)';
COMMENT ON COLUMN source.transcripts.transcription_cost_usd IS 'Cost of transcription in USD';

-- Create table for manual review queue
CREATE TABLE IF NOT EXISTS source.manual_review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES source.videos(id) ON DELETE CASCADE,
    channel_id UUID REFERENCES source.channels(id) ON DELETE SET NULL,
    priority VARCHAR(20) DEFAULT 'MEDIUM',  -- HIGH, MEDIUM, LOW
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, skipped
    assigned_to UUID REFERENCES users.users(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    review_notes TEXT,
    original_transcript TEXT,
    corrected_transcript TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    
    CONSTRAINT chk_review_queue_priority 
    CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    
    CONSTRAINT chk_review_queue_status 
    CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped'))
);

CREATE INDEX idx_manual_review_queue_status 
ON source.manual_review_queue(status) 
WHERE status = 'pending';

CREATE INDEX idx_manual_review_queue_priority_status 
ON source.manual_review_queue(priority, status);

CREATE INDEX idx_manual_review_queue_assigned_to 
ON source.manual_review_queue(assigned_to) 
WHERE assigned_to IS NOT NULL;

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_manual_review_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_manual_review_queue_updated_at
    BEFORE UPDATE ON source.manual_review_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_manual_review_queue_updated_at();

-- Add comment
COMMENT ON TABLE source.manual_review_queue IS 'Queue for manual transcript review and correction';