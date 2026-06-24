"""Background Worker for Video Processing.

Consumes video processing jobs from queue and processes them
through the pipeline using the state machine.
"""

import asyncio
import json
import structlog
from typing import Optional
from datetime import datetime

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from orchestration.application.state_machine import (
    StateMachine,
    VideoProcessingState,
    InvalidStateTransition,
    MaxRetriesExceeded,
)
from ai_shared.database import Database
from ai_shared.config import ServiceConfig

logger = structlog.get_logger(__name__)


class VideoProcessingWorker:
    """Background worker for processing videos through the pipeline.
    
    Consumes jobs from RabbitMQ/Redpanda queue and processes them
    in the background, transitioning through states using the state machine.
    """

    def __init__(
        self,
        db: Database,
        config: ServiceConfig,
        state_machine: Optional[StateMachine] = None,
        rabbitmq_url: Optional[str] = None,
    ):
        self.db = db
        self.config = config
        self.state_machine = state_machine or StateMachine(db)
        self.rabbitmq_url = rabbitmq_url or config.get("rabbitmq_url", "amqp://guest:guest@localhost/")
        self.running = False
        self.connection: Optional[aio_pika.RobustConnection] = None

    async def start(self):
        """Start the background worker."""
        logger.info("video_processing_worker_starting", rabbitmq_url=self.rabbitmq_url)
        
        try:
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            
            # Create channel
            channel = await self.connection.channel()
            
            # Set QoS (prefetch count)
            await channel.set_qos(prefetch_count=5)
            
            # Declare queues
            await self._declare_queues(channel)
            
            # Start consuming
            self.running = True
            await self._consume_jobs(channel)
            
        except Exception as e:
            logger.error("worker_startup_failed", error=str(e), exc_info=True)
            raise

    async def _declare_queues(self, channel):
        """Declare queues and exchanges."""
        # Main processing queue
        await channel.queue_declare(
            "video.processing",
            durable=True,
        )
        
        # Priority queues
        for priority in ["HIGH", "MEDIUM", "LOW"]:
            await channel.queue_declare(
                f"video.processing.{priority.lower()}",
                durable=True,
                arguments={
                    "x-max-priority": 10 if priority == "HIGH" else 5,
                }
            )
        
        # Dead letter queue for failed jobs
        await channel.queue_declare(
            "video.processing.dlq",
            durable=True,
        )
        
        logger.info("queues_declared")

    async def _consume_jobs(self, channel):
        """Consume jobs from the queue."""
        async with channel.iterator(
            queue="video.processing",
            no_ack=False,
        ) as queue_iter:
            logger.info("worker_started_consuming")
            
            async for message in queue_iter:
                try:
                    async with message.process(requeue=True):
                        await self._process_message(message)
                except Exception as e:
                    logger.error(
                        "message_processing_failed",
                        message_id=message.message_id,
                        error=str(e),
                        exc_info=True,
                    )

    async def _process_message(self, message: AbstractIncomingMessage):
        """Process a single message from the queue."""
        try:
            # Parse message body
            job_data = json.loads(message.body)
            
            video_id = job_data.get("video_id")
            action = job_data.get("action", "process")
            
            logger.info(
                "processing_job",
                video_id=video_id,
                action=action,
                message_id=message.message_id,
            )
            
            if action == "process":
                await self._process_video(video_id)
            elif action == "retry":
                await self._retry_video(video_id)
            elif action == "reset":
                await self._reset_video(video_id)
            else:
                logger.warning("unknown_action", action=action)
                
        except json.JSONDecodeError as e:
            logger.error("json_decode_error", message_body=message.body[:100])
            raise
        except Exception as e:
            logger.error("process_message_error", error=str(e), exc_info=True)
            raise

    async def _process_video(self, video_id: str):
        """Process a video through the pipeline."""
        # Get video details
        video = await self.db.fetchrow(
            """
            SELECT v.id, v.url, v.priority, v.processing_state, v.channel_id,
                   c.name as channel_name
            FROM source.videos v
            LEFT JOIN source.channels c ON v.channel_id = c.id
            WHERE v.id = $1
            """,
            video_id,
        )
        
        if not video:
            logger.error("video_not_found", video_id=video_id)
            return
        
        video = dict(video)
        current_state = VideoProcessingState(video["processing_state"])
        
        logger.info(
            "processing_video",
            video_id=video_id,
            current_state=current_state.value,
            priority=video["priority"],
        )
        
        try:
            # Check if we should skip this video
            if video["priority"] == "SKIP":
                await self.state_machine.transition(video_id, VideoProcessingState.COMPLETED)
                logger.info("video_skipped", video_id=video_id, reason="SKIP priority")
                return
            
            # Process based on current state
            if current_state == VideoProcessingState.QUEUED:
                await self._process_metadata_extraction(video)
            elif current_state == VideoProcessingState.METADATA_EXTRACTED:
                await self._process_transcript_extraction(video)
            elif current_state == VideoProcessingState.TRANSCRIPT_READY:
                await self._process_canonicalization(video)
            elif current_state == VideoProcessingState.CANONICALIZED:
                await self._process_knowledge_extraction(video)
            elif current_state == VideoProcessingState.KNOWLEDGE_READY:
                await self._process_graph_sync(video)
            elif current_state == VideoProcessingState.GRAPH_READY:
                await self._process_article_generation(video)
            else:
                logger.warning(
                    "video_in_unexpected_state",
                    video_id=video_id,
                    state=current_state.value,
                )
                
        except MaxRetriesExceeded:
            logger.error("max_retries_exceeded", video_id=video_id)
            # Send to DLQ or mark as permanently failed
            await self._send_to_dlq(video_id, "Max retries exceeded")
            
        except InvalidStateTransition as e:
            logger.error("invalid_transition", video_id=video_id, error=str(e))
            # Reset to QUEUED for retry
            await self.state_machine._update_state(video_id, VideoProcessingState.QUEUED, f"Invalid transition: {e}")
            
        except Exception as e:
            logger.error(
                "processing_failed",
                video_id=video_id,
                error=str(e),
                exc_info=True,
            )
            # Transition to appropriate error state
            error_state = self._determine_error_state(current_state)
            await self.state_machine.transition(video_id, error_state, str(e))

    async def _process_metadata_extraction(self, video: dict):
        """Extract video metadata."""
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.METADATA_EXTRACTING,
        )
        
        # Simulate metadata extraction (would call ingestion service)
        await asyncio.sleep(1)
        
        # Transition to extracted
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.METADATA_EXTRACTED,
        )
        
        logger.info("metadata_extraction_completed", video_id=video["id"])

    async def _process_transcript_extraction(self, video: dict):
        """Extract transcript using 4-tier strategy."""
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.TRANSCRIPT_EXTRACTING,
        )
        
        # Simulate transcript extraction (would call extraction service)
        await asyncio.sleep(2)
        
        # Transition to ready
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.TRANSCRIPT_READY,
        )
        
        logger.info("transcript_extraction_completed", video_id=video["id"])

    async def _process_canonicalization(self, video: dict):
        """Run 3-stage knowledge pipeline."""
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.CANONICALIZING,
        )
        
        # Simulate canonicalization (would call enrichment service)
        await asyncio.sleep(3)
        
        # Transition to canonicalized
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.CANONICALIZED,
        )
        
        logger.info("canonicalization_completed", video_id=video["id"])

    async def _process_knowledge_extraction(self, video: dict):
        """Extract knowledge."""
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.KNOWLEDGE_EXTRACTING,
        )
        
        # Knowledge extraction is done in canonicalization
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.KNOWLEDGE_READY,
        )
        
        logger.info("knowledge_extraction_completed", video_id=video["id"])

    async def _process_graph_sync(self, video: dict):
        """Sync to Neo4j knowledge graph."""
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.GRAPH_SYNCING,
        )
        
        # Simulate graph sync (would call Neo4j sync service)
        await asyncio.sleep(2)
        
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.GRAPH_READY,
        )
        
        logger.info("graph_sync_completed", video_id=video["id"])

    async def _process_article_generation(self, video: dict):
        """Generate articles (HIGH priority only)."""
        if video["priority"] != "HIGH":
            # Skip article generation for MEDIUM/LOW
            await self.state_machine.transition(
                video["id"],
                VideoProcessingState.COMPLETED,
            )
            logger.info(
                "article_generation_skipped",
                video_id=video["id"],
                priority=video["priority"],
            )
            return
        
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.ARTICLES_GENERATING,
        )
        
        # Simulate article generation (would call article service)
        await asyncio.sleep(2)
        
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.ARTICLES_GENERATED,
        )
        
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.PUBLISHED,
        )
        
        await self.state_machine.transition(
            video["id"],
            VideoProcessingState.COMPLETED,
        )
        
        logger.info("article_generation_completed", video_id=video["id"])

    def _determine_error_state(
        self,
        current_state: VideoProcessingState,
    ) -> VideoProcessingState:
        """Determine appropriate error state based on current state."""
        state_mapping = {
            VideoProcessingState.METADATA_EXTRACTING: VideoProcessingState.FAILED_METADATA,
            VideoProcessingState.TRANSCRIPT_EXTRACTING: VideoProcessingState.FAILED_TRANSCRIPT,
            VideoProcessingState.CANONICALIZING: VideoProcessingState.FAILED_LLM,
            VideoProcessingState.KNOWLEDGE_EXTRACTING: VideoProcessingState.FAILED_LLM,
            VideoProcessingState.GRAPH_SYNCING: VideoProcessingState.FAILED_GRAPH,
            VideoProcessingState.ARTICLES_GENERATING: VideoProcessingState.FAILED_ARTICLE,
        }
        
        return state_mapping.get(current_state, VideoProcessingState.FAILED_REVIEW)

    async def _retry_video(self, video_id: str):
        """Retry a failed video."""
        await self.state_machine.transition(video_id, VideoProcessingState.QUEUED)
        logger.info("video_retried", video_id=video_id)

    async def _reset_video(self, video_id: str):
        """Reset a video to QUEUED state (used for stale videos)."""
        current_state = await self.state_machine._get_current_state(video_id)
        
        await self.db.execute("""
            UPDATE source.videos
            SET processing_state = 'QUEUED',
                retry_count = 0,
                error_message = NULL,
                updated_at = now()
            WHERE id = $1
        """, video_id)
        
        logger.info(
            "video_reset",
            video_id=video_id,
            previous_state=current_state.value if current_state else None,
        )

    async def _send_to_dlq(self, video_id: str, reason: str):
        """Send video to dead letter queue."""
        # In production, this would publish to DLQ
        await self.db.execute("""
            UPDATE source.videos
            SET processing_state = 'FAILED_REVIEW',
                error_message = 'Sent to DLQ: ' || $2,
                updated_at = now()
            WHERE id = $1
        """, video_id, reason)
        
        logger.info("video_sent_to_dlq", video_id=video_id, reason=reason)

    async def stop(self):
        """Stop the background worker."""
        logger.info("video_processing_worker_stopping")
        self.running = False
        
        if self.connection:
            await self.connection.close()
            logger.info("worker_connection_closed")

    async def check_stale_videos(self, stale_threshold_minutes: int = 60):
        """Check for and reset stale videos."""
        stale_videos = await self.state_machine.get_stale_videos(stale_threshold_minutes)
        
        for video in stale_videos:
            await self.state_machine.reset_stale_video(video["id"])
        
        logger.info(
            "stale_videos_checked",
            count=len(stale_videos),
            threshold_minutes=stale_threshold_minutes,
        )