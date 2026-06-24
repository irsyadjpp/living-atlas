"""Pipeline state machine — coordinates multi-step processing pipelines (Updated for 3-Stage Knowledge Pipeline)."""

import json
import uuid
import structlog
from enum import Enum
from typing import Optional
from ai_shared.database import Database

logger = structlog.get_logger(__name__)


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVIEW = "needs_review"  # For low-quality canonical stories


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"  # For low-quality validation


PIPELINE_STEPS = [
    {"order": 1, "name": "ingestion", "service": "ingestion-service", "topic": "video.ingested"},
    {"order": 2, "name": "extraction", "service": "extraction-service", "topic": "transcript.generated"},
    {"order": 3, "name": "canonicalization", "service": "enrichment-service", "topic": "knowledge.extracted"},
    {"order": 4, "name": "quality_gate", "service": "orchestration-service", "topic": "quality.check"},
    {"order": 5, "name": "article_generation", "service": "article-service", "topic": "article.draft.created"},
    {"order": 6, "name": "knowledge_graph_sync", "service": "orchestration-service", "topic": "graph.synced"},
]


class PipelineExecutor:
    """State machine for pipeline execution.

    Manages creation, starting, step advancement, retry, and completion
    of multi-step processing pipelines across all AI platform services.
    """

    def __init__(self, db: Database, event_producer, neo4j_sync_service=None):
        self.db = db
        self.event_producer = event_producer
        self.neo4j_sync_service = neo4j_sync_service

    async def create_pipeline(self, video_url: str, pipeline_type: str = "full") -> uuid.UUID:
        """Create a new pipeline with all steps defined."""
        pipeline_id = uuid.uuid4()
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ai.pipelines (id, pipeline_type, status, current_step, metadata)
                VALUES ($1, $2, 'pending', 'ingestion', $3)
                """,
                pipeline_id, pipeline_type, json.dumps({"video_url": video_url}),
            )
            for step in PIPELINE_STEPS:
                if pipeline_type == "ingestion_only" and step["order"] > 1:
                    break
                await conn.execute(
                    """
                    INSERT INTO ai.pipeline_steps (pipeline_id, step_order, step_name, service_name, status)
                    VALUES ($1, $2, $3, $4, 'pending')
                    """,
                    pipeline_id, step["order"], step["name"], step["service"],
                )
        logger.info("pipeline_created", pipeline_id=str(pipeline_id), pipeline_type=pipeline_type)
        return pipeline_id

    async def start_pipeline(self, pipeline_id: uuid.UUID):
        """Start the first step of a pipeline."""
        await self._update_step_status(pipeline_id, "ingestion", StepStatus.RUNNING)
        await self._update_pipeline_status(pipeline_id, current_step="ingestion", status=PipelineStatus.RUNNING)
        if self.event_producer:
            await self.event_producer.produce(
                "pipeline.started",
                {"pipeline_id": str(pipeline_id), "status": "running", "current_step": "ingestion"},
                key=str(pipeline_id),
            )
        logger.info("pipeline_started", pipeline_id=str(pipeline_id))

    async def handle_step_completed(self, pipeline_id: uuid.UUID, step_name: str):
        """Advance pipeline to the next step after a step completes successfully."""
        step_order = next(s["order"] for s in PIPELINE_STEPS if s["name"] == step_name)
        next_step = next((s for s in PIPELINE_STEPS if s["order"] == step_order + 1), None)

        await self._update_step_status(pipeline_id, step_name, StepStatus.COMPLETED)

        # Check priority and skip steps accordingly
        video_priority = await self._get_video_priority(pipeline_id)
        
        # Skip logic based on priority:
        # HIGH: Full pipeline (all steps)
        # MEDIUM: Knowledge only (skip article_generation)
        # LOW: Metadata only (skip canonicalization, article_generation, graph_sync)
        # SKIP: Skip everything
        
        if video_priority == "SKIP":
            logger.info("pipeline_skipped_low_priority", pipeline_id=str(pipeline_id), priority=video_priority)
            await self._update_pipeline_status(pipeline_id, status=PipelineStatus.COMPLETED)
            return
        
        if video_priority == "LOW" and next_step:
            # LOW priority: only metadata and transcript
            if next_step["name"] in ["canonicalization", "quality_gate", "article_generation", "knowledge_graph_sync"]:
                logger.info(
                    "pipeline_step_skipped_low_priority",
                    pipeline_id=str(pipeline_id),
                    step=next_step["name"],
                    priority=video_priority
                )
                await self._update_step_status(pipeline_id, next_step["name"], StepStatus.SKIPPED)
                # Skip to end
                await self._update_pipeline_status(pipeline_id, status=PipelineStatus.COMPLETED)
                return
        
        if video_priority == "MEDIUM" and next_step:
            # MEDIUM priority: skip article generation only
            if next_step["name"] == "article_generation":
                logger.info(
                    "pipeline_step_skipped_medium_priority",
                    pipeline_id=str(pipeline_id),
                    step=next_step["name"],
                    priority=video_priority
                )
                await self._update_step_status(pipeline_id, next_step["name"], StepStatus.SKIPPED)
                # Skip article generation but continue to graph sync
                next_after_article = next((s for s in PIPELINE_STEPS if s["order"] == step_order + 2), None)
                if next_after_article:
                    await self._update_step_status(pipeline_id, next_after_article["name"], StepStatus.RUNNING)
                    await self._update_pipeline_status(pipeline_id, current_step=next_after_article["name"])
                    logger.info("pipeline_step_advanced", pipeline_id=str(pipeline_id), step=next_after_article["name"])
                else:
                    await self._update_pipeline_status(pipeline_id, status=PipelineStatus.COMPLETED)
                return

        # Special handling for quality gate after canonicalization
        if step_name == "canonicalization" and next_step and next_step["name"] == "quality_gate":
            await self._run_quality_gate(pipeline_id)
            return

        if next_step:
            await self._update_step_status(pipeline_id, next_step["name"], StepStatus.RUNNING)
            await self._update_pipeline_status(pipeline_id, current_step=next_step["name"])
            
            # Special handling for knowledge graph sync
            if next_step["name"] == "knowledge_graph_sync" and self.neo4j_sync_service:
                await self._run_neo4j_sync(pipeline_id)
                return
            
            logger.info("pipeline_step_advanced", pipeline_id=str(pipeline_id), step=next_step["name"])
        else:
            await self._update_pipeline_status(pipeline_id, PipelineStatus.COMPLETED)
            if self.event_producer:
                await self.event_producer.produce(
                    "pipeline.completed",
                    {"pipeline_id": str(pipeline_id), "status": "completed"},
                    key=str(pipeline_id),
                )
            logger.info("pipeline_completed", pipeline_id=str(pipeline_id))

    async def _run_neo4j_sync(self, pipeline_id: uuid.UUID):
        """Sync validated canonical story to Neo4j knowledge graph."""
        logger.info("neo4j_sync_started", pipeline_id=str(pipeline_id))
        
        # Get video_id from pipeline metadata
        pipeline = await self.db.fetchrow(
            "SELECT metadata FROM ai.pipelines WHERE id = $1",
            pipeline_id
        )
        
        if not pipeline:
            logger.error("pipeline_not_found_for_neo4j_sync", pipeline_id=str(pipeline_id))
            await self.handle_step_failed(pipeline_id, "knowledge_graph_sync", "Pipeline not found")
            return
        
        metadata = json.loads(pipeline["metadata"])
        video_id = metadata.get("video_id")
        
        if not video_id:
            logger.error("video_id_not_in_metadata", pipeline_id=str(pipeline_id))
            await self.handle_step_failed(pipeline_id, "knowledge_graph_sync", "Video ID not found")
            return
        
        # Get latest validated canonical story
        story_result = await self.db.fetchrow(
            """
            SELECT id FROM canonical.stories
            WHERE source_video_id = $1 AND is_validated = true
            ORDER BY created_at DESC LIMIT 1
            """,
            video_id,
        )
        
        if not story_result:
            logger.warning("no_validated_canonical_story", pipeline_id=str(pipeline_id), video_id=video_id)
            await self._update_step_status(pipeline_id, "knowledge_graph_sync", StepStatus.SKIPPED)
            await self.handle_step_completed(pipeline_id, "knowledge_graph_sync")
            return
        
        canonical_story_id = story_result["id"]
        
        try:
            # Sync to Neo4j
            sync_stats = await self.neo4j_sync_service.sync_canonical_story(canonical_story_id)
            
            await self._update_step_status(pipeline_id, "knowledge_graph_sync", StepStatus.COMPLETED)
            
            logger.info(
                "neo4j_sync_completed",
                pipeline_id=str(pipeline_id),
                canonical_story_id=canonical_story_id,
                stats=sync_stats,
            )
            
            # Advance to next step (or complete)
            await self.handle_step_completed(pipeline_id, "knowledge_graph_sync")
            
        except Exception as e:
            logger.error(
                "neo4j_sync_failed",
                pipeline_id=str(pipeline_id),
                canonical_story_id=canonical_story_id,
                error=str(e),
                exc_info=True,
            )
            await self.handle_step_failed(pipeline_id, "knowledge_graph_sync", str(e))

    async def _run_quality_gate(self, pipeline_id: uuid.UUID):
        """Run quality gate check on canonical story before article generation."""
        logger.info("quality_gate_check_started", pipeline_id=str(pipeline_id))
        
        # Get video_id from pipeline metadata
        pipeline = await self.db.fetchrow(
            "SELECT metadata FROM ai.pipelines WHERE id = $1",
            pipeline_id
        )
        
        if not pipeline:
            logger.error("pipeline_not_found_for_quality_gate", pipeline_id=str(pipeline_id))
            await self.handle_step_failed(pipeline_id, "quality_gate", "Pipeline not found")
            return
        
        metadata = json.loads(pipeline["metadata"])
        video_id = metadata.get("video_id")
        
        if not video_id:
            logger.error("video_id_not_in_metadata", pipeline_id=str(pipeline_id))
            await self.handle_step_failed(pipeline_id, "quality_gate", "Video ID not found")
            return
        
        # Get latest canonical story validation result
        validation = await self.db.fetchrow(
            """
            SELECT v.quality_score, v.ready_for_graph, v.recommendation, v.issues
            FROM canonical.validation_results v
            JOIN canonical.stories s ON v.story_id = s.id
            WHERE s.source_video_id = $1
            ORDER BY v.validated_at DESC
            LIMIT 1
            """,
            video_id,
        )
        
        if not validation:
            logger.error("validation_not_found", pipeline_id=str(pipeline_id), video_id=video_id)
            await self.handle_step_failed(pipeline_id, "quality_gate", "Validation result not found")
            return
        
        quality_score = validation["quality_score"]
        ready_for_graph = validation["ready_for_graph"]
        recommendation = validation["recommendation"]
        
        logger.info(
            "quality_gate_check",
            pipeline_id=str(pipeline_id),
            video_id=video_id,
            quality_score=quality_score,
            ready_for_graph=ready_for_graph,
            recommendation=recommendation,
        )
        
        # Quality gate logic
        QUALITY_THRESHOLD = 0.7
        
        if quality_score >= QUALITY_THRESHOLD and ready_for_graph:
            # Pass quality gate, proceed to article generation
            await self._update_step_status(pipeline_id, "quality_gate", StepStatus.COMPLETED)
            
            # Trigger article generation
            await self._update_step_status(pipeline_id, "article_generation", StepStatus.RUNNING)
            await self._update_pipeline_status(pipeline_id, current_step="article_generation")
            
            logger.info(
                "quality_gate_passed",
                pipeline_id=str(pipeline_id),
                quality_score=quality_score,
            )
        else:
            # Fail quality gate, mark for manual review
            await self._update_step_status(pipeline_id, "quality_gate", StepStatus.NEEDS_MANUAL_REVIEW)
            await self._update_pipeline_status(pipeline_id, status=PipelineStatus.NEEDS_REVIEW)
            
            # Store quality gate failure for manual review
            await self._store_quality_gate_failure(
                pipeline_id,
                video_id,
                quality_score,
                recommendation,
                validation["issues"],
            )
            
            logger.warning(
                "quality_gate_failed_needs_review",
                pipeline_id=str(pipeline_id),
                quality_score=quality_score,
                threshold=QUALITY_THRESHOLD,
                ready_for_graph=ready_for_graph,
            )

    async def _store_quality_gate_failure(
        self,
        pipeline_id: uuid.UUID,
        video_id: str,
        quality_score: float,
        recommendation: str,
        issues: list,
    ):
        """Store quality gate failure for manual review."""
        await self.db.execute(
            """
            INSERT INTO ai.pipeline_failed_jobs (
                pipeline_run_id, stage_name, error_type, error_message, payload, retry_count
            ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
            pipeline_id,
            "quality_gate",
            "quality_threshold_not_met",
            f"Quality score {quality_score} below threshold, recommendation: {recommendation}",
            {
                "video_id": video_id,
                "quality_score": quality_score,
                "recommendation": recommendation,
                "issues": issues,
            },
            0,  # Don't auto-retry quality gate failures
        )

    async def handle_step_failed(self, pipeline_id: uuid.UUID, step_name: str, error: str):
        """Handle step failure with retry logic up to max_attempts."""
        step = await self._get_step(pipeline_id, step_name)
        if not step:
            logger.error("step_not_found", pipeline_id=str(pipeline_id), step=step_name)
            return

        current_attempts = step["attempt_count"]
        max_attempts = step["max_attempts"]

        if current_attempts < max_attempts:
            await self.db.execute(
                """
                UPDATE ai.pipeline_steps
                SET status = 'pending', attempt_count = attempt_count + 1, error_message = $3
                WHERE pipeline_id = $1 AND step_name = $2
                """,
                pipeline_id, step_name, error,
            )
            logger.info("pipeline_step_retry", pipeline_id=str(pipeline_id), step=step_name,
                         attempt=current_attempts + 1, max=max_attempts)
        else:
            await self._update_step_status(pipeline_id, step_name, StepStatus.FAILED)
            await self._update_pipeline_status(pipeline_id, PipelineStatus.FAILED)
            if self.event_producer:
                await self.event_producer.produce(
                    "pipeline.failed",
                    {
                        "pipeline_id": str(pipeline_id),
                        "status": "failed",
                        "error_message": error,
                        "failed_step": step_name,
                    },
                    key=str(pipeline_id),
                )
            logger.error("pipeline_failed", pipeline_id=str(pipeline_id), step=step_name, error=error)

    async def _update_step_status(self, pipeline_id: uuid.UUID, step_name: str, status: StepStatus):
        await self.db.execute(
            """
            UPDATE ai.pipeline_steps
            SET status = $3, started_at = CASE WHEN $3 = 'running' THEN now() ELSE started_at END,
                completed_at = CASE WHEN $3 IN ('completed','failed') THEN now() ELSE completed_at END
            WHERE pipeline_id = $1 AND step_name = $2
            """,
            pipeline_id, step_name, status.value,
        )

    async def _update_pipeline_status(self, pipeline_id: uuid.UUID, status: Optional[PipelineStatus] = None, current_step: Optional[str] = None):
        sets = []
        values = [pipeline_id]
        idx = 2
        if status:
            sets.append(f"status = ${idx}")
            values.append(status.value)
            idx += 1
            if status == PipelineStatus.COMPLETED:
                sets.append("completed_at = now()")
            elif status == PipelineStatus.RUNNING:
                sets.append("started_at = CASE WHEN started_at IS NULL THEN now() ELSE started_at END")
        if current_step:
            sets.append(f"current_step = ${idx}")
            values.append(current_step)
            idx += 1
        if sets:
            await self.db.execute(
                f"UPDATE ai.pipelines SET {', '.join(sets)} WHERE id = $1",
                *values,
            )

    async def _get_step(self, pipeline_id: uuid.UUID, step_name: str) -> Optional[dict]:
        row = await self.db.fetchrow(
            "SELECT * FROM ai.pipeline_steps WHERE pipeline_id = $1 AND step_name = $2",
            pipeline_id, step_name,
        )
        if row:
            return dict(row)
        return None

    async def _get_video_priority(self, pipeline_id: uuid.UUID) -> Optional[str]:
        """Get video priority from pipeline metadata."""
        try:
            pipeline = await self.db.fetchrow(
                "SELECT metadata FROM ai.pipelines WHERE id = $1",
                pipeline_id
            )
            
            if pipeline:
                metadata = json.loads(pipeline["metadata"])
                video_id = metadata.get("video_id")
                
                if video_id:
                    # Get video priority from database
                    video = await self.db.fetchrow(
                        "SELECT priority FROM source.videos WHERE id = $1",
                        video_id
                    )
                    
                    if video:
                        return video["priority"]
            
            # Default to MEDIUM if not found
            return "MEDIUM"
            
        except Exception as e:
            logger.warning(
                "get_video_priority_failed",
                pipeline_id=str(pipeline_id),
                error=str(e)
            )
            return "MEDIUM"  # Default