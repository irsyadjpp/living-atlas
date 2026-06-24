-- Migration 007: Add Video Processing State Machine
-- This migration adds state machine support for background processing

-- Create video_processing_state enum
CREATE TYPE video_processing_state AS ENUM (
    -- Initial states
    'SUBMITTED',
    'QUEUED',
    
    -- Metadata stage
    'METADATA_EXTRACTING',
    'METADATA_EXTRACTED',
    
    -- Transcript stage
    'TRANSCRIPT_EXTRACTING',
    'TRANSCRIPT_READY',
    
    -- Canonicalization stage
    'CANONICALIZING',
    'CANONICALIZED',
    
    -- Knowledge extraction stage
    'KNOWLEDGE_EXTRACTING',
    'KNOWLEDGE_READY',
    
    -- Graph sync stage
    'GRAPH_SYNCING',
    'GRAPH_READY',
    
    -- Article generation stage
    'ARTICLES_GENERATING',
    'ARTICLES_GENERATED',
    
    -- Final states
    'PUBLISHED',
    'COMPLETED',
    
    -- Error states
    'FAILED_METADATA',
    'FAILED_TRANSCRIPT',
    'FAILED_LLM',
    'FAILED_ARTICLE',
    'FAILED_GRAPH',
    'FAILED_REVIEW',
    'MANUAL_REVIEW_REQUIRED'
);

-- Add processing state columns to source.videos
ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS processing_state video_processing_state DEFAULT 'SUBMITTED';

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP;

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP;

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS error_message TEXT;

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;

-- Add check constraint for processing_state
ALTER TABLE source.videos 
ADD CONSTRAINT chk_processing_state 
CHECK (processing_state IN (
    'SUBMITTED', 'QUEUED', 'METADATA_EXTRACTING', 'METADATA_EXTRACTED',
    'TRANSCRIPT_EXTRACTING', 'TRANSCRIPT_READY', 'CANONICALIZING', 'CANONICALIZED',
    'KNOWLEDGE_EXTRACTING', 'KNOWLEDGE_READY', 'GRAPH_SYNCING', 'GRAPH_READY',
    'ARTICLES_GENERATING', 'ARTICLES_GENERATED', 'PUBLISHED', 'COMPLETED',
    'FAILED_METADATA', 'FAILED_TRANSCRIPT', 'FAILED_LLM', 'FAILED_ARTICLE',
    'FAILED_GRAPH', 'FAILED_REVIEW', 'MANUAL_REVIEW_REQUIRED'
));

-- Add indexes for state-based queries
CREATE INDEX IF NOT EXISTS idx_videos_processing_state 
ON source.videos(processing_state);

CREATE INDEX IF NOT EXISTS idx_videos_processing_state_priority 
ON source.videos(processing_state, priority);

CREATE INDEX IF NOT EXISTS idx_videos_queued 
ON source.videos(processing_state) 
WHERE processing_state = 'QUEUED';

CREATE INDEX IF NOT EXISTS idx_videos_failed 
ON source.videos(processing_state) 
WHERE processing_state LIKE 'FAILED_%';

-- Add function to transition processing state with validation
CREATE OR REPLACE FUNCTION transition_video_processing_state(
    p_video_id UUID,
    p_new_state video_processing_state,
    p_error_message TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    current_state video_processing_state;
    valid_transition BOOLEAN := FALSE;
BEGIN
    -- Get current state
    SELECT processing_state INTO current_state
    FROM source.videos
    WHERE id = p_video_id;
    
    -- Define valid transitions
    IF current_state = 'SUBMITTED' AND p_new_state IN ('QUEUED') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'QUEUED' AND p_new_state IN ('METADATA_EXTRACTING', 'FAILED_METADATA') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'METADATA_EXTRACTING' AND p_new_state IN ('METADATA_EXTRACTED', 'FAILED_METADATA') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'METADATA_EXTRACTED' AND p_new_state IN ('TRANSCRIPT_EXTRACTING', 'COMPLETED') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'TRANSCRIPT_EXTRACTING' AND p_new_state IN ('TRANSCRIPT_READY', 'FAILED_TRANSCRIPT', 'MANUAL_REVIEW_REQUIRED') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'TRANSCRIPT_READY' AND p_new_state IN ('CANONICALIZING') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'CANONICALIZING' AND p_new_state IN ('CANONICALIZED', 'FAILED_LLM') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'CANONICALIZED' AND p_new_state IN ('KNOWLEDGE_EXTRACTING') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'KNOWLEDGE_EXTRACTING' AND p_new_state IN ('KNOWLEDGE_READY', 'FAILED_LLM') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'KNOWLEDGE_READY' AND p_new_state IN ('GRAPH_SYNCING') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'GRAPH_SYNCING' AND p_new_state IN ('GRAPH_READY', 'FAILED_GRAPH') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'GRAPH_READY' AND p_new_state IN ('ARTICLES_GENERATING', 'COMPLETED') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'ARTICLES_GENERATING' AND p_new_state IN ('ARTICLES_GENERATED', 'FAILED_ARTICLE') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'ARTICLES_GENERATED' AND p_new_state IN ('PUBLISHED') THEN
        valid_transition := TRUE;
    ELSIF current_state = 'PUBLISHED' AND p_new_state IN ('COMPLETED') THEN
        valid_transition := TRUE;
    
    -- Error recovery transitions
    ELSIF current_state LIKE 'FAILED_%' AND p_new_state = 'QUEUED' THEN
        valid_transition := TRUE;
    ELSIF p_new_state = 'MANUAL_REVIEW_REQUIRED' THEN
        valid_transition := TRUE;
    END IF;
    
    IF valid_transition THEN
        -- Update state
        UPDATE source.videos
        SET processing_state = p_new_state,
            processing_started_at = COALESCE(processing_started_at, CASE WHEN p_new_state != 'SUBMITTED' AND p_new_state != 'QUEUED' THEN now() ELSE processing_started_at END),
            processing_completed_at = CASE WHEN p_new_state = 'COMPLETED' THEN now() WHEN p_new_state = 'PUBLISHED' THEN now() ELSE processing_completed_at END,
            error_message = p_error_message,
            retry_count = CASE WHEN p_new_state LIKE 'FAILED_%' THEN retry_count + 1 ELSE retry_count END,
            updated_at = now()
        WHERE id = p_video_id;
        
        RETURN TRUE;
    ELSE
        RAISE EXCEPTION 'Invalid state transition from % to %', current_state, p_new_state;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON TYPE video_processing_state IS 'State of video processing in background pipeline';
COMMENT ON COLUMN source.videos.processing_state IS 'Current state in processing pipeline';
COMMENT ON COLUMN source.videos.processing_started_at IS 'When background processing started';
COMMENT ON COLUMN source.videos.processing_completed_at IS 'When background processing completed';
COMMENT ON COLUMN source.videos.error_message IS 'Error message if processing failed';
COMMENT ON COLUMN source.videos.retry_count IS 'Number of retry attempts';
COMMENT ON COLUMN source.videos.max_retries IS 'Maximum allowed retry attempts';
COMMENT ON FUNCTION transition_video_processing_state IS 'Safely transition video processing state with validation';