# AI Platform Domain Event Catalog

## The Living Atlas of Indonesian Mystery Culture

**Version:** 1.0  
**Status:** Draft  
**Owner:** AI Platform Team  

---

# Table of Contents

1. [Event Architecture Principles](#1-event-architecture-principles)
2. [Event Naming Convention](#2-event-naming-convention)
3. [Event Categories](#3-event-categories)
4. [Event Specification Template](#4-event-specification-template)
5. [Complete Event Catalog](#5-complete-event-catalog)
6. [Payload Contracts](#6-payload-contracts)
7. [Event Versioning Strategy](#7-event-versioning-strategy)
8. [Dead Letter Handling](#8-dead-letter-handling)
9. [Observability](#9-observability)

---

# 1. Event Architecture Principles

## 1.1 Event Driven Architecture

The AI Platform operates exclusively through event-driven processing. All operations are initiated by queue messages received from Redpanda topics. No REST API is exposed. No synchronous RPC is permitted.

**Rules:**
- Every stage of processing produces at least one event.
- Events are the sole integration contract between services.
- No service may call another service directly.
- The platform must be stateless, horizontally scalable, and retryable.

## 1.2 Transactional Outbox

Backend services (Spring Boot) publish bridge events to the AI Platform via the transactional outbox pattern.

**Flow:**
```
Service → Outbox Table (PG) → Outbox Publisher → Redpanda Topic → AI Worker
```

**Guarantees:**
- At-least-once delivery.
- Exactly-once processing (via idempotency).
- No message loss during service failures.
- Ordering preserved per aggregate ID within a topic partition.

**Outbox table** (per service):
```sql
CREATE TABLE system.outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(255) NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ
);
```

## 1.3 Idempotency

Every event handler must support re-execution. Repeated execution of the same event must produce identical results.

**Mechanisms:**
- **Deduplication by eventId:** Each consumer maintains a deduplication store (PostgreSQL dedup table or Redis) keyed by `eventId`. Events with an already-processed `eventId` are silently dropped.
- **Idempotent writes:** Database writes use `INSERT ... ON CONFLICT DO NOTHING` or upsert patterns keyed by `aggregateId` + `eventType`.
- **Deterministic processing:** AI providers must be called with identical prompts and parameters for identical inputs.

**Deduplication table:**
```sql
CREATE TABLE ai_platform.processed_events (
    event_id UUID PRIMARY KEY,
    consumer VARCHAR(255) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT now() + interval '30 days'
);
```

## 1.4 Event Versioning

Every event carries a version number in its envelope. Schema evolution follows semantic versioning.

- **Major version increment:** Breaking schema changes (field removal, type changes, required field additions).
- **Minor version increment:** Backward-compatible additions (new optional fields, field ordering changes).
- **Patch version increment:** Documentation, clarifications, non-structural changes.

Producers MUST NOT remove fields in minor versions. Consumers MUST tolerate unknown fields.

## 1.5 Event Ownership

| Service | Owned Events |
|---------|-------------|
| content-service (Backend) | SourceSubmitted, SourceMetadataImported |
| ingestion-service (AI) | TranscriptImported, TranscriptNormalized |
| orchestration-service (AI) | CanonicalStoryExtractionRequested, KnowledgeExtractionRequested, KnowledgeNormalizationRequested, KnowledgeValidationRequested, ArticleGenerationRequested, EmbeddingGenerationRequested, GraphProjectionRequested |
| extraction-service (AI) | CanonicalStoryExtracted, KnowledgeExtracted |
| normalization-service (AI) | KnowledgeNormalized |
| validation-service (AI) | KnowledgeValidated |
| article-service (AI) | ArticleGenerated |
| embedding-service (AI) | EmbeddingGenerated |
| workflow-service (Backend) | ReviewRequested, ReviewApproved, ReviewRejected, PublicationRequested, PublicationCompleted |
| data-platform (Backend) | GraphProjected |

---

# 2. Event Naming Convention

## 2.1 Format

Events use **PascalCase** with the following conventions:

```
{Aggregate}{PastTenseVerb}
{Context}{PastTenseVerb}
{Action}Requested
```

## 2.2 Patterns

| Pattern | Use Case | Example |
|---------|----------|---------|
| `{Noun}{PastTenseVerb}` | Factual completion | SourceSubmitted, TranscriptImported |
| `{Noun}{PastParticiple}` | State transformation | TranscriptNormalized, KnowledgeValidated |
| `{Action}Requested` | Workflow trigger | CanonicalStoryExtractionRequested |
| `{Noun}Generated` | Created artifact | ArticleGenerated, EmbeddingGenerated |
| `Review{PastTenseVerb}` | Human review cycle | ReviewApproved, ReviewRejected |
| `Publication{PastTenseVerb}` | Publication cycle | PublicationRequested, PublicationCompleted |
| `Graph{PastParticiple}` | Projection ready | GraphProjected |

## 2.3 Topic Naming Convention

Redpanda topics use **dot-separated lowercase** with the following scheme:

```
source.submitted
source.metadata.imported
transcript.imported
transcript.normalized
story.extraction.requested
story.extracted
knowledge.extraction.requested
knowledge.extracted
knowledge.normalization.requested
knowledge.normalized
knowledge.validation.requested
knowledge.validated
article.generation.requested
article.generated
embedding.generation.requested
embedding.generated
graph.projection.requested
graph.projected
review.requested
review.approved
review.rejected
publication.requested
publication.completed
```

## 2.4 Event Envelope

Every event uses the standard envelope defined in ADR-004 and implemented via `AiBridgeEvent`:

```json
{
  "eventId": "uuid",
  "eventType": "SourceSubmitted",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T01:00:00Z",
  "producer": "content-service",
  "aggregateId": "uuid",
  "data": {},
  "metadata": {
    "tenantId": "uuid",
    "correlationId": "uuid",
    "causationId": "uuid",
    "jobId": "uuid"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| eventId | UUID | Unique identifier for this event occurrence |
| eventType | String | PascalCase event name |
| eventVersion | Integer | Schema version for this event type |
| occurredAt | ISO8601 | Timestamp when the event was produced |
| producer | String | Name of the service that produced the event |
| aggregateId | UUID | Identifier of the domain aggregate this event relates to |
| data | JSON Object | Event-specific payload (see section 5 for schemas) |
| metadata.tenantId | UUID | Multi-tenant scope identifier |
| metadata.correlationId | UUID | Tracks across the entire processing flow |
| metadata.causationId | UUID | Identifies the immediate cause (previous event) |
| metadata.jobId | UUID | Tracks a specific pipeline job execution |

---

# 3. Event Categories

## 3.1 Source Events

Events related to acquisition and registration of source materials.

| Event | Description |
|-------|-------------|
| SourceSubmitted | New source material submitted (YouTube, podcast, manual upload) |
| SourceMetadataImported | External metadata has been extracted and normalized |

## 3.2 Transcript Events

Events related to transcript acquisition and processing.

| Event | Description |
|-------|-------------|
| TranscriptImported | Raw transcript text has been imported |
| TranscriptNormalized | Transcript has been cleaned, segmented, and normalized |

## 3.3 Story Events

Events related to canonical story extraction.

| Event | Description |
|-------|-------------|
| CanonicalStoryExtractionRequested | Request to extract a canonical story from transcript |
| CanonicalStoryExtracted | Canonical story has been extracted |

## 3.4 Knowledge Events

Events related to knowledge extraction, normalization, and validation.

| Event | Description |
|-------|-------------|
| KnowledgeExtractionRequested | Request to extract structured knowledge from story |
| KnowledgeExtracted | Knowledge entities, claims, themes, motifs extracted |
| KnowledgeNormalizationRequested | Request to normalize and resolve ambiguities |
| KnowledgeNormalized | Knowledge normalized; aliases resolved, duplicates merged |
| KnowledgeValidationRequested | Request to validate knowledge quality |
| KnowledgeValidated | Knowledge passed or failed validation |

## 3.5 Article Events

Events related to article generation.

| Event | Description |
|-------|-------------|
| ArticleGenerationRequested | Request to generate an article from validated knowledge |
| ArticleGenerated | Article draft has been generated |

## 3.6 Embedding Events

Events related to vector embedding generation.

| Event | Description |
|-------|-------------|
| EmbeddingGenerationRequested | Request to generate embeddings for knowledge artifacts |
| EmbeddingGenerated | Embeddings have been generated and stored |

## 3.7 Projection Events

Events related to downstream data projections.

| Event | Description |
|-------|-------------|
| GraphProjectionRequested | Request to update the knowledge graph projection |
| GraphProjected | Knowledge graph projection has been updated |

## 3.8 Workflow Events

Events related to human review and publication workflows.

| Event | Description |
|-------|-------------|
| ReviewRequested | Content submitted for human review |
| ReviewApproved | Content approved by reviewer |
| ReviewRejected | Content rejected by reviewer |
| PublicationRequested | Request to publish approved content |
| PublicationCompleted | Content has been published |

## 3.9 System Events

Events related to pipeline lifecycle and infrastructure.

| Event | Description |
|-------|-------------|
| PipelineFailed | Pipeline step failed irrecoverably |
| PipelineCancelled | Pipeline cancelled by operator |
| PipelineCompleted | Entire pipeline finished successfully |

---

# 4. Event Specification Template

Every event specification in this catalog follows the template below:

```
## Event Name

### Purpose
Why this event exists and what it represents.

### Topic
The Redpanda topic name.

### Producer
The service that emits this event.

### Consumers
The services that consume this event.

### Trigger
What action or condition causes this event to be emitted.

### Payload Schema
Required and optional fields in the `data` payload.

### Idempotency Rules
How consumers ensure idempotent processing.

### Retry Rules
Retry strategy for consumer failures.

### Ordering Rules
Partition key and ordering guarantees.
```

---

# 5. Complete Event Catalog

---

## 5.1 SourceSubmitted

### Purpose
Indicates that a new source material has been submitted for processing by the AI platform. This is the entry point for the entire AI pipeline.

### Topic
`source.submitted`

### Producer
`content-service` (Spring Boot)

### Consumers
`orchestration-service` (Python worker)

### Trigger
A user uploads a video, adds a YouTube channel, or submits a podcast feed via the Backend API.

### Payload Schema
```json
{
  "sourceId": "uuid",
  "sourceType": "youtube_channel | youtube_video | podcast_rss | manual_upload",
  "externalUrl": "string (optional)",
  "platformSourceId": "string (e.g., YouTube video ID or channel ID)",
  "channelId": "uuid (optional)",
  "title": "string",
  "description": "string (optional)",
  "language": "id | en",
  "submittedBy": "uuid (user ID)",
  "submittedAt": "ISO8601"
}
```

### Idempotency Rules
- Consumer MUST deduplicate by `eventId`.
- If the same `sourceId` has already been processed, the event MUST be silently skipped.

### Retry Rules
- Retry on: network timeout, temporary outage, consumer crash.
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum retries: 5.
- After 5 retries: send to Dead Letter Queue.

### Ordering Rules
- Partition key: `sourceId`.
- Events for the same source MUST be processed in order.
- Different sources can be processed in parallel.

---

## 5.2 SourceMetadataImported

### Purpose
Indicates that external metadata for a source (title, description, thumbnails, duration, etc.) has been successfully imported and normalized.

### Topic
`source.metadata.imported`

### Producer
`ingestion-service` (Python worker)

### Consumers
`content-service` (Spring Boot), `orchestration-service` (Python worker)

### Trigger
Ingestion service has completed metadata retrieval from YouTube API, RSS feed, or manual upload extraction.

### Payload Schema
```json
{
  "sourceId": "uuid",
  "sourceType": "youtube_channel | youtube_video | podcast_rss | manual_upload",
  "title": "string",
  "description": "string",
  "thumbnailUrl": "string (optional)",
  "durationSeconds": "integer (optional)",
  "publishedAt": "ISO8601 (optional)",
  "tags": ["string"] (optional),
  "language": "string (optional)",
  "metadata": {
    "viewCount": "integer (optional)",
    "likeCount": "integer (optional)",
    "channelTitle": "string (optional)"
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If metadata was already stored for this `sourceId`, the event is a no-op.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.
- Dead letter on final failure.

### Ordering Rules
- Partition key: `sourceId`.
- Guaranteed ordering per source.

---

## 5.3 TranscriptImported

### Purpose
Indicates that a transcript has been successfully retrieved (from subtitles, ASR, or manual upload) and is ready for processing.

### Topic
`transcript.imported`

### Producer
`ingestion-service` (Python worker)

### Consumers
`orchestration-service` (Python worker), `content-service` (Spring Boot)

### Trigger
Ingestion service has fetched or generated the transcript text for a source.

### Payload Schema
```json
{
  "sourceId": "uuid",
  "transcriptId": "uuid",
  "language": "id | en | other",
  "transcriptType": "manual | youtube_caption | asr_generated | podcast_rss",
  "textLength": "integer (character count)",
  "hasTimestamps": false,
  "segmentCount": "integer (optional, 0 if no timestamps)",
  "storageUrl": "string (object storage path or inline)"
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If `transcriptId` already processed, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 5 retries.
- Dead letter on final failure.

### Ordering Rules
- Partition key: `sourceId`.
- Ordered per source.

---

## 5.4 TranscriptNormalized

### Purpose
Indicates that the raw transcript has been cleaned, segmented, and normalized for AI extraction.

### Topic
`transcript.normalized`

### Producer
`ingestion-service` (Python worker)

### Consumers
`orchestration-service` (Python worker)

### Trigger
Transcript normalization (text cleaning, speaker diarization, segment structuring) has completed.

### Payload Schema
```json
{
  "sourceId": "uuid",
  "transcriptId": "uuid",
  "normalizedVersion": "integer",
  "segments": [
    {
      "segmentIndex": 0,
      "startTime": 0.0,
      "endTime": 12.5,
      "speaker": "string (optional)",
      "text": "string",
      "confidence": 0.95
    }
  ],
  "statistics": {
    "totalDurationSeconds": 3847,
    "segmentCount": 42,
    "speakerCount": 3,
    "averageConfidence": 0.94
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If the transcript version has already been normalized, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `transcriptId`.
- Ordered per transcript.

---

## 5.5 CanonicalStoryExtractionRequested

### Purpose
Requests the extraction service to extract a canonical story from the normalized transcript.

### Topic
`story.extraction.requested`

### Producer
`orchestration-service` (Python worker)

### Consumers
`extraction-service` (Python worker)

### Trigger
Orchestration service determines transcript is ready for story extraction.

### Payload Schema
```json
{
  "sourceId": "uuid",
  "transcriptId": "uuid",
  "jobId": "uuid",
  "extractionConfig": {
    "model": "gemini-2.5-pro | claude-sonnet-4 | gpt-4o",
    "promptVersion": "story-extraction-v3",
    "temperature": 0.3,
    "maxTokens": 8192
  },
  "transcript": {
    "segments": [
      {
        "segmentIndex": 0,
        "startTime": 0.0,
        "endTime": 12.5,
        "speaker": "string (optional)",
        "text": "string"
      }
    ],
    "language": "id"
  },
  "metadata": {
    "title": "string",
    "description": "string (optional)",
    "publishedAt": "ISO8601 (optional)"
  }
}
```

### Idempotency Rules
- Consumer MUST check if extraction job `jobId` has already been processed.
- If completed, event is silently dropped.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 5 retries.
- Dead letter on final failure.

### Ordering Rules
- Partition key: `jobId`.
- No strict ordering requirements; can be processed in parallel.

---

## 5.6 CanonicalStoryExtracted

### Purpose
Indicates that a canonical story has been successfully extracted from the transcript.

### Topic
`story.extracted`

### Producer
`extraction-service` (Python worker)

### Consumers
`orchestration-service` (Python worker), `content-service` (Spring Boot)

### Trigger
Extraction service completes story extraction successfully.

### Payload Schema
```json
{
  "sourceId": "uuid",
  "transcriptId": "uuid",
  "jobId": "uuid",
  "canonicalStoryId": "uuid",
  "storyTitle": "string",
  "storySummary": "string",
  "language": "id",
  "qualityScore": 0.88,
  "extractionMetadata": {
    "modelUsed": "gemini-2.5-pro",
    "promptVersion": "story-extraction-v3",
    "inputTokens": 4502,
    "outputTokens": 1280,
    "executionCost": 0.0032,
    "executionTimeMs": 12450
  },
  "extractedArtifacts": {
    "hasThemes": true,
    "hasEntities": true,
    "hasClaims": true,
    "hasMotifs": true,
    "hasBeliefs": true,
    "hasRituals": true
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If `canonicalStoryId` already persisted, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `canonicalStoryId`.
- Ordered per story.

---

## 5.7 KnowledgeExtractionRequested

### Purpose
Requests the extraction service to extract structured knowledge entities from a canonical story.

### Topic
`knowledge.extraction.requested`

### Producer
`orchestration-service` (Python worker)

### Consumers
`extraction-service` (Python worker)

### Trigger
Orchestration service receives `CanonicalStoryExtracted` and determines knowledge extraction is needed.

### Payload Schema
```json
{
  "canonicalStoryId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "extractionConfig": {
    "model": "gemini-2.5-pro | claude-sonnet-4 | gpt-4o",
    "promptVersion": "knowledge-extraction-v2",
    "temperature": 0.2,
    "maxTokens": 8192
  },
  "story": {
    "title": "string",
    "summary": "string",
    "fullText": "string"
  },
  "extractionTypes": [
    "themes",
    "entities",
    "claims",
    "motifs",
    "rituals",
    "beliefs",
    "contradictions"
  ]
}
```

### Idempotency Rules
- Consumer MUST check if `jobId` already processed.
- If completed, event is silently dropped.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `jobId`.

---

## 5.8 KnowledgeExtracted

### Purpose
Indicates that structured knowledge (themes, entities, claims, motifs, etc.) has been successfully extracted from a canonical story.

### Topic
`knowledge.extracted`

### Producer
`extraction-service` (Python worker)

### Consumers
`orchestration-service` (Python worker), `knowledge-service` (Spring Boot)

### Trigger
Extraction service completes knowledge extraction successfully.

### Payload Schema
```json
{
  "canonicalStoryId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "knowledgeId": "uuid",
  "extractionMetadata": {
    "modelUsed": "gemini-2.5-pro",
    "promptVersion": "knowledge-extraction-v2",
    "inputTokens": 8200,
    "outputTokens": 3500,
    "executionCost": 0.0085,
    "executionTimeMs": 22300
  },
  "knowledge": {
    "themes": [
      {
        "themeId": "uuid",
        "name": "string",
        "confidence": 0.92
      }
    ],
    "entities": [
      {
        "entityId": "uuid",
        "name": "string",
        "entityType": "spirit | location | person | creature | object",
        "confidence": 0.95
      }
    ],
    "claims": [
      {
        "claimId": "uuid",
        "statement": "string",
        "confidence": 0.85,
        "evidence": [
          {
            "segmentIndex": 5,
            "text": "string",
            "startTime": 10.5,
            "endTime": 15.2
          }
        ]
      }
    ],
    "motifs": [
      {
        "motifId": "uuid",
        "name": "string",
        "category": "string",
        "confidence": 0.78
      }
    ],
    "rituals": [],
    "beliefs": [],
    "contradictions": []
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If `knowledgeId` already persisted, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `knowledgeId`.

---

## 5.9 KnowledgeNormalizationRequested

### Purpose
Requests the normalization service to resolve ambiguities and normalize the extracted knowledge.

### Topic
`knowledge.normalization.requested`

### Producer
`orchestration-service` (Python worker)

### Consumers
`normalization-service` (Python worker)

### Trigger
Orchestration service receives `KnowledgeExtracted` and determines normalization is needed.

### Payload Schema
```json
{
  "knowledgeId": "uuid",
  "canonicalStoryId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "normalizationConfig": {
    "model": "claude-sonnet-4 | gemini-2.5-pro | gpt-4o",
    "promptVersion": "knowledge-normalization-v1",
    "temperature": 0.1,
    "maxTokens": 4096
  },
  "knowledge": {
    "themes": [],
    "entities": [],
    "claims": [],
    "motifs": [],
    "rituals": [],
    "beliefs": []
  }
}
```

### Idempotency Rules
- Consumer MUST check if `jobId` already processed.
- If completed, event is silently dropped.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `jobId`.

---

## 5.10 KnowledgeNormalized

### Purpose
Indicates that knowledge has been normalized — aliases resolved, duplicates merged, entities disambiguated.

### Topic
`knowledge.normalized`

### Producer
`normalization-service` (Python worker)

### Consumers
`orchestration-service` (Python worker), `knowledge-service` (Spring Boot)

### Trigger
Normalization service completes knowledge normalization successfully.

### Payload Schema
```json
{
  "knowledgeId": "uuid",
  "canonicalStoryId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "normalizationMetadata": {
    "modelUsed": "claude-sonnet-4",
    "promptVersion": "knowledge-normalization-v1",
    "inputTokens": 3200,
    "outputTokens": 1100,
    "executionCost": 0.0028,
    "executionTimeMs": 8900,
    "aliasesResolved": 3,
    "duplicatesMerged": 2
  },
  "normalizedKnowledge": {
    "themes": [],
    "entities": [],
    "claims": [],
    "motifs": [],
    "rituals": [],
    "beliefs": [],
    "contradictions": [],
    "normalizationReport": {
      "entityAliases": {
        "Kuntilanak": ["Pontianak", "Kunti"]
      },
      "mergedEntities": [
        {
          "targetId": "uuid",
          "sourceIds": ["uuid", "uuid"],
          "mergeReason": "synonym_detected"
        }
      ]
    }
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If normalization already stored, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `knowledgeId`.

---

## 5.11 KnowledgeValidationRequested

### Purpose
Requests the validation service to assess quality, completeness, and consistency of normalized knowledge.

### Topic
`knowledge.validation.requested`

### Producer
`orchestration-service` (Python worker)

### Consumers
`validation-service` (Python worker)

### Trigger
Orchestration service receives `KnowledgeNormalized` and determines validation is needed.

### Payload Schema
```json
{
  "knowledgeId": "uuid",
  "canonicalStoryId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "validationConfig": {
    "model": "gemini-2.5-pro | claude-sonnet-4 | gpt-4o",
    "promptVersion": "knowledge-validation-v2",
    "temperature": 0.1,
    "maxTokens": 4096
  },
  "normalizedKnowledge": {
    "themes": [],
    "entities": [],
    "claims": [],
    "motifs": [],
    "rituals": [],
    "beliefs": [],
    "contradictions": []
  }
}
```

### Idempotency Rules
- Consumer MUST check if `jobId` already processed.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `jobId`.

---

## 5.12 KnowledgeValidated

### Purpose
Indicates that knowledge has passed validation and is ready for downstream consumption.

### Topic
`knowledge.validated`

### Producer
`validation-service` (Python worker)

### Consumers
`orchestration-service` (Python worker), `knowledge-service` (Spring Boot)

### Trigger
Validation service completes knowledge validation successfully.

### Payload Schema
```json
{
  "knowledgeId": "uuid",
  "canonicalStoryId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "validatedAt": "ISO8601",
  "validationResult": {
    "overallScore": 0.85,
    "passed": true,
    "schemaValid": true,
    "completenessScore": 0.82,
    "confidenceScore": 0.88,
    "consistencyScore": 0.91
  },
  "warnings": [
    {
      "type": "missing_evidence | low_confidence | research_gap",
      "target": "entity | claim | motif",
      "targetId": "uuid",
      "message": "string",
      "severity": "low | medium | high"
    }
  ],
  "issues": [],
  "validationMetadata": {
    "modelUsed": "gemini-2.5-pro",
    "promptVersion": "knowledge-validation-v2",
    "inputTokens": 2800,
    "outputTokens": 950,
    "executionCost": 0.0024,
    "executionTimeMs": 7200
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If validation already stored for `knowledgeId`, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `knowledgeId`.

---

## 5.13 ArticleGenerationRequested

### Purpose
Requests the article service to generate a publication-ready article from validated knowledge.

### Topic
`article.generation.requested`

### Producer
`orchestration-service` (Python worker)

### Consumers
`article-service` (Python worker)

### Trigger
Orchestration service receives `KnowledgeValidated` and triggers article generation based on configured article types.

### Payload Schema
```json
{
  "canonicalStoryId": "uuid",
  "knowledgeId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "articleType": "narrative | knowledge | news | creative",
  "generationConfig": {
    "model": "gemini-2.5-pro | claude-sonnet-4 | gpt-4o",
    "promptVersion": "article-generation-narrative-v3",
    "temperature": 0.4,
    "maxTokens": 16384
  },
  "language": "id | en",
  "validatedKnowledge": {
    "themes": [],
    "entities": [],
    "claims": [],
    "motifs": [],
    "rituals": [],
    "beliefs": []
  },
  "requirements": {
    "minLength": 1500,
    "maxLength": 5000,
    "includeSources": true,
    "includeProvenance": true
  }
}
```

### Idempotency Rules
- Consumer MUST check if `jobId` already processed.
- If article already generated, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `jobId`.

---

## 5.14 ArticleGenerated

### Purpose
Indicates that an article draft has been generated and is ready for review and publication.

### Topic
`article.generated`

### Producer
`article-service` (Python worker)

### Consumers
`orchestration-service` (Python worker), `workflow-service` (Spring Boot, via bridge)

### Trigger
Article service completes article generation successfully.

### Payload Schema
```json
{
  "canonicalStoryId": "uuid",
  "knowledgeId": "uuid",
  "sourceId": "uuid",
  "jobId": "uuid",
  "articleDraftId": "uuid",
  "articleType": "narrative | knowledge | news | creative",
  "title": "string",
  "language": "id | en",
  "wordCount": 2840,
  "qualityScore": 0.87,
  "generationMetadata": {
    "modelUsed": "gemini-2.5-pro",
    "promptVersion": "article-generation-narrative-v3",
    "inputTokens": 6500,
    "outputTokens": 3800,
    "executionCost": 0.0076,
    "executionTimeMs": 18500
  },
  "storageUrl": "string (object storage path to markdown content)",
  "preview": "string (first 500 characters of article)"
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If `articleDraftId` already stored, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `articleDraftId`.

---

## 5.15 EmbeddingGenerationRequested

### Purpose
Requests the embedding service to generate vector embeddings for knowledge artifacts and/or articles.

### Topic
`embedding.generation.requested`

### Producer
`orchestration-service` (Python worker)

### Consumers
`embedding-service` (Python worker)

### Trigger
Orchestration service triggers embedding generation after knowledge validation or article generation completes.

### Payload Schema
```json
{
  "jobId": "uuid",
  "embeddingTargets": [
    {
      "targetType": "story | article | entity | theme | claim | motif",
      "targetId": "uuid",
      "content": "string (text to embed)",
      "language": "id | en"
    }
  ],
  "embeddingConfig": {
    "model": "text-embedding-3-large | gecko | bge-m3",
    "dimensions": 1536,
    "batchSize": 32
  }
}
```

### Idempotency Rules
- Consumer MUST check if any target IDs in the batch have already been embedded.
- Skip already-processed targets.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `jobId`.
- No ordering requirements between targets.

---

## 5.16 EmbeddingGenerated

### Purpose
Indicates that vector embeddings have been generated and stored for the target artifacts.

### Topic
`embedding.generated`

### Producer
`embedding-service` (Python worker)

### Consumers
`orchestration-service` (Python worker), `data-platform` (weaviate-sync)

### Trigger
Embedding service completes embedding generation for all targets in the requested batch.

### Payload Schema
```json
{
  "jobId": "uuid",
  "embeddingResults": [
    {
      "targetType": "story | article | entity | theme | claim | motif",
      "targetId": "uuid",
      "embeddingId": "uuid",
      "dimension": 1536,
      "model": "text-embedding-3-large",
      "storageUrl": "string (vector storage reference)",
      "hash": "string (sha256 of source text for integrity)"
    }
  ],
  "embeddingMetadata": {
    "modelUsed": "text-embedding-3-large",
    "totalTargets": 12,
    "successCount": 12,
    "failedCount": 0,
    "inputTokens": 18000,
    "executionCost": 0.0009,
    "executionTimeMs": 3450
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- Deduplicate by `embeddingId` on the consumer side.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `jobId`.

---

## 5.17 GraphProjectionRequested

### Purpose
Requests the knowledge graph projection to be updated with new or modified knowledge artifacts.

### Topic
`graph.projection.requested`

### Producer
`orchestration-service` (Python worker)

### Consumers
`data-platform` (neo4j-sync worker)

### Trigger
Orchestration service receives `KnowledgeValidated` or `CanonicalStoryExtracted` with graph projection enabled.

### Payload Schema
```json
{
  "projectionId": "uuid",
  "canonicalStoryId": "uuid",
  "knowledgeId": "uuid",
  "jobId": "uuid",
  "projectionType": "incremental | full_rebuild",
  "validatedKnowledge": {
    "story": {
      "storyId": "uuid",
      "title": "string",
      "summary": "string"
    },
    "themes": [],
    "entities": [],
    "claims": [],
    "motifs": [],
    "rituals": [],
    "beliefs": [],
    "relationships": [
      {
        "sourceId": "uuid",
        "sourceType": "entity | theme | motif",
        "targetId": "uuid",
        "targetType": "entity | theme | motif",
        "relationType": "associated_with | manifestation_of | appears_in | contradicts",
        "confidence": 0.85
      }
    ]
  }
}
```

### Idempotency Rules
- Consumer MUST check if `projectionId` already processed.
- Graph projections are UPSERT operations.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `projectionId`.

---

## 5.18 GraphProjected

### Purpose
Indicates that the knowledge graph projection has been successfully updated.

### Topic
`graph.projected`

### Producer
`data-platform` (neo4j-sync)

### Consumers
`orchestration-service` (Python worker)

### Trigger
Neo4j sync completes the graph projection update.

### Payload Schema
```json
{
  "projectionId": "uuid",
  "canonicalStoryId": "uuid",
  "knowledgeId": "uuid",
  "jobId": "uuid",
  "projectedAt": "ISO8601",
  "projectionMetadata": {
    "nodesCreated": 15,
    "nodesUpdated": 3,
    "relationshipsCreated": 28,
    "relationshipsUpdated": 5,
    "executionTimeMs": 1200
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `projectionId`.

---

## 5.19 ReviewRequested

### Purpose
Indicates that a content artifact (story or article) has been submitted for human review via the editorial workflow.

### Topic
`review.requested`

### Producer
`orchestration-service` (AI Python worker) or `content-service` (Spring Boot)

### Consumers
`workflow-service` (Spring Boot)

### Trigger
AI pipeline completes article generation, or a user submits content for manual review.

### Payload Schema
```json
{
  "reviewId": "uuid",
  "targetType": "story | article",
  "targetId": "uuid",
  "submittedBy": "uuid (user or system identifier)",
  "submittedAt": "ISO8601",
  "workflowType": "editorial_review | content_approval",
  "reviewers": ["uuid"] (optional, specific reviewers),
  "context": {
    "sourceId": "uuid (optional)",
    "canonicalStoryId": "uuid (optional)",
    "knowledgeId": "uuid (optional)",
    "qualityScore": 0.87
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If review already exists for the target, the event is a no-op.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `reviewId`.

---

## 5.20 ReviewApproved

### Purpose
Indicates that a human reviewer has approved a content artifact, allowing it to proceed in the pipeline.

### Topic
`review.approved`

### Producer
`workflow-service` (Spring Boot)

### Consumers
`orchestration-service` (AI Python worker, via bridge), `content-service` (Spring Boot), `knowledge-service` (Spring Boot)

### Trigger
A reviewer approves the content in the workflow system.

### Payload Schema
```json
{
  "reviewId": "uuid",
  "targetType": "story | article",
  "targetId": "uuid",
  "approvedBy": "uuid (reviewer user ID)",
  "approvedAt": "ISO8601",
  "decision": "approved",
  "comments": "string (optional)",
  "context": {
    "sourceId": "uuid (optional)",
    "canonicalStoryId": "uuid (optional)",
    "knowledgeId": "uuid (optional)",
    "articleDraftId": "uuid (optional)"
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If `reviewId` already processed, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `reviewId`.

---

## 5.21 ReviewRejected

### Purpose
Indicates that a human reviewer has rejected a content artifact, requiring revision.

### Topic
`review.rejected`

### Producer
`workflow-service` (Spring Boot)

### Consumers
`orchestration-service` (AI Python worker, via bridge), `content-service` (Spring Boot), `knowledge-service` (Spring Boot)

### Trigger
A reviewer rejects the content in the workflow system.

### Payload Schema
```json
{
  "reviewId": "uuid",
  "targetType": "story | article",
  "targetId": "uuid",
  "rejectedBy": "uuid (reviewer user ID)",
  "rejectedAt": "ISO8601",
  "decision": "rejected",
  "rejectionReason": "incomplete | inaccurate | needs_revision | duplicate | inappropriate",
  "comments": "string (detailed feedback)",
  "context": {
    "sourceId": "uuid (optional)",
    "canonicalStoryId": "uuid (optional)",
    "knowledgeId": "uuid (optional)",
    "articleDraftId": "uuid (optional)"
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `reviewId`.

---

## 5.22 PublicationRequested

### Purpose
Requests that an approved content artifact be published and made publicly available.

### Topic
`publication.requested`

### Producer
`workflow-service` (Spring Boot)

### Consumers
`content-service` (Spring Boot)

### Trigger
Content passes editorial review and publication is triggered.

### Payload Schema
```json
{
  "publicationId": "uuid",
  "targetType": "story | article",
  "targetId": "uuid",
  "requestedBy": "uuid (user ID)",
  "requestedAt": "ISO8601",
  "publishConfig": {
    "publishDate": "ISO8601 (scheduled, optional)",
    "visibility": "public | members_only | restricted",
    "notifySubscribers": false,
    "includeInFeed": true
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.
- If `targetId` already published, skip.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `publicationId`.

---

## 5.23 PublicationCompleted

### Purpose
Indicates that content has been successfully published and is live.

### Topic
`publication.completed`

### Producer
`content-service` (Spring Boot)

### Consumers
`orchestration-service` (AI Python worker, via bridge), `knowledge-service` (Spring Boot), `research-service` (Spring Boot)

### Trigger
Content service completes the publication process.

### Payload Schema
```json
{
  "publicationId": "uuid",
  "targetType": "story | article",
  "targetId": "uuid",
  "publishedAt": "ISO8601",
  "publishedBy": "uuid (user ID)",
  "publicationMetadata": {
    "slug": "string",
    "visibility": "public",
    "url": "string (public URL)",
    "version": 1
  }
}
```

### Idempotency Rules
- Deduplicate by `eventId`.

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 5 retries.

### Ordering Rules
- Partition key: `publicationId`.

---

# 6. Payload Contracts

## 6.1 SourceSubmitted — Full JSON Example

```json
{
  "eventId": "e7b8c9a0-1d2f-3a4b-5c6d-7e8f9a0b1c2d",
  "eventType": "SourceSubmitted",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T14:30:00Z",
  "producer": "content-service",
  "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "data": {
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "sourceType": "youtube_video",
    "externalUrl": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "platformSourceId": "dQw4w9WgXcQ",
    "channelId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Misteri Kuntilanak di Desa Sukamaju",
    "description": "Dokumentasi wawancara dengan warga...",
    "language": "id",
    "submittedBy": "f1e2d3c4-b5a6-7890-fedc-ba9876543210",
    "submittedAt": "2026-06-20T14:30:00Z"
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": null,
    "jobId": null
  }
}
```

## 6.2 SourceMetadataImported — Full JSON Example

```json
{
  "eventId": "f9e8d7c6-b5a4-3c2d-1e0f-9a8b7c6d5e4f",
  "eventType": "SourceMetadataImported",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T14:31:30Z",
  "producer": "ingestion-service",
  "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "data": {
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "sourceType": "youtube_video",
    "title": "Misteri Kuntilanak di Desa Sukamaju",
    "description": "Dokumentasi wawancara dengan warga Desa Sukamaju mengenai penampakan Kuntilanak di area pemakaman. Narasumber: Pak Sariman, Bu Dewi.",
    "thumbnailUrl": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "durationSeconds": 2847,
    "publishedAt": "2026-06-15T08:00:00Z",
    "tags": ["kuntilanak", "misteri", "desa sukamaju", "hantu indonesia"],
    "language": "id",
    "metadata": {
      "viewCount": 15420,
      "likeCount": 843,
      "channelTitle": "Jelajah Misteri Nusantara"
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "e7b8c9a0-1d2f-3a4b-5c6d-7e8f9a0b1c2d",
    "jobId": null
  }
}
```

## 6.3 TranscriptImported — Full JSON Example

```json
{
  "eventId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "eventType": "TranscriptImported",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:00:00Z",
  "producer": "ingestion-service",
  "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "data": {
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "transcriptId": "d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b",
    "language": "id",
    "transcriptType": "youtube_caption",
    "textLength": 45280,
    "hasTimestamps": true,
    "segmentCount": 184,
    "storageUrl": "s3://ai-platform/transcripts/d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b.json"
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "f9e8d7c6-b5a4-3c2d-1e0f-9a8b7c6d5e4f",
    "jobId": null
  }
}
```

## 6.4 TranscriptNormalized — Full JSON Example

```json
{
  "eventId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "eventType": "TranscriptNormalized",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:05:00Z",
  "producer": "ingestion-service",
  "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "data": {
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "transcriptId": "d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b",
    "normalizedVersion": 1,
    "segments": [
      {
        "segmentIndex": 0,
        "startTime": 0.0,
        "endTime": 15.2,
        "speaker": "Pewawancara",
        "text": "Selamat malam, Pak Sariman. Terima kasih sudah bersedia ditemui.",
        "confidence": 0.98
      },
      {
        "segmentIndex": 1,
        "startTime": 15.3,
        "endTime": 45.8,
        "speaker": "Pak Sariman",
        "text": "Selamat malam. Iya, silakan. Mau tanya apa saja tentang Kuntilanak?",
        "confidence": 0.96
      },
      {
        "segmentIndex": 2,
        "startTime": 46.0,
        "endTime": 120.5,
        "speaker": "Pak Sariman",
        "text": "Jadi ceritanya, waktu itu tahun 2019, saya pulang dari sawah jam 11 malam...",
        "confidence": 0.94
      }
    ],
    "statistics": {
      "totalDurationSeconds": 2847,
      "segmentCount": 184,
      "speakerCount": 4,
      "averageConfidence": 0.95
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "jobId": null
  }
}
```

## 6.5 CanonicalStoryExtractionRequested — Full JSON Example

```json
{
  "eventId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "eventType": "CanonicalStoryExtractionRequested",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:05:01Z",
  "producer": "orchestration-service",
  "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "data": {
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "transcriptId": "d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b",
    "jobId": "e5f6a7b8-c901-2def-3456-789012345678",
    "extractionConfig": {
      "model": "gemini-2.5-pro",
      "promptVersion": "story-extraction-v3",
      "temperature": 0.3,
      "maxTokens": 8192
    },
    "transcript": {
      "segments": [
        {
          "segmentIndex": 0,
          "startTime": 0.0,
          "endTime": 15.2,
          "speaker": "Pewawancara",
          "text": "Selamat malam, Pak Sariman. Terima kasih sudah bersedia ditemui."
        },
        {
          "segmentIndex": 1,
          "startTime": 15.3,
          "endTime": 45.8,
          "speaker": "Pak Sariman",
          "text": "Selamat malam. Iya, silakan. Mau tanya apa saja tentang Kuntilanak?"
        }
      ],
      "language": "id"
    },
    "metadata": {
      "title": "Misteri Kuntilanak di Desa Sukamaju",
      "description": "Dokumentasi wawancara dengan warga Desa Sukamaju..."
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "jobId": "e5f6a7b8-c901-2def-3456-789012345678"
  }
}
```

## 6.6 CanonicalStoryExtracted — Full JSON Example

```json
{
  "eventId": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "eventType": "CanonicalStoryExtracted",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:08:30Z",
  "producer": "extraction-service",
  "aggregateId": "c5d6e7f8-a9b0-1234-efab-345678901234",
  "data": {
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "transcriptId": "d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b",
    "jobId": "e5f6a7b8-c901-2def-3456-789012345678",
    "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
    "storyTitle": "Penampakan Kuntilanak di Pemakaman Desa Sukamaju",
    "storySummary": "Pak Sariman, seorang petani di Desa Sukamaju, menceritakan pengalamannya melihat Kuntilanak di area pemakaman desa pada tahun 2019. Makhluk tersebut muncul dalam wujud perempuan berambut panjang dengan gaun putih, dan menghilang saat didekati.",
    "language": "id",
    "qualityScore": 0.88,
    "extractionMetadata": {
      "modelUsed": "gemini-2.5-pro",
      "promptVersion": "story-extraction-v3",
      "inputTokens": 4502,
      "outputTokens": 1280,
      "executionCost": 0.0032,
      "executionTimeMs": 12450
    },
    "extractedArtifacts": {
      "hasThemes": true,
      "hasEntities": true,
      "hasClaims": true,
      "hasMotifs": true,
      "hasBeliefs": false,
      "hasRituals": false
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "jobId": "e5f6a7b8-c901-2def-3456-789012345678"
  }
}
```

## 6.7 KnowledgeExtractionRequested — Full JSON Example

```json
{
  "eventId": "e5f6a7b8-c901-2def-3456-789012345679",
  "eventType": "KnowledgeExtractionRequested",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:08:31Z",
  "producer": "orchestration-service",
  "aggregateId": "c5d6e7f8-a9b0-1234-efab-345678901234",
  "data": {
    "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "jobId": "f6a7b8c9-d012-3efa-4567-890123456789",
    "extractionConfig": {
      "model": "gemini-2.5-pro",
      "promptVersion": "knowledge-extraction-v2",
      "temperature": 0.2,
      "maxTokens": 8192
    },
    "story": {
      "title": "Penampakan Kuntilanak di Pemakaman Desa Sukamaju",
      "summary": "Pak Sariman ...",
      "fullText": "Pak Sariman, seorang petani di Desa Sukamaju, menceritakan pengalamannya... [full extracted story text]"
    },
    "extractionTypes": [
      "themes", "entities", "claims", "motifs", "rituals", "beliefs", "contradictions"
    ]
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "d4e5f6a7-b8c9-0123-defa-234567890123",
    "jobId": "f6a7b8c9-d012-3efa-4567-890123456789"
  }
}
```

## 6.8 KnowledgeExtracted — Full JSON Example

```json
{
  "eventId": "f6a7b8c9-d012-3efa-4567-890123456789",
  "eventType": "KnowledgeExtracted",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:12:00Z",
  "producer": "extraction-service",
  "aggregateId": "c5d6e7f8-a9b0-1234-efab-345678901234",
  "data": {
    "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "jobId": "f6a7b8c9-d012-3efa-4567-890123456789",
    "knowledgeId": "a7b8c9d0-e123-4fab-5678-901234567890",
    "extractionMetadata": {
      "modelUsed": "gemini-2.5-pro",
      "promptVersion": "knowledge-extraction-v2",
      "inputTokens": 8200,
      "outputTokens": 3500,
      "executionCost": 0.0085,
      "executionTimeMs": 22300
    },
    "knowledge": {
      "themes": [
        {
          "themeId": "b8c9d0e1-f234-5abc-6789-012345678901",
          "name": "Penampakan Mistis di Area Pemakaman",
          "confidence": 0.92
        }
      ],
      "entities": [
        {
          "entityId": "c9d0e1f2-3456-7bcd-8901-234567890123",
          "name": "Kuntilanak",
          "entityType": "spirit",
          "confidence": 0.95
        },
        {
          "entityId": "d0e1f2a3-4567-8cde-9012-345678901234",
          "name": "Pak Sariman",
          "entityType": "person",
          "confidence": 0.98
        }
      ],
      "claims": [
        {
          "claimId": "e1f2a3b4-5678-9def-0123-456789012345",
          "statement": "Kuntilanak muncul di pemakaman Desa Sukamaju pada tahun 2019 sekitar jam 11 malam",
          "confidence": 0.85,
          "evidence": [
            {
              "segmentIndex": 2,
              "text": "waktu itu tahun 2019, saya pulang dari sawah jam 11 malam...",
              "startTime": 46.0,
              "endTime": 120.5
            }
          ]
        }
      ],
      "motifs": [
        {
          "motifId": "f2a3b4c5-6789-0efa-1234-567890123456",
          "name": "Penampakan di Pemakaman",
          "category": "setting",
          "confidence": 0.78
        }
      ],
      "rituals": [],
      "beliefs": [],
      "contradictions": []
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "e5f6a7b8-c901-2def-3456-789012345679",
    "jobId": "f6a7b8c9-d012-3efa-4567-890123456789"
  }
}
```

## 6.9 KnowledgeNormalized — Full JSON Example

```json
{
  "eventId": "a7b8c9d0-e123-4fab-5678-901234567891",
  "eventType": "KnowledgeNormalized",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:14:00Z",
  "producer": "normalization-service",
  "aggregateId": "a7b8c9d0-e123-4fab-5678-901234567890",
  "data": {
    "knowledgeId": "a7b8c9d0-e123-4fab-5678-901234567890",
    "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "jobId": "b8c9d0e1-f234-5abc-6789-012345678902",
    "normalizationMetadata": {
      "modelUsed": "claude-sonnet-4",
      "promptVersion": "knowledge-normalization-v1",
      "inputTokens": 3200,
      "outputTokens": 1100,
      "executionCost": 0.0028,
      "executionTimeMs": 8900,
      "aliasesResolved": 3,
      "duplicatesMerged": 2
    },
    "normalizedKnowledge": {
      "themes": [
        {
          "themeId": "b8c9d0e1-f234-5abc-6789-012345678901",
          "name": "Penampakan Mistis di Area Pemakaman",
          "confidence": 0.92
        }
      ],
      "entities": [
        {
          "entityId": "c9d0e1f2-3456-7bcd-8901-234567890123",
          "name": "Kuntilanak",
          "entityType": "spirit",
          "confidence": 0.95
        },
        {
          "entityId": "d0e1f2a3-4567-8cde-9012-345678901234",
          "name": "Pak Sariman",
          "entityType": "person",
          "confidence": 0.98
        }
      ],
      "claims": [],
      "motifs": [],
      "rituals": [],
      "beliefs": [],
      "contradictions": [],
      "normalizationReport": {
        "entityAliases": {
          "Kuntilanak": ["Pontianak", "Kunti"]
        },
        "mergedEntities": [
          {
            "targetId": "c9d0e1f2-3456-7bcd-8901-234567890123",
            "sourceIds": ["x1y2z3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6g"],
            "mergeReason": "synonym_detected"
          }
        ]
      }
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "f6a7b8c9-d012-3efa-4567-890123456789",
    "jobId": "b8c9d0e1-f234-5abc-6789-012345678902"
  }
}
```

## 6.10 KnowledgeValidated — Full JSON Example

```json
{
  "eventId": "b8c9d0e1-f234-5abc-6789-012345678903",
  "eventType": "KnowledgeValidated",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:16:00Z",
  "producer": "validation-service",
  "aggregateId": "a7b8c9d0-e123-4fab-5678-901234567890",
  "data": {
    "knowledgeId": "a7b8c9d0-e123-4fab-5678-901234567890",
    "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "jobId": "c9d0e1f2-3456-7bcd-8901-234567890123",
    "validatedAt": "2026-06-20T15:16:00Z",
    "validationResult": {
      "overallScore": 0.85,
      "passed": true,
      "schemaValid": true,
      "completenessScore": 0.82,
      "confidenceScore": 0.88,
      "consistencyScore": 0.91
    },
    "warnings": [
      {
        "type": "missing_evidence",
        "target": "claim",
        "targetId": "e1f2a3b4-5678-9def-0123-456789012345",
        "message": "Claim has only one evidence segment; corroboration recommended",
        "severity": "low"
      }
    ],
    "issues": [],
    "validationMetadata": {
      "modelUsed": "gemini-2.5-pro",
      "promptVersion": "knowledge-validation-v2",
      "inputTokens": 2800,
      "outputTokens": 950,
      "executionCost": 0.0024,
      "executionTimeMs": 7200
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "a7b8c9d0-e123-4fab-5678-901234567891",
    "jobId": "c9d0e1f2-3456-7bcd-8901-234567890123"
  }
}
```

## 6.11 ArticleGenerated — Full JSON Example

```json
{
  "eventId": "c9d0e1f2-3456-7bcd-8901-234567890124",
  "eventType": "ArticleGenerated",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:20:00Z",
  "producer": "article-service",
  "aggregateId": "d0e1f2a3-4567-8cde-9012-345678901235",
  "data": {
    "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
    "knowledgeId": "a7b8c9d0-e123-4fab-5678-901234567890",
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "jobId": "d0e1f2a3-4567-8cde-9012-345678901235",
    "articleDraftId": "d0e1f2a3-4567-8cde-9012-345678901235",
    "articleType": "narrative",
    "title": "Misteri Kuntilanak di Desa Sukamaju: Kesaksian Pak Sariman",
    "language": "id",
    "wordCount": 2840,
    "qualityScore": 0.87,
    "generationMetadata": {
      "modelUsed": "gemini-2.5-pro",
      "promptVersion": "article-generation-narrative-v3",
      "inputTokens": 6500,
      "outputTokens": 3800,
      "executionCost": 0.0076,
      "executionTimeMs": 18500
    },
    "storageUrl": "s3://ai-platform/articles/d0e1f2a3-4567-8cde-9012-345678901235.md",
    "preview": "Desa Sukamaju, sebuah desa kecil di Jawa Timur, menyimpan cerita mistis yang telah lama menjadi perbincangan warga. Pada tahun 2019, seorang petani bernama Pak Sariman mengalami pengalaman yang tidak akan pernah dia lupakan..."
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "b8c9d0e1-f234-5abc-6789-012345678903",
    "jobId": "d0e1f2a3-4567-8cde-9012-345678901235"
  }
}
```

## 6.12 EmbeddingGenerated — Full JSON Example

```json
{
  "eventId": "d0e1f2a3-4567-8cde-9012-345678901236",
  "eventType": "EmbeddingGenerated",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T15:22:00Z",
  "producer": "embedding-service",
  "aggregateId": "c5d6e7f8-a9b0-1234-efab-345678901234",
  "data": {
    "jobId": "e1f2a3b4-5678-9def-0123-456789012346",
    "embeddingResults": [
      {
        "targetType": "story",
        "targetId": "c5d6e7f8-a9b0-1234-efab-345678901234",
        "embeddingId": "f2a3b4c5-6789-0efa-1234-567890123457",
        "dimension": 1536,
        "model": "text-embedding-3-large",
        "storageUrl": "weaviate://living-atlas/stories/c5d6e7f8-a9b0-1234-efab-345678901234",
        "hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
      },
      {
        "targetType": "entity",
        "targetId": "c9d0e1f2-3456-7bcd-8901-234567890123",
        "embeddingId": "a3b4c5d6-e789-0f12-3456-789012345678",
        "dimension": 1536,
        "model": "text-embedding-3-large",
        "storageUrl": "weaviate://living-atlas/entities/c9d0e1f2-3456-7bcd-8901-234567890123",
        "hash": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1"
      }
    ],
    "embeddingMetadata": {
      "modelUsed": "text-embedding-3-large",
      "totalTargets": 12,
      "successCount": 12,
      "failedCount": 0,
      "inputTokens": 18000,
      "executionCost": 0.0009,
      "executionTimeMs": 3450
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "c9d0e1f2-3456-7bcd-8901-234567890124",
    "jobId": "e1f2a3b4-5678-9def-0123-456789012346"
  }
}
```

## 6.13 ReviewApproved — Full JSON Example

```json
{
  "eventId": "e1f2a3b4-5678-9def-0123-456789012347",
  "eventType": "ReviewApproved",
  "eventVersion": 1,
  "occurredAt": "2026-06-21T09:00:00Z",
  "producer": "workflow-service",
  "aggregateId": "d0e1f2a3-4567-8cde-9012-345678901235",
  "data": {
    "reviewId": "f2a3b4c5-6789-0efa-1234-567890123457",
    "targetType": "article",
    "targetId": "d0e1f2a3-4567-8cde-9012-345678901235",
    "approvedBy": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "approvedAt": "2026-06-21T09:00:00Z",
    "decision": "approved",
    "comments": "Artikel bagus, beberapa referensi silang ditambahkan.",
    "context": {
      "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
      "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
      "knowledgeId": "a7b8c9d0-e123-4fab-5678-901234567890",
      "articleDraftId": "d0e1f2a3-4567-8cde-9012-345678901235"
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "c9d0e1f2-3456-7bcd-8901-234567890124",
    "jobId": null
  }
}
```

## 6.14 PublicationCompleted — Full JSON Example

```json
{
  "eventId": "f2a3b4c5-6789-0efa-1234-567890123458",
  "eventType": "PublicationCompleted",
  "eventVersion": 1,
  "occurredAt": "2026-06-21T09:05:00Z",
  "producer": "content-service",
  "aggregateId": "d0e1f2a3-4567-8cde-9012-345678901235",
  "data": {
    "publicationId": "a3b4c5d6-e789-0f12-3456-789012345679",
    "targetType": "article",
    "targetId": "d0e1f2a3-4567-8cde-9012-345678901235",
    "publishedAt": "2026-06-21T09:05:00Z",
    "publishedBy": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "publicationMetadata": {
      "slug": "misteri-kuntilanak-desa-sukamaju",
      "visibility": "public",
      "url": "https://livingatlas.id/stories/misteri-kuntilanak-desa-sukamaju",
      "version": 1
    }
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "causationId": "e1f2a3b4-5678-9def-0123-456789012347",
    "jobId": null
  }
}
```

---

# 7. Event Versioning Strategy

## 7.1 Version Lifecycle

Each event type tracks its own version independently.

```
v1 ──→ v2 ──→ v3 ──→ ...
       ↑     ↑
    current deprecated
```

**States:**
- **Active:** Current version. All producers must emit this version.
- **Deprecated:** Old version still consumed but no longer produced. Consumers must support.
- **Removed:** Old version no longer supported. Consumers must migrate.

## 7.2 Version Compatibility Contract

| Change | Version Impact | Producer Action | Consumer Action |
|--------|---------------|----------------|-----------------|
| Add optional field | Minor (+0.1) | Add field, include default | Ignore unknown fields |
| Add required field | Major (+1) | New version created | Must implement |
| Remove field | Major (+1) | New version created | Must migrate |
| Rename field | Major (+1) | New version created | Must migrate |
| Change field type | Major (+1) | New version created | Must migrate |
| Reduce field constraints | Minor (+0.1) | Loosen validation | Accept new values |
| Increase field constraints | Major (+1) | New version created | Must migrate |

## 7.3 Coexistence Period

When a major version is introduced:
- **Deprecation period:** 90 days from the release of the new version.
- During deprecation: both v1 and v2 event types exist in the same topic.
- After 90 days: v1 is removed from production; consumers must have migrated.

### Example: KnowledgeValidated v1 → v2

**v1 (current, active):**
```json
{
  "validationResult": {
    "overallScore": 0.85,
    "passed": true
  }
}
```

**v2 (new, introduced day 0):**
```json
{
  "validationResult": {
    "overallScore": 0.85,
    "passed": true,
    "completenessScore": 0.82,
    "confidenceScore": 0.88,
    "consistencyScore": 0.91
  },
  "warnings": [],
  "issues": []
}
```

**Migration window:**
```
Day 0:     Producers emit v2. Consumers must accept both v1 and v2.
Day 0-90:  Legacy consumers migrate to v2. V1 still consumed.
Day 90:    v1 deprecated. Producers stop emitting v1. 
Day 90+:   Only v2 exists. All consumers must use v2.
```

## 7.4 Event Type Naming for Versions

The `eventType` field in the envelope carries the version-independent name. The `eventVersion` field distinguishes the schema.

```json
{
  "eventType": "KnowledgeValidated",
  "eventVersion": 2,
  "data": {}
}
```

Major version changes that break consumers should use a new topic:

```
source.submitted.v2
```

New minor versions within the same major version share the same topic:

```
knowledge.validated  ← v1.0 and v1.1 both use this topic
```

## 7.5 Schema Registry

All event schemas MUST be registered in a schema registry (Redpanda Schema Registry or Apicurio).

- **Schema ID:** Unique per event type + version combination.
- **Compatibility mode:** `BACKWARD` — new schema must be readable by consumers using old schema.
- **Evolution:** Auto-register on deployment.

---

# 8. Dead Letter Handling

## 8.1 Retry Policy

| Failure Type | Retryable | Initial Retry | Backoff | Max Retries |
|-------------|-----------|---------------|---------|-------------|
| Rate Limit (429) | Yes | 1 minute | Exponential | 5 |
| Temporary Outage (5xx) | Yes | 1 minute | Exponential | 5 |
| Timeout | Yes | 1 minute | Exponential | 5 |
| Network Failure | Yes | 1 minute | Exponential | 5 |
| Schema Validation Error | No | — | — | 0 (DLQ immediately) |
| Business Logic Error | No | — | — | 0 (DLQ immediately) |
| Poison Message | No | — | — | 0 (DLQ immediately) |

**Backoff schedule:**
```
Retry 1:  1 minute
Retry 2:  5 minutes
Retry 3:  15 minutes
Retry 4:  1 hour
Retry 5:  1 hour (final)
```
Total = ~2 hours 21 minutes before dead letter.

## 8.2 Dead Letter Queue Configuration

Each source topic has a corresponding DLQ topic:

```
Topic: source.submitted
DLQ:   source.submitted.dlq

Topic: knowledge.validated
DLQ:   knowledge.validated.dlq
```

**DLQ message envelope:**
```json
{
  "originalEvent": { /* the full original AiBridgeEvent */ },
  "dlqMetadata": {
    "failedAt": "2026-06-20T16:00:00Z",
    "failedConsumer": "extraction-service",
    "failureReason": "Rate limit exceeded after 5 retries",
    "failureType": "rate_limit",
    "retryCount": 5,
    "lastError": "429 Too Many Requests",
    "lastErrorTraceback": "..."  /* Python traceback or Java stack trace */
  }
}
```

## 8.3 Poison Message Handling

**Detection:**
- Message that fails schema validation.
- Message that causes repeated business logic errors.
- Message that exceeds max retries with the same error.

**Handling:**
1. Route to DLQ immediately (no retries for validation errors).
2. Alert on-call engineer via monitoring (see Section 9).
3. Quarantine message for manual inspection.

**Manual recovery flow:**
1. Engineer inspects DLQ message via admin UI or CLI.
2. Engineer fixes the underlying issue (e.g., missing data, schema mismatch).
3. Engineer replays the message from DLQ to the original topic.
4. Consumer processes the message normally.

## 8.4 Recovery Procedures

### Automated Recovery
Messages fail due to transient issues (rate limits, timeouts). They are retried automatically per the retry schedule. No manual intervention required.

### Semi-Automated Recovery
Messages that fail consistently may be fixed by:
1. **Patching schema:** If the schema registry is too strict, update compatibility.
2. **Patching consumer:** Deploy a fix to the consumer and replay from DLQ.
3. **Replay tool:** CLI tool to move messages from DLQ back to source topic.

### Manual Recovery
Messages that require human judgment (e.g., corrupt data, missing references):
1. Quarantine in DLQ.
2. Engineer reviews the message.
3. Either: a) Fix data and replay, b) Delete the message, c) Trigger reprocessing from an upstream event.

**Replay command (CLI tool):**
```bash
# Replay all messages from DLQ back to source topic
redpanda-replay --dlq source.submitted.dlq --topic source.submitted

# Replay a specific message
redpanda-replay --dlq source.submitted.dlq --topic source.submitted --message-id <uuid>
```

### Dead Letter Table (PostgreSQL)
For services using transactional outbox (Spring Boot services), failed outbox entries are tracked:

```sql
CREATE TABLE system.dead_letter_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_event_id UUID NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL,
    failure_reason TEXT NOT NULL,
    failure_type VARCHAR(100) NOT NULL,
    retry_count INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'quarantined',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(255)
);
```

---

# 9. Observability

## 9.1 Tracing — Correlation IDs

Every event carries a `correlationId` in the `metadata` envelope.

**Scope:**
- The `correlationId` is generated once at the entry point of a processing flow.
- It propagates through every event in the flow.
- It enables end-to-end tracing across all services and workers.

**Generation:**
```python
# Python worker — generated on first event
correlation_id = str(uuid.uuid4())  # generated by content-service on SourceSubmitted
```

**Propagation:**
```
SourceSubmitted (correlationId: X)
  → SourceMetadataImported (correlationId: X, causationId: previousEventId)
    → TranscriptImported (correlationId: X, causationId: previousEventId)
      → CanonicalStoryExtractionRequested (correlationId: X, causationId: previousEventId)
        → ...
```

## 9.2 Causation IDs

Each event also carries a `causationId` — the `eventId` of the event that directly caused it.

**Structure:**
```
eventId: A
  causationId: null (first event)

eventId: B
  causationId: A (caused by event A)
  correlationId: X (same trace)

eventId: C
  causationId: B (caused by event B)
  correlationId: X (same trace)
```

**Usage:**
- Build a causal chain: A → B → C → D
- Debug: "What caused this event?"
- Audit: "Why was this article generated?"

## 9.3 Job IDs

Pipeline jobs are tracked with a `jobId` in the metadata. This is set when the orchestration service creates extraction/normalization/validation/article/embedding jobs.

**Job tracking table:**
```sql
CREATE TABLE ai_platform.jobs (
    job_id UUID PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL,       -- story_extraction, knowledge_extraction, normalization, validation, article_generation, embedding
    correlation_id UUID NOT NULL,
    aggregate_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX idx_jobs_correlation ON ai_platform.jobs(correlation_id);
CREATE INDEX idx_jobs_status ON ai_platform.jobs(status);
CREATE INDEX idx_jobs_created ON ai_platform.jobs(created_at);
```

## 9.4 Structured Logging

All workers must emit structured JSON logs.

**Log format:**
```json
{
  "timestamp": "2026-06-20T15:08:30.123Z",
  "level": "INFO",
  "service": "extraction-service",
  "worker": "story-extractor",
  "eventId": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "causationId": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "jobId": "e5f6a7b8-c901-2def-3456-789012345678",
  "message": "Canonical story extracted successfully",
  "extras": {
    "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
    "qualityScore": 0.88,
    "inputTokens": 4502,
    "outputTokens": 1280,
    "executionTimeMs": 12450
  }
}
```

## 9.5 Metrics

### Event Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ai_events_produced_total` | Counter | event_type, producer | Events emitted |
| `ai_events_consumed_total` | Counter | event_type, consumer | Events processed |
| `ai_events_failed_total` | Counter | event_type, consumer, failure_type | Events that failed |
| `ai_events_retry_total` | Counter | event_type, consumer, retry_count | Events being retried |
| `ai_events_dlq_total` | Counter | event_type, failure_type | Events sent to DLQ |
| `ai_event_processing_duration_ms` | Histogram | event_type, consumer | Processing time per event |

### Job Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ai_jobs_started_total` | Counter | job_type | Pipeline jobs started |
| `ai_jobs_completed_total` | Counter | job_type | Pipeline jobs completed |
| `ai_jobs_failed_total` | Counter | job_type, failure_type | Pipeline jobs failed |
| `ai_job_duration_ms` | Histogram | job_type | Duration per job type |

### Provider Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ai_provider_calls_total` | Counter | provider, model, operation | AI provider requests |
| `ai_provider_errors_total` | Counter | provider, model, error_type | AI provider errors |
| `ai_provider_latency_ms` | Histogram | provider, model | Provider response time |
| `ai_token_usage_total` | Counter | provider, model, token_type | Input/output token count |
| `ai_cost_total` | Counter | provider, model | Execution cost in USD |

## 9.6 Health Checks

Every consumer must expose a health endpoint:

```json
// GET /health
{
  "status": "UP",
  "service": "extraction-service",
  "version": "0.1.0",
  "uptime": "12h 34m 56s",
  "consumers": {
    "story.extraction.requested": {
      "status": "RUNNING",
      "partitionAssignments": [0, 1, 2],
      "lag": 0,
      "lastProcessed": "2026-06-20T15:08:30Z"
    },
    "knowledge.extraction.requested": {
      "status": "RUNNING",
      "partitionAssignments": [3, 4],
      "lag": 5,
      "lastProcessed": "2026-06-20T15:12:00Z"
    }
  },
  "database": {
    "status": "UP",
    "connectionPool": 8,
    "activeConnections": 2
  },
  "aiProviders": {
    "gemini": { "status": "UP", "lastCall": "2026-06-20T15:08:30Z" },
    "claude": { "status": "UP", "lastCall": "2026-06-20T15:14:00Z" }
  }
}
```

## 9.7 End-to-End Trace Example

```
content-service                  ingestion-service          extraction-service        orchestration-service
    │                                │                            │                           │
    │  SourceSubmitted                │                            │                           │
    │  correlationId: X              │                            │                           │
    │  causationId: null             │                            │                           │
    │ ──────────────────────────────►│                            │                           │
    │                                │  SourceMetadataImported    │                           │
    │                                │  correlationId: X          │                           │
    │                                │  causationId: A            │                           │
    │ ◄──────────────────────────────│                            │                           │
    │                                │  TranscriptImported        │                           │
    │                                │  correlationId: X          │                           │
    │                                │  causationId: B            │                           │
    │ ◄──────────────────────────────│                            │                           │
    │                                │                            │                           │
    │                                │  TranscriptNormalized      │                           │
    │                                │  correlationId: X          │                           │
    │                                │  causationId: C            │                           │
    │                                │ ───────────────────────────────────────────────────────►│
    │                                │                            │                           │
    │                                │                            │ CanonicalStoryExtraction  │
    │                                │                            │ Requested                 │
    │                                │                            │ correlationId: X          │
    │                                │                            │ causationId: D            │
    │                                │                            │◄──────────────────────────│
    │                                │                            │                           │
    │                                │                            │ CanonicalStoryExtracted   │
    │                                │                            │ correlationId: X          │
    │                                │                            │ causationId: E            │
    │                                │                            │ ──────────────────────────►│
```

---

# References

- **ADR-004:** Event-Driven Architecture with Transactional Outbox
- **ADR-009:** AI Pipeline Integration
- **PRD.md:** AI Platform Product Requirements Document
- **docs/architecture/domain-event-catalog.md:** Backend service event catalog (complement)
- **EventTopics.java:** Topic registry in `packages/shared-events`
- **AiBridgeEvent.java:** Event envelope implementation in `packages/shared-events`