"""Event producer for ingestion service events.

Uses standard topic names from EventTopics.java.
Produces:
- source.metadata.imported
- transcript.imported
- transcript.normalized
"""
import structlog
from typing import Optional
from ai_shared.redpanda import EventProducer

logger = structlog.get_logger(__name__)


class IngestionEventProducer:
    """Produces ingestion-related events to Redpanda."""

    def __init__(self, event_producer: Optional[EventProducer] = None):
        self.event_producer = event_producer

    async def emit_source_metadata_imported(self, source_id: str, source_type: str, metadata: dict):
        """Emit source.metadata.imported event after metadata extraction."""
        if self.event_producer:
            await self.event_producer.produce_event("source.metadata.imported", {
                "sourceId": source_id,
                "sourceType": source_type,
                **metadata
            })
            logger.info("event_emitted", topic="source.metadata.imported", source_id=source_id)

    async def emit_transcript_imported(self, source_id: str, transcript_id: str, metadata: dict):
        """Emit transcript.imported event after transcript retrieval."""
        if self.event_producer:
            await self.event_producer.produce_event("transcript.imported", {
                "sourceId": source_id,
                "transcriptId": transcript_id,
                **metadata
            })
            logger.info("event_emitted", topic="transcript.imported", transcript_id=transcript_id)

    async def emit_transcript_normalized(self, source_id: str, transcript_id: str, segments: list, stats: dict):
        """Emit transcript.normalized event after normalization."""
        if self.event_producer:
            await self.event_producer.produce_event("transcript.normalized", {
                "sourceId": source_id,
                "transcriptId": transcript_id,
                "segments": segments,
                "statistics": stats,
            })
            logger.info("event_emitted", topic="transcript.normalized", transcript_id=transcript_id)