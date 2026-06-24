"""Shared Pydantic event schemas for Redpanda/Kafka messages.

All AI platform services use these event definitions to ensure
consistent message formats across the event-driven pipeline.

Topic names follow the standard convention defined in EventTopics.java:
  {domain}.{action}[.{qualifier}]

Reference: docs/ai-platform/queue-contract-specification.md
Reference: packages/shared-events/.../EventTopics.java
"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class SourceSubmitted(BaseModel):
    """New source material submitted for AI pipeline processing.
    Topic: source.submitted
    """
    sourceId: UUID
    sourceType: str  # youtube_channel, youtube_video, podcast_rss, manual_upload
    platformSourceId: str
    title: str
    description: Optional[str] = None
    language: str = "id"
    submittedBy: UUID
    submittedAt: datetime = Field(default_factory=datetime.utcnow)


class SourceMetadataImported(BaseModel):
    """External metadata has been extracted and normalized.
    Topic: source.metadata.imported
    """
    sourceId: UUID
    sourceType: str
    title: str
    description: Optional[str] = None
    durationSeconds: Optional[int] = None
    language: Optional[str] = None
    tags: list[str] = []


class TranscriptImported(BaseModel):
    """Raw transcript text has been imported.
    Topic: transcript.imported
    """
    sourceId: UUID
    transcriptId: UUID
    language: str = "id"
    transcriptType: str = "youtube_caption"
    textLength: int = 0
    hasTimestamps: bool = False
    segmentCount: int = 0


class TranscriptNormalized(BaseModel):
    """Transcript has been cleaned, segmented, and normalized.
    Topic: transcript.normalized
    """
    sourceId: UUID
    transcriptId: UUID
    normalizedVersion: int = 1
    segments: list[dict] = []
    statistics: dict = {}


class CanonicalStoryExtracted(BaseModel):
    """Canonical story has been extracted.
    Topic: story.extracted
    """
    sourceId: UUID
    transcriptId: UUID
    jobId: UUID
    canonicalStoryId: UUID
    storyTitle: str
    storySummary: str
    language: str = "id"
    qualityScore: float = 0.0


class KnowledgeExtracted(BaseModel):
    """Knowledge entities extracted from canonical story.
    Topic: knowledge.extracted
    """
    canonicalStoryId: UUID
    sourceId: UUID
    jobId: UUID
    knowledgeId: UUID
    entityCount: int = 0
    claimCount: int = 0
    themeCount: int = 0
    motifCount: int = 0


class KnowledgeNormalized(BaseModel):
    """Knowledge has been normalized.
    Topic: knowledge.normalized
    """
    knowledgeId: UUID
    canonicalStoryId: UUID
    sourceId: UUID
    jobId: UUID
    aliasesResolved: int = 0
    duplicatesMerged: int = 0


class KnowledgeValidated(BaseModel):
    """Knowledge has passed or failed validation.
    Topic: knowledge.validated
    """
    knowledgeId: UUID
    canonicalStoryId: UUID
    sourceId: UUID
    jobId: UUID
    overallScore: float = 0.0
    passed: bool = False


class ArticleGenerated(BaseModel):
    """Article draft has been generated.
    Topic: article.generated
    """
    canonicalStoryId: UUID
    knowledgeId: UUID
    sourceId: UUID
    jobId: UUID
    articleDraftId: UUID
    articleType: str  # narrative, knowledge, news, creative
    title: str
    wordCount: int = 0
    qualityScore: float = 0.0


class EmbeddingGenerated(BaseModel):
    """Embeddings have been generated.
    Topic: embedding.generated
    """
    jobId: UUID
    targetType: str  # story, article, entity, theme, claim, motif
    targetId: UUID
    embeddingId: UUID
    dimension: int = 1536
    model: str = "text-embedding-3-large"


class GraphProjected(BaseModel):
    """Knowledge graph projection has been updated.
    Topic: graph.projected
    """
    projectionId: UUID
    canonicalStoryId: UUID
    knowledgeId: UUID
    jobId: UUID
    nodesCreated: int = 0
    relationshipsCreated: int = 0


class ReviewRequested(BaseModel):
    """Content submitted for human review.
    Topic: review.requested
    """
    reviewId: UUID
    targetType: str  # story, article
    targetId: UUID
    workflowType: str = "editorial_review"


class ReviewApproved(BaseModel):
    """Content approved by reviewer.
    Topic: review.approved
    """
    reviewId: UUID
    targetType: str
    targetId: UUID
    approvedBy: UUID


class ReviewRejected(BaseModel):
    """Content rejected by reviewer.
    Topic: review.rejected
    """
    reviewId: UUID
    targetType: str
    targetId: UUID
    rejectedBy: UUID
    rejectionReason: str


class VideoIngested(BaseModel):
    """Video has been ingested by the ingestion service.
    Topic: ai.video.ingested
    """
    video_id: UUID
    channel_id: UUID
    platform_video_id: str
    title: str
    duration_seconds: int = 0
    language_code: str = "id"
    has_subtitles: bool = False
    subtitle_track_id: Optional[UUID] = None
    payload_hash: str = ""
    ingestion_job_id: UUID
    metadata: dict = {}


class TranscriptGenerated(BaseModel):
    """Transcript has been generated from source.
    Topic: ai.transcript.generated.v1
    """
    event_version: str = "2"
    video_id: UUID
    transcript_id: UUID
    extraction_run_id: UUID
    source_type: str = "youtube_subtitle"
    language_detected: str = "id"
    duration_seconds: int = 0
    word_count: int = 0
    avg_confidence: float = 0.0
    has_low_confidence_segments: bool = False
    cost_usd: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeExtractedEvent(BaseModel):
    """Knowledge has been extracted from transcript.
    Topic: ai.knowledge.extracted.v1
    """
    event_version: str = "1"
    video_id: UUID
    transcript_id: UUID
    enrichment_run_id: UUID
    entity_count: int = 0
    claim_count: int = 0
    theme_count: int = 0
    motif_count: int = 0
    story_count: int = 0
    model_used: str = ""
    cost_usd: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineFailed(BaseModel):
    """Emitted by orchestration-service when a pipeline step fails."""
    event_version: str = "1"
    pipeline_id: UUID
    error_message: str
    failed_step: str
    retry_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Event registry: maps topic name (standard convention) to Pydantic model
EVENT_REGISTRY: dict[str, type[BaseModel]] = {
    "source.submitted": SourceSubmitted,
    "source.metadata.imported": SourceMetadataImported,
    "transcript.imported": TranscriptImported,
    "transcript.normalized": TranscriptNormalized,
    "story.extracted": CanonicalStoryExtracted,
    "knowledge.extracted": KnowledgeExtracted,
    "knowledge.normalized": KnowledgeNormalized,
    "knowledge.validated": KnowledgeValidated,
    "article.generated": ArticleGenerated,
    "embedding.generated": EmbeddingGenerated,
    "graph.projected": GraphProjected,
    "review.requested": ReviewRequested,
    "review.approved": ReviewApproved,
    "review.rejected": ReviewRejected,
    "pipeline.failed": PipelineFailed,
}