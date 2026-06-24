"""Enrichment Service - Updated with 3-Stage Knowledge Pipeline.

Replaces 6 separate extractors with:
1. Story Canonicalization (transcript → canonical JSON)
2. Knowledge Normalization (canonical JSON → normalized JSON)
3. Knowledge Validation (normalized JSON → validated JSON + quality score)

All articles and knowledge graph now come from Validated Canonical Story.
"""

import asyncio
import uuid
from typing import Optional
from datetime import datetime

import structlog
from ai_shared.database import Database
from ai_shared.config import ServiceConfig

from ai_shared.canonical_pipeline import (
    ThreeStageKnowledgePipeline,
    CanonicalizationResult,
)
from ai_shared.canonical import CanonicalStory
from ai_shared.redpanda import EventProducer

from enrichment.infrastructure.llm_client import LLMClientRouter

logger = structlog.get_logger(__name__)


class EnrichmentService:
    """Service layer for enrichment with 3-stage knowledge pipeline.
    
    New Architecture:
    - Transcript → Story Canonicalization → Knowledge Normalization → Validation
    - Validated Canonical Story as single source of truth
    - All downstream systems use validated canonical story
    """

    def __init__(self, db: Database, config: ServiceConfig):
        self.db = db
        self.config = config
        
        # Initialize LLM router
        self.llm_router = LLMClientRouter()
        
        # Initialize 3-stage pipeline
        self.knowledge_pipeline = ThreeStageKnowledgePipeline(self.llm_router)
        
        # Event producer (if configured)
        self.producer: Optional[EventProducer] = None

    async def start_event_producer(self):
        """Initialize event producer for canonical story events."""
        from ai_shared.redpanda import EventProducer
        self.producer = EventProducer(self.config)
        await self.producer.start()
        logger.info("event_producer_started")

    async def stop_event_producer(self):
        """Stop event producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("event_producer_stopped")

    async def process_transcript_to_canonical_story(
        self,
        video_id: str,
        transcript_id: str,
        transcript_text: str,
        video_metadata: dict,
    ) -> tuple[CanonicalStory, dict]:
        """Process transcript through 3-stage pipeline and store canonical story.
        
        Args:
            video_id: UUID of the source video
            transcript_id: UUID of the transcript
            transcript_text: Clean transcript text
            video_metadata: Video metadata from YouTube
            
        Returns:
            Tuple of (validated_canonical_story, validation_result)
        """
        canonical_story_id = str(uuid.uuid4())
        
        logger.info(
            "enrichment_started",
            video_id=video_id,
            transcript_id=transcript_id,
            transcript_length=len(transcript_text),
        )

        try:
            # Create enrichment run record
            await self._create_enrichment_run(
                canonical_story_id=canonical_story_id,
                video_id=video_id,
                transcript_id=transcript_id,
            )

            # Run 3-stage pipeline
            canonical_story, validation_result = await self.knowledge_pipeline.process(
                transcript_text=transcript_text,
                video_metadata=video_metadata,
            )

            # Store canonical story in database
            await self._store_canonical_story(
                canonical_story_id=canonical_story_id,
                canonical_story=canonical_story,
                validation_result=validation_result,
                video_id=video_id,
                transcript_id=transcript_id,
            )

            # Update enrichment run with completion
            total_cost = self._calculate_pipeline_cost(
                canonical_story_id,
                video_id,
            )
            
            await self._update_enrichment_run(
                canonical_story_id=canonical_story_id,
                status="completed" if validation_result.get("ready_for_graph") else "needs_review",
                cost_usd=total_cost,
            )

            # Update cost tracking
            await self._update_cost_tracking(
                video_id=video_id,
                canonical_cost_usd=total_cost,
            )

            # Produce canonical story extracted event if validation passed
            if validation_result.get("ready_for_graph") and self.producer:
                await self._produce_canonical_story_extracted_event(
                    canonical_story_id,
                    canonical_story,
                    validation_result,
                )

            logger.info(
                "enrichment_completed",
                video_id=video_id,
                canonical_story_id=canonical_story_id,
                quality_score=validation_result.get("quality_score"),
                ready_for_graph=validation_result.get("ready_for_graph"),
            )

            return canonical_story, validation_result

        except Exception as e:
            logger.error(
                "enrichment_failed",
                video_id=video_id,
                canonical_story_id=canonical_story_id,
                error=str(e),
                exc_info=True,
            )
            await self._update_enrichment_run(
                canonical_story_id=canonical_story_id,
                status="failed",
                error_message=str(e),
            )
            raise

    async def _create_enrichment_run(
        self,
        canonical_story_id: str,
        video_id: str,
        transcript_id: str,
    ):
        """Create enrichment run record in database."""
        await self.db.execute("""
            INSERT INTO ai.enrichment_runs (
                id, video_id, transcript_id, model_provider, model_name,
                status, started_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, canonical_story_id, video_id, transcript_id, "gemini", "gemini-1.5-flash", "running", datetime.utcnow())

    async def _store_canonical_story(
        self,
        canonical_story_id: str,
        canonical_story: CanonicalStory,
        validation_result: dict,
        video_id: str,
        transcript_id: str,
    ):
        """Store canonical story in canonical.stories table."""
        
        import json
        
        # Store main canonical story
        await self.db.execute("""
            INSERT INTO canonical.stories (
                id, title, summary, story_type, primary_culture, region, 
                time_period, confidence, source_video_id, source_transcript_id,
                extraction_date, extraction_model, extraction_version,
                is_validated, quality_score, validation_date, ready_for_graph,
                canonical_data, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 
                $15, $16, $17, $18, $19, $20, now(), now())
        """,
            canonical_story_id,
            canonical_story.story.title,
            canonical_story.story.summary,
            canonical_story.story.story_type.value,
            canonical_story.story.primary_culture,
            canonical_story.story.region,
            canonical_story.story.time_period,
            canonical_story.story.confidence,
            video_id,
            transcript_id,
            canonical_story.extraction_date,
            canonical_story.extraction_model,
            canonical_story.extraction_version,
            True,  # is_validated
            validation_result.get("quality_score"),
            datetime.utcnow(),
            validation_result.get("ready_for_graph", False),
            json.dumps(canonical_story.model_dump(), ensure_ascii=False),
        )

        # Store validation result
        validation_id = str(uuid.uuid4())
        await self.db.execute("""
            INSERT INTO canonical.validation_results (
                id, story_id, story_version, quality_score, ready_for_graph,
                validation_errors, validation_warnings, validation_date,
                validator_model, validator_version
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
            validation_id,
            canonical_story_id,
            canonical_story.extraction_version,
            validation_result.get("quality_score"),
            validation_result.get("ready_for_graph", False),
            json.dumps(validation_result.get("errors", [])),
            json.dumps(validation_result.get("warnings", [])),
            datetime.utcnow(),
            "gemini",
            "1.0",
        )

        # Store entities from canonical story
        for entity in canonical_story.entities:
            entity_id = str(uuid.uuid4())
            await self.db.execute("""
                INSERT INTO canonical.entities (
                    id, story_id, name, type, role, confidence, 
                    canonical_data, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, now(), now())
            """,
                entity_id,
                canonical_story_id,
                entity.name,
                entity.type.value,
                entity.role,
                entity.confidence,
                json.dumps(entity.model_dump(), ensure_ascii=False),
            )

        # Store claims from canonical story
        for claim in canonical_story.claims:
            claim_id = str(uuid.uuid4())
            await self.db.execute("""
                INSERT INTO canonical.claims (
                    id, story_id, text, claim_type, confidence, 
                    canonical_data, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, now(), now())
            """,
                claim_id,
                canonical_story_id,
                claim.text,
                claim.claim_type.value,
                claim.confidence,
                json.dumps(claim.model_dump(), ensure_ascii=False),
            )

        # Store relationships from canonical story
        for relationship in canonical_story.relationships:
            relationship_id = str(uuid.uuid4())
            await self.db.execute("""
                INSERT INTO canonical.relationships (
                    id, story_id, source_entity_id, target_entity_id, 
                    relationship_type, confidence, canonical_data, 
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, now(), now())
            """,
                relationship_id,
                canonical_story_id,
                relationship.source,
                relationship.target,
                relationship.relationship_type.value,
                relationship.confidence,
                json.dumps(relationship.model_dump(), ensure_ascii=False),
            )

        logger.info(
            "canonical_story_stored",
            story_id=canonical_story_id,
            entity_count=len(canonical_story.entities),
            claim_count=len(canonical_story.claims),
            relationship_count=len(canonical_story.relationships),
        )

    async def _calculate_pipeline_cost(
        self,
        canonical_story_id: str,
        video_id: str,
    ) -> float:
        """Calculate total cost for the pipeline from enrichment run."""
        result = await self.db.fetchrow(
            "SELECT COALESCE(cost_usd, 0.0) as cost FROM ai.enrichment_runs WHERE id = $1",
            canonical_story_id
        )
        return result["cost"] if result else 0.0

    async def _update_enrichment_run(
        self,
        canonical_story_id: str,
        status: str,
        cost_usd: Optional[float] = None,
        error_message: Optional[str] = None,
    ):
        """Update enrichment run with completion status."""
        await self.db.execute("""
            UPDATE ai.enrichment_runs
            SET status = $2,
                completed_at = now(),
                cost_usd = COALESCE($3, cost_usd),
                error_message = $4,
                updated_at = now()
            WHERE id = $1
        """, canonical_story_id, status, cost_usd, error_message)

    async def _update_cost_tracking(
        self,
        video_id: str,
        canonical_cost_usd: float,
    ):
        """Update cost tracking for the video."""
        await self.db.execute("""
            UPDATE source.videos
            SET canonical_cost_usd = $2,
                updated_at = now()
            WHERE id = $1
        """, video_id, canonical_cost_usd)

    async def _produce_canonical_story_extracted_event(
        self,
        canonical_story_id: str,
        canonical_story: CanonicalStory,
        validation_result: dict,
    ):
        """Produce event for downstream systems."""
        import json
        
        event_data = {
            "canonical_story_id": canonical_story_id,
            "video_id": canonical_story.story.source_video_id,
            "transcript_id": canonical_story.story.source_transcript_id,
            "title": canonical_story.story.title,
            "story_type": canonical_story.story.story_type.value,
            "quality_score": validation_result.get("quality_score"),
            "ready_for_graph": validation_result.get("ready_for_graph"),
            "entity_count": len(canonical_story.entities),
            "claim_count": len(canonical_story.claims),
            "relationship_count": len(canonical_story.relationships),
        }
        
        if self.producer:
            await self.producer.produce(
                topic="canonical.story.extracted",
                key=canonical_story_id,
                value=event_data,
            )
            logger.info(
                "canonical_story_event_produced",
                canonical_story_id=canonical_story_id,
            )