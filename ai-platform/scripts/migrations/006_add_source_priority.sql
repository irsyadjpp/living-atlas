-- Migration 006: Add Source Priority System
-- This migration adds priority levels to optimize processing costs

-- Create source_priority enum
CREATE TYPE source_priority AS ENUM ('HIGH', 'MEDIUM', 'LOW', 'SKIP');

-- Add priority column to source.channels
ALTER TABLE source.channels 
ADD COLUMN IF NOT EXISTS default_priority source_priority DEFAULT 'MEDIUM';

-- Add priority column to source.videos
ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS priority source_priority DEFAULT 'MEDIUM';

-- Add column to track if priority was manually overridden
ALTER TABLE source.videos 
ADD COLUMN IF NOT EXISTS priority_override_reason TEXT;

-- Add index for querying by priority
CREATE INDEX IF NOT EXISTS idx_videos_priority 
ON source.videos(priority);

CREATE INDEX IF NOT EXISTS idx_videos_priority_state 
ON source.videos(priority, processing_state);

-- Add check constraint
ALTER TABLE source.videos 
ADD CONSTRAINT chk_source_priority 
CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW', 'SKIP'));

-- Add comments
COMMENT ON TYPE source_priority IS 'Priority level for video processing';
COMMENT ON COLUMN source.channels.default_priority IS 'Default priority for videos from this channel';
COMMENT ON COLUMN source.videos.priority IS 'Processing priority for this video';
COMMENT ON COLUMN source.videos.priority_override_reason IS 'Reason for manual priority override';

-- Set default priorities for known important channels (example data)
-- This should be adjusted based on actual channel data
UPDATE source.channels 
SET default_priority = 'HIGH' 
WHERE name IN (
    'Jurnal Risa',
    'Nadia Omara',
    'Hirotada Radifan'
);

UPDATE source.channels 
SET default_priority = 'LOW' 
WHERE subscriber_count < 10000 OR subscriber_count IS NULL;

-- Add function to inherit priority from channel if not set
CREATE OR REPLACE FUNCTION inherit_channel_priority()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.priority IS NULL THEN
        SELECT default_priority INTO NEW.priority
        FROM source.channels
        WHERE id = NEW.channel_id;
        
        -- Default to MEDIUM if channel priority is not set
        IF NEW.priority IS NULL THEN
            NEW.priority = 'MEDIUM';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to inherit channel priority
DROP TRIGGER IF EXISTS trigger_inherit_channel_priority ON source.videos;
CREATE TRIGGER trigger_inherit_channel_priority
    BEFORE INSERT OR UPDATE OF priority, channel_id ON source.videos
    FOR EACH ROW
    WHEN (NEW.priority IS NULL OR (OLD.channel_id IS DISTINCT FROM NEW.channel_id AND NEW.priority = 'MEDIUM'))
    EXECUTE FUNCTION inherit_channel_priority();

-- Add comment for the trigger
COMMENT ON FUNCTION inherit_channel_priority IS 'Inherit default priority from channel if video priority is not set';