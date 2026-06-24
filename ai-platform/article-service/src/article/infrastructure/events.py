"""Event integration for article-service.

Consumes article.generation.requested events and triggers article generation.
Produces article.generated events.

Uses standard topic names from EventTopics.java.
"""
import asyncio
import json
import uuid
from typing import Optional
from datetime import datetime

import structlog
from ai_shared.config import ServiceConfig
from ai_shared.database import Database
from ai_shared.redpanda import EventProducer, EventConsumer

from article.application.service import ArticleService
from ai_shared.canonical import CanonicalStory

logger = structlog.get_logger(__name__)


class ArticleEventIntegration:
    """Event-driven integration for article service."""

    def __init__(
        self,
        config: ServiceConfig,
        db: Database,
        article_service: ArticleService,
    ):
        self.config = config
        self.db = db
        self.article_service = article_service

        # Event producer
        self.producer = EventProducer(config)

        # Event consumer — listens on article.generation.requested
        self.consumer = EventConsumer(config, group_id="article-generation")

        # Running state
        self._running = False
        self._consume_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start event producer and consumer."""
        logger.info("article_event_integration_starting")

        # Start producer
        await self.producer.start()

        # Register handler for article generation requests
        self.consumer.register_handler(
            "article.generation.requested",
            self._handle_article_generation_requested,
        )

        # Start consumer
        await self.consumer.start(["article.generation.requested"])

        # Start consume loop in background
        self._running = True
        self._consume_task = asyncio.create_task(self.consumer.consume_loop())

        logger.info("article_event_integration_started")

    async def stop(self):
        """Stop event producer and consumer."""
        logger.info("article_event_integration_stopping")
        self._running = False

        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass
            self._consume_task = None

        await self.consumer.stop()
        await self.producer.stop()
        logger.info("article_event_integration_stopped")

    async def _handle_article_generation_requested(self, event_data: dict):
        """Handle article.generation.requested event.

        Args:
            event_data: {
                canonicalStoryId, knowledgeId, sourceId, jobId,
                articleType, generationConfig, language, validatedKnowledge
            }
        """
        try:
            canonical_story_id = event_data.get("canonicalStoryId")
            article_type = event_data.get("articleType", "narrative")
            language = event_data.get("language", "id")
            generation_config = event_data.get("generationConfig", {})

            if not canonical_story_id:
                logger.warning("missing_canonical_story_id", event=event_data)
                return

            logger.info(
                "article_generation_requested",
                canonical_story_id=canonical_story_id,
                article_type=article_type,
                language=language,
            )

            # Retrieve canonical story from database
            canonical_story = await self._get_canonical_story(canonical_story_id)
            if not canonical_story:
                logger.error(
                    "canonical_story_not_found",
                    canonical_story_id=str(canonical_story_id),
                )
                return

            # Generate article
            result = await self.article_service.generate_article(
                article_type=article_type,
                canonical_story_id=str(canonical_story_id),
                canonical_story=canonical_story,
                language=language,
                generation_config=generation_config,
            )

            logger.info(
                "article_generation_completed",
                canonical_story_id=str(canonical_story_id),
                article_type=article_type,
                quality_score=result.quality_score,
            )

            # Produce article.generated event
            await self._produce_article_generated_event(
                canonical_story_id=canonical_story_id,
                article_type=article_type,
                result=result,
                job_id=event_data.get("jobId"),
                knowledge_id=event_data.get("knowledgeId"),
                source_id=event_data.get("sourceId"),
            )

        except Exception as e:
            logger.error(
                "article_generation_failed",
                canonical_story_id=event_data.get("canonicalStoryId"),
                error=str(e),
                exc_info=True,
            )

    async def _get_canonical_story(self, canonical_story_id: str) -> Optional[CanonicalStory]:
        """Retrieve canonical story from database."""
        try:
            result = await self.db.fetchrow(
                "SELECT story_json FROM ai_platform.canonical_stories WHERE canonical_story_id = $1",
                str(canonical_story_id),
            )
            if result:
                data = json.loads(result["story_json"]) if isinstance(result["story_json"], str) else result["story_json"]
                return CanonicalStory(**data)
            return None
        except Exception as e:
            logger.error("canonical_story_retrieval_failed", canonical_story_id=str(canonical_story_id), error=str(e))
            return None

    async def _produce_article_generated_event(
        self,
        canonical_story_id,
        article_type: str,
        result,
        job_id=None,
        knowledge_id=None,
        source_id=None,
    ):
        """Produce article.generated event (standard topic name)."""
        article_draft_id = str(uuid.uuid4())
        event_data = {
            "canonicalStoryId": str(canonical_story_id),
            "knowledgeId": str(knowledge_id) if knowledge_id else None,
            "sourceId": str(source_id) if source_id else None,
            "jobId": str(job_id) if job_id else None,
            "articleDraftId": article_draft_id,
            "articleType": article_type,
            "title": getattr(result, 'title', 'Untitled') or 'Untitled',
            "wordCount": getattr(result, 'word_count', 0),
            "qualityScore": getattr(result, 'quality_score', 0.0),
            "generationMetadata": {
                "modelUsed": getattr(result, 'model_used', ''),
                "promptVersion": getattr(result, 'prompt_version', ''),
                "executionTimeMs": getattr(result, 'execution_time_ms', 0),
            },
        }

        await self.producer.produce_event("article.generated", event_data)
        logger.info(
            "article_generated_event_emitted",
            topic="article.generated",
            article_draft_id=article_draft_id,
            article_type=article_type,
        )