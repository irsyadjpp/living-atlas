"""Event integration for enrichment-service.

Handles:
- Consuming transcript.normalized to trigger story extraction
- Producing story.extracted and knowledge.extracted events
- Event schema validation
- DLQ handling for failed events

Uses standard topic names from EventTopics.java.
"""

import asyncio
import uuid
from typing import Optional
from datetime import datetime

import structlog
from ai_shared.config import ServiceConfig
from ai_shared.database import Database
from ai_shared.redpanda import EventProducer, EventConsumer
from ai_shared.events import TranscriptGenerated, KnowledgeExtracted

from enrichment.application.service import EnrichmentService

logger = structlog.get_logger(__name__)


class EnrichmentEventIntegration:
    """Event-driven integration for enrichment service (3-stage pipeline)."""

    def __init__(
        self,
        config: ServiceConfig,
        db: Database,
        enrichment_service: EnrichmentService,
    ):
        self.config = config
        self.db = db
        self.enrichment_service = enrichment_service
        
        # Event producer
        self.producer = EventProducer(config)
        
        # Event consumer
        self.consumer = EventConsumer(config, group_id="enrichment-service")
        
        # Running state
        self._running = False
        self._consume_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start event producer and consumer."""
        logger.info("enrichment_event_integration_starting")
        
        # Start producer (service already started in lifespan)
        
        # Register handler for transcript normalized events
        self.consumer.register_handler(
            "transcript.normalized",
            self._handle_transcript_normalized,
        )
        
        # Start consumer
        await self.consumer.start(["transcript.normalized"])
        
        # Start consume loop in background
        self._running = True
        self._consume_task = asyncio.create_task(self.consumer.consume_loop())
        
        logger.info("enrichment_event_integration_started")

    async def stop(self):
        """Stop event producer and consumer."""
        logger.info("enrichment_event_integration_stopping")
        
        self._running = False
        
        # Stop consume task
        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass
            self._consume_task = None
        
        # Stop consumer (producer stopped by service lifespan)
        await self.consumer.stop()
        
        logger.info("enrichment_event_integration_stopped")

    async def _handle_transcript_normalized(self, event_data: dict):
        """Handle transcript.normalized event and trigger story extraction.

        Args:
            event_data: Raw event data from Kafka
        """
        try:
            # Validate event schema
            event = TranscriptGenerated(**event_data)
            
            logger.info(
                "transcript_generated_event_received",
                video_id=str(event.video_id),
                transcript_id=str(event.transcript_id),
                source_type=event.source_type,
                word_count=event.word_count,
                avg_confidence=event.avg_confidence,
            )

            # Retrieve transcript text from database
            transcript_text = await self._get_transcript_text(event.transcript_id)
            
            if not transcript_text:
                logger.error(
                    "transcript_not_found",
                    transcript_id=str(event.transcript_id),
                )
                return

            # Prepare video metadata
            video_metadata = {
                "video_id": str(event.video_id),
                "transcript_id": str(event.transcript_id),
                "title": "Unknown",  # Would need to fetch from source.videos
                "description": "",
                "channel_id": "",
                "duration_seconds": event.duration_seconds,
                "language_code": event.language_detected,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            }

            # Process 3-stage pipeline
            canonical_story, validation_result = await self.enrichment_service.process_transcript_to_canonical_story(
                video_id=str(event.video_id),
                transcript_id=str(event.transcript_id),
                transcript_text=transcript_text,
                video_metadata=video_metadata,
            )

            # Event production handled by service
            logger.info(
                "canonical_story_processed",
                video_id=str(event.video_id),
                canonical_story_id=canonical_story.source_video_id,
                quality_score=validation_result.get("quality_score"),
                ready_for_graph=validation_result.get("ready_for_graph"),
            )

        except Exception as e:
            logger.error(
                "transcript_generated_handler_failed",
                video_id=event_data.get("video_id"),
                error=str(e),
                exc_info=True,
            )
            # TODO: Send to DLQ for retry
            await self._send_to_dlq("transcript.normalized", event_data, str(e))

    async def _get_transcript_text(self, transcript_id: str) -> Optional[str]:
        """Retrieve transcript text from database.

        Args:
            transcript_id: UUID of the transcript

        Returns:
            Transcript text or None if not found
        """
        try:
            # Query source.transcripts table for transcript content
            result = await self.db.fetchrow(
                """
                SELECT t.content, t.language
                FROM source.transcripts t
                WHERE t.id = $1
                """,
                transcript_id,
            )
            
            if result:
                return result.get("content", "")
            return None

        except Exception as e:
            logger.error(
                "transcript_retrieval_failed",
                transcript_id=transcript_id,
                error=str(e),
            )
            return None

    async def _send_to_dlq(self, original_topic: str, event_data: dict, error_message: str):
        """Send failed event to Dead Letter Queue.

        Args:
            original_topic: Original topic the event came from
            event_data: Original event data
            error_message: Error message for why it failed
        """
        try:
            # Store in ai.pipeline_failed_jobs table
            await self.db.execute(
                """
                INSERT INTO ai.pipeline_failed_jobs (
                    pipeline_run_id, stage_name, error_type, 
                    error_message, payload, retry_count
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                str(uuid.uuid4()),  # Generate a pipeline_run_id for tracking
                "enrichment",
                "handler_error",
                error_message,
                event_data,
                0,
            )
            
            logger.info(
                "event_sent_to_dlq",
                original_topic=original_topic,
                error=error_message,
            )

        except Exception as e:
            logger.error(
                "dlq_insert_failed",
                original_topic=original_topic,
                error=str(e),
            )