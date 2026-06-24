"""Video Processing State Machine.

Manages state transitions for video processing pipeline with validation,
error recovery, and retry logic.
"""

import uuid
import structlog
from enum import Enum
from typing import Optional, Dict, Set
from datetime import datetime

from ai_shared.database import Database

logger = structlog.get_logger(__name__)


class VideoProcessingState(str, Enum):
    """States in video processing pipeline."""
    # Initial states
    SUBMITTED = "SUBMITTED"
    QUEUED = "QUEUED"
    
    # Metadata stage
    METADATA_EXTRACTING = "METADATA_EXTRACTING"
    METADATA_EXTRACTED = "METADATA_EXTRACTED"
    
    # Transcript stage
    TRANSCRIPT_EXTRACTING = "TRANSCRIPT_EXTRACTING"
    TRANSCRIPT_READY = "TRANSCRIPT_READY"
    
    # Canonicalization stage
    CANONICALIZING = "CANONICALIZING"
    CANONICALIZED = "CANONICALIZED"
    
    # Knowledge extraction stage
    KNOWLEDGE_EXTRACTING = "KNOWLEDGE_EXTRACTING"
    KNOWLEDGE_READY = "KNOWLEDGE_READY"
    
    # Graph sync stage
    GRAPH_SYNCING = "GRAPH_SYNCING"
    GRAPH_READY = "GRAPH_READY"
    
    # Article generation stage
    ARTICLES_GENERATING = "ARTICLES_GENERATING"
    ARTICLES_GENERATED = "ARTICLES_GENERATED"
    
    # Final states
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    
    # Error states
    FAILED_METADATA = "FAILED_METADATA"
    FAILED_TRANSCRIPT = "FAILED_TRANSCRIPT"
    FAILED_LLM = "FAILED_LLM"
    FAILED_ARTICLE = "FAILED_ARTICLE"
    FAILED_GRAPH = "FAILED_GRAPH"
    FAILED_REVIEW = "FAILED_REVIEW"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class StateMachine:
    """State machine for video processing pipeline.
    
    Validates state transitions and enforces business logic.
    Handles error recovery with retry limits.
    """

    def __init__(self, db: Database):
        self.db = db
        self.state_transitions = self._build_transitions()
        self.max_retries = 3

    def _build_transitions(self) -> Dict[VideoProcessingState, Set[VideoProcessingState]]:
        """Define valid state transitions."""
        return {
            VideoProcessingState.SUBMITTED: {VideoProcessingState.QUEUED},
            VideoProcessingState.QUEUED: {
                VideoProcessingState.METADATA_EXTRACTING,
                VideoProcessingState.FAILED_METADATA,
            },
            VideoProcessingState.METADATA_EXTRACTING: {
                VideoProcessingState.METADATA_EXTRACTED,
                VideoProcessingState.FAILED_METADATA,
            },
            VideoProcessingState.METADATA_EXTRACTED: {
                VideoProcessingState.TRANSCRIPT_EXTRACTING,
                VideoProcessingState.COMPLETED,  # For LOW priority
            },
            VideoProcessingState.TRANSCRIPT_EXTRACTING: {
                VideoProcessingState.TRANSCRIPT_READY,
                VideoProcessingState.FAILED_TRANSCRIPT,
                VideoProcessingState.MANUAL_REVIEW_REQUIRED,
            },
            VideoProcessingState.TRANSCRIPT_READY: {
                VideoProcessingState.CANONICALIZING,
            },
            VideoProcessingState.CANONICALIZING: {
                VideoProcessingState.CANONICALIZED,
                VideoProcessingState.FAILED_LLM,
            },
            VideoProcessingState.CANONICALIZED: {
                VideoProcessingState.KNOWLEDGE_EXTRACTING,
            },
            VideoProcessingState.KNOWLEDGE_EXTRACTING: {
                VideoProcessingState.KNOWLEDGE_READY,
                VideoProcessingState.FAILED_LLM,
            },
            VideoProcessingState.KNOWLEDGE_READY: {
                VideoProcessingState.GRAPH_SYNCING,
            },
            VideoProcessingState.GRAPH_SYNCING: {
                VideoProcessingState.GRAPH_READY,
                VideoProcessingState.FAILED_GRAPH,
            },
            VideoProcessingState.GRAPH_READY: {
                VideoProcessingState.ARTICLES_GENERATING,
                VideoProcessingState.COMPLETED,  # For MEDIUM priority
            },
            VideoProcessingState.ARTICLES_GENERATING: {
                VideoProcessingState.ARTICLES_GENERATED,
                VideoProcessingState.FAILED_ARTICLE,
            },
            VideoProcessingState.ARTICLES_GENERATED: {
                VideoProcessingState.PUBLISHED,
            },
            VideoProcessingState.PUBLISHED: {
                VideoProcessingState.COMPLETED,
            },
            
            # Error recovery (can retry from FAILED_ states)
            VideoProcessingState.FAILED_METADATA: {VideoProcessingState.QUEUED},
            VideoProcessingState.FAILED_TRANSCRIPT: {VideoProcessingState.QUEUED},
            VideoProcessingState.FAILED_LLM: {VideoProcessingState.QUEUED},
            VideoProcessingState.FAILED_ARTICLE: {VideoProcessingState.QUEUED},
            VideoProcessingState.FAILED_GRAPH: {VideoProcessingState.QUEUED},
            VideoProcessingState.FAILED_REVIEW: {VideoProcessingState.QUEUED},
            
            # Manual review can be set from any state
            VideoProcessingState.MANUAL_REVIEW_REQUIRED: set(),
        }

    async def transition(
        self,
        video_id: str,
        new_state: VideoProcessingState,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Transition video to new state with validation.
        
        Args:
            video_id: UUID of the video
            new_state: Target state
            error_message: Error message if transitioning to error state
            
        Returns:
            True if transition successful
            
        Raises:
            InvalidStateTransition: If transition is not valid
            MaxRetriesExceeded: If retry limit exceeded
        """
        current_state = await self._get_current_state(video_id)
        
        # Validate transition
        if new_state not in self._get_valid_transitions(current_state):
            logger.error(
                "invalid_state_transition",
                video_id=video_id,
                current_state=current_state.value if current_state else None,
                new_state=new_state.value,
            )
            raise InvalidStateTransition(
                f"Cannot transition from {current_state} to {new_state}"
            )
        
        # Check retry limit for error states
        if new_state.value.startswith("FAILED_"):
            retry_count = await self._get_retry_count(video_id)
            if retry_count >= self.max_retries:
                logger.error(
                    "max_retries_exceeded",
                    video_id=video_id,
                    retry_count=retry_count,
                    max_retries=self.max_retries,
                )
                raise MaxRetriesExceeded(
                    f"Max retries ({self.max_retries}) exceeded for video {video_id}"
                )
        
        # Update state in database
        await self._update_state(video_id, new_state, error_message)
        
        logger.info(
            "state_transition_completed",
            video_id=video_id,
            old_state=current_state.value if current_state else None,
            new_state=new_state.value,
            error_message=error_message,
        )
        
        return True

    async def _get_current_state(
        self,
        video_id: str,
    ) -> Optional[VideoProcessingState]:
        """Get current processing state for video."""
        result = await self.db.fetchrow(
            "SELECT processing_state FROM source.videos WHERE id = $1",
            video_id,
        )
        
        if result and result["processing_state"]:
            return VideoProcessingState(result["processing_state"])
        
        return VideoProcessingState.SUBMITTED  # Default

    def _get_valid_transitions(
        self,
        current_state: Optional[VideoProcessingState],
    ) -> Set[VideoProcessingState]:
        """Get valid transitions for current state."""
        if current_state is None:
            return {VideoProcessingState.QUEUED}
        
        return self.state_transitions.get(current_state, set())

    async def _get_retry_count(self, video_id: str) -> int:
        """Get current retry count for video."""
        result = await self.db.fetchrow(
            "SELECT retry_count, max_retries FROM source.videos WHERE id = $1",
            video_id,
        )
        
        if result:
            return result.get("retry_count", 0)
        
        return 0

    async def _update_state(
        self,
        video_id: str,
        new_state: VideoProcessingState,
        error_message: Optional[str] = None,
    ):
        """Update processing state in database."""
        await self.db.execute("""
            UPDATE source.videos
            SET processing_state = $2,
                processing_started_at = COALESCE(
                    processing_started_at,
                    CASE WHEN $2 != 'SUBMITTED' AND $2 != 'QUEUED' THEN now() ELSE processing_started_at END
                ),
                processing_completed_at = CASE WHEN $2 = 'COMPLETED' THEN now() 
                                              WHEN $2 = 'PUBLISHED' THEN now()
                                              ELSE processing_completed_at END,
                error_message = $3,
                retry_count = CASE WHEN $2 LIKE 'FAILED_%' THEN retry_count + 1 ELSE retry_count END,
                updated_at = now()
            WHERE id = $1
        """, video_id, new_state.value, error_message)

    async def get_videos_ready_for_processing(
        self,
        state: VideoProcessingState = VideoProcessingState.QUEUED,
        limit: int = 10,
    ) -> list[dict]:
        """
        Get videos ready for next processing step.
        
        Prioritizes HIGH priority videos, then MEDIUM, then LOW.
        
        Args:
            state: Current state to query
            limit: Maximum number of videos to return
            
        Returns:
            List of video dictionaries with id, url, and priority
        """
        videos = await self.db.fetch("""
            SELECT v.id, v.url, v.priority, v.processing_state, 
                   v.retry_count, v.channel_id, c.name as channel_name
            FROM source.videos v
            LEFT JOIN source.channels c ON v.channel_id = c.id
            WHERE v.processing_state = $1
            ORDER BY 
                CASE v.priority
                    WHEN 'HIGH' THEN 1
                    WHEN 'MEDIUM' THEN 2
                    WHEN 'LOW' THEN 3
                    WHEN 'SKIP' THEN 4
                    ELSE 5
                END,
                v.created_at ASC,
                v.retry_count ASC
            LIMIT $2
        """, state.value, limit)
        
        return [dict(video) for video in videos] if videos else []

    async def get_stale_videos(
        self,
        stale_threshold_minutes: int = 60,
    ) -> list[dict]:
        """
        Get videos that have been stuck in a non-terminal state for too long.
        
        Args:
            stale_threshold_minutes: Minutes after which a state is considered stale
            
        Returns:
            List of videos that need attention
        """
        non_terminal_states = [
            VideoProcessingState.METADATA_EXTRACTING,
            VideoProcessingState.TRANSCRIPT_EXTRACTING,
            VideoProcessingState.CANONICALIZING,
            VideoProcessingState.KNOWLEDGE_EXTRACTING,
            VideoProcessingState.GRAPH_SYNCING,
            VideoProcessingState.ARTICLES_GENERATING,
        ]
        
        state_values = [s.value for s in non_terminal_states]
        
        videos = await self.db.fetch(f"""
            SELECT v.id, v.processing_state, v.processing_started_at, v.url
            FROM source.videos v
            WHERE v.processing_state = ANY($1::varchar[])
              AND v.processing_started_at < now() - INTERVAL '{stale_threshold_minutes} minutes'
            ORDER BY v.processing_started_at ASC
        """, state_values)
        
        return [dict(video) for video in videos] if videos else []

    async def reset_stale_video(self, video_id: str):
        """Reset a stale video to QUEUED state for reprocessing."""
        current_state = await self._get_current_state(video_id)
        
        # Reset retry count when resetting stale video
        await self.db.execute("""
            UPDATE source.videos
            SET processing_state = 'QUEUED',
                retry_count = 0,
                error_message = 'Reset after stale detection',
                updated_at = now()
            WHERE id = $1
        """, video_id)
        
        logger.info(
            "stale_video_reset",
            video_id=video_id,
            previous_state=current_state.value if current_state else None,
        )


class InvalidStateTransition(Exception):
    """Raised when attempting invalid state transition."""
    pass


class MaxRetriesExceeded(Exception):
    """Raised when maximum retry attempts exceeded."""
    pass