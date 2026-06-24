"""Event consumer for ingestion service.

Consumes:
- source.submitted: from content-service (Spring Boot), triggers YouTube crawling

Produces:
- source.metadata.imported
- transcript.imported
"""

import structlog
import json
import uuid
from typing import Optional

from ai_shared.redpanda import EventConsumer
from ai_shared.database import Database
from ingestion.application.crawler import CrawlerService
from ingestion.infrastructure.youtube import YouTubeClient

logger = structlog.get_logger(__name__)


class IngestionEventConsumer:
    """Consumes events from Redpanda and triggers ingestion workflows."""

    def __init__(self, db: Database, crawler: CrawlerService, event_consumer: EventConsumer):
        self.db = db
        self.crawler = crawler
        self.consumer = event_consumer
        self._running = False

    async def start(self):
        """Register handlers and start consuming."""
        self.consumer.register_handler("source.submitted", self.handle_source_submitted)
        await self.consumer.start(["source.submitted"])
        self._running = True
        logger.info("ingestion_consumer_started", topics=["source.submitted"])

    async def handle_source_submitted(self, event: dict):
        """Handle source.submitted event from content-service.

        The event arrives as AiBridgeEvent JSON (from Spring Boot):
        {
            "eventId": "...", "eventType": "source.submitted",
            "producer": "content-service", "aggregateId": "uuid",
            "dataJson": "{\"sourceType\":\"youtube_video\",\"platformSourceId\":\"dQw4w9WgXcQ\",...}"
        }

        We extract the actual data from dataJson field.
        """
        # Extract payload — it's either in dataJson (from Spring Boot AiBridgeEvent)
        # or flat directly (from Python producers)
        data = event
        data_json_str = event.get("dataJson")
        if data_json_str:
            import json as json_mod
            try:
                data = json_mod.loads(data_json_str)
            except (json_mod.JSONDecodeError, TypeError):
                data = event

        source_type = data.get("sourceType", "")
        platform_source_id = data.get("platformSourceId", "")
        channel_id_str = data.get("channelId")

        logger.info(
            "source_submitted_received",
            source_type=source_type,
            platform_source_id=platform_source_id,
        )

        channel_uuid = uuid.UUID(channel_id_str) if channel_id_str else None

        try:
            if source_type == "youtube_video":
                # Crawl single video
                result = await self.crawler.crawl_video(
                    platform_video_id=platform_source_id,
                    channel_id=channel_uuid,
                )
                logger.info(
                    "video_crawl_completed_from_event",
                    video_id=result.get("video_id"),
                    status=result.get("status"),
                )

            elif source_type == "youtube_channel":
                # Crawl entire channel
                result = await self.crawler.crawl_channel(
                    url=f"https://www.youtube.com/@{platform_source_id}",
                    max_videos=50,
                )
                logger.info(
                    "channel_crawl_completed_from_event",
                    channel_id=result.get("channel_id"),
                    videos_discovered=result.get("videos_discovered"),
                )

            else:
                logger.warning("unknown_source_type", source_type=source_type)

        except Exception as e:
            logger.error(
                "source_crawl_failed",
                source_type=source_type,
                platform_source_id=platform_source_id,
                error=str(e),
            )

    async def stop(self):
        """Stop the consumer."""
        self._running = False
        await self.consumer.stop()
        logger.info("ingestion_consumer_stopped")