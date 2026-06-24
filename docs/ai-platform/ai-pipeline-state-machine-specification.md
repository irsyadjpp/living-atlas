# AI Pipeline State Machine Specification

## The Living Atlas of Indonesian Mystery Culture

**Version:** 1.0  
**Status:** Draft  
**Owner:** AI Platform Team  
**Classification:** Principal Platform Engineering Document

---

# Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Pipeline Stages](#2-pipeline-stages)
3. [Job State Machine](#3-job-state-machine)
4. [Story Processing State Machine](#4-story-processing-state-machine)
5. [Knowledge Processing State Machine](#5-knowledge-processing-state-machine)
6. [Article Generation State Machine](#6-article-generation-state-machine)
7. [Failure Handling](#7-failure-handling)
8. [Human Review Workflow](#8-human-review-workflow)
9. [Recovery Strategy](#9-recovery-strategy)
10. [Operational Runbooks](#10-operational-runbooks)

---

# 1. Pipeline Overview

## 1.1 End-to-End Pipeline Flow

```
Source
  │
  ▼
Metadata Import ──────────► [Ingestion Service]
  │
  ▼
Transcript Import ────────► [Ingestion Service]
  │
  ▼
Transcript Normalization ──► [Ingestion Service]
  │
  ▼
Canonical Story Extraction ► [Extraction Service]
  │
  ▼
Knowledge Extraction ─────► [Extraction Service]
  │
  ▼
Knowledge Normalization ──► [Normalization Service]
  │
  ▼
Knowledge Validation ─────► [Validation Service]
  │
  ├──► Knowledge Persistence (PostgreSQL)
  │
  ▼
Article Generation ───────► [Article Service]
  │
  ▼
Embedding Generation ─────► [Embedding Service]
  │
  ▼
Graph Projection ─────────► [Neo4j Sync]
```

## 1.2 Pipeline Responsibilities

| Stage | Service | Responsibility | AI Call? |
|-------|---------|---------------|----------|
| Source Ingestion | ingestion-service | Fetch metadata, download/retrieve transcript | No |
| Transcript Normalization | ingestion-service | Clean text, diarize speakers, segment | No |
| Canonical Story Extraction | extraction-service | Extract structured story from transcript | Yes |
| Knowledge Extraction | extraction-service | Extract entities, themes, claims, motifs | Yes |
| Knowledge Normalization | normalization-service | Resolve aliases, merge duplicates | Yes |
| Knowledge Validation | validation-service | Score quality, detect gaps, validate schema | Yes |
| Article Generation | article-service | Generate publication-ready articles | Yes |
| Embedding Generation | embedding-service | Create vector embeddings | Yes (embedding model) |
| Graph Projection | neo4j-sync | Update knowledge graph | No |

## 1.3 Pipeline Orchestration

The orchestration-service is the central coordinator. It:

1. Receives initial events (`SourceSubmitted`, `TranscriptImported`).
2. Creates and tracks jobs in the `ai_platform.jobs` table.
3. Publishes `*Requested` events to trigger downstream workers.
4. Consumes `*Completed` events to advance pipeline state.
5. Handles retry logic and dead letter routing.
6. Tracks per-source pipeline state through the state machine.

## 1.4 Pipeline State per Source

Each source progresses through pipeline-level states independently:

```
METADATA_PENDING
    │
    ▼
METADATA_READY ──────────► TRANSCRIPT_PENDING
    │                           │
    │                           ▼
    │                    TRANSCRIPT_READY
    │                           │
    └───────────────────────────┘
                │
                ▼
        CANONICALIZED
                │
                ▼
          NORMALIZED
                │
                ▼
          VALIDATED
                │
                ▼
    ARTICLES_GENERATED
                │
                ▼
    EMBEDDINGS_GENERATED
                │
                ▼
          FINISHED
                │
                ▼
          FAILED (any stage)
          CANCELLED (any stage)
```

---

# 2. Pipeline Stages

## 2.1 Stage: Source Ingestion

### Purpose
Acquire source metadata and transcript from external providers (YouTube, RSS, manual upload).

### Input
- `SourceSubmitted` event from content-service.
- Contains: `sourceId`, `sourceType`, `platformSourceId`, `externalUrl`.

### Output
- `SourceMetadataImported` event (metadata stored in PostgreSQL).
- `TranscriptImported` event (transcript stored in object storage).

### Dependencies
- External API availability (YouTube Data API, RSS feed).
- Object storage availability (MinIO/S3).
- Network connectivity to external providers.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| YouTube API rate limit (429) | Exponential backoff, up to 5 retries | Yes |
| YouTube API unavailable (5xx) | Exponential backoff, up to 5 retries | Yes |
| Invalid URL / resource not found | DLQ immediately | No |
| Transcript not available | DLQ with flag `manual_transcript_required` | No |
| Object storage write failure | Exponential backoff, up to 5 retries | Yes |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour → 1 hour.
- Maximum: 5 retries.
- After 5 retries: DLQ with `failure_type=transient`.

### Manual Review Rules
- If transcript is unavailable after all retries: flag for manual upload.
- If metadata is incomplete (missing title, language): flag for manual enrichment.
- Manual review is triggered by setting pipeline state to `MANUAL_REVIEW_NEEDED`.

---

## 2.2 Stage: Transcript Normalization

### Purpose
Clean raw transcript text, perform speaker diarization, segment into timestamped chunks.

### Input
- Raw transcript text from `TranscriptImported` payload.
- Optional: speaker labels from ASR provider.

### Output
- `TranscriptNormalized` event.
- Contains: segments with speaker labels, confidence scores, timing.

### Dependencies
- Transcript text must be non-empty.
- Language must be detected or provided.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| Empty transcript | DLQ immediately | No |
| Language detection failure | Default to "id", proceed with warning | No |
| Segmentation timeout (ASR reprocessing) | Retry with backoff | Yes |
| Speaker diarization failure | Proceed without speaker labels | Partial |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 3 retries (lower because this is a lightweight stage).
- After 3 retries: DLQ.

### Manual Review Rules
- If transcript quality is below threshold (confidence < 0.5): flag for manual review.
- Reviewer can: accept as-is, upload corrected transcript, or reject source.

---

## 2.3 Stage: Canonical Story Extraction

### Purpose
Extract a structured canonical story from the normalized transcript using an AI provider.

### Input
- `CanonicalStoryExtractionRequested` event.
- Contains: transcript segments, metadata, extraction config (model, prompt version).

### Output
- `CanonicalStoryExtracted` event.
- Contains: story title, summary, quality score, extracted artifact flags.

### Dependencies
- AI provider availability (Gemini, Claude, or OpenAI).
- Prompt version must exist in prompt registry.
- Transcript must be normalized.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| AI provider rate limit (429) | Exponential backoff with jitter | Yes |
| AI provider unavailable (5xx) | Failover to alternate provider, retry | Yes |
| AI provider timeout (>120s) | Retry with reduced max tokens | Yes |
| Malformed output (invalid JSON) | Retry with stricter prompt (temperature=0) | Yes |
| Empty output (no story found) | DLQ for manual review | No |
| Schema validation failure | Retry once, then DLQ | Partial |
| Hallucination detected (provenance mismatch) | DLQ for manual review | No |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour → 1 hour.
- Maximum: 5 retries.
- Provider failover: try primary → secondary → tertiary provider on each retry.
- After 5 retries: DLQ.

### Manual Review Rules
- Quality score < 0.6: flag for manual review.
- Reviewers can: accept extracted story, edit and accept, or reject source.
- Manual re-extraction can be triggered with different prompt version.

---

## 2.4 Stage: Knowledge Extraction

### Purpose
Extract structured knowledge entities (themes, entities, claims, motifs, rituals, beliefs, contradictions) from a canonical story.

### Input
- `KnowledgeExtractionRequested` event.
- Contains: canonical story text, extraction types requested.

### Output
- `KnowledgeExtracted` event.
- Contains: knowledge object with all extracted entities.

### Dependencies
- Canonical story must be extracted.
- AI provider availability.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| AI provider failure | Failover to alternate provider | Yes |
| Partial extraction (some types failed) | Emit with partial results + warnings | Partial |
| Entity count exceeds threshold (>100) | Split into batches, re-request | Yes |
| Schema violation | Retry once with strict mode | Partial |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 4 retries.
- Partial success: emit `KnowledgeExtracted` with `warnings` array, do not retry.

### Manual Review Rules
- Extraction confidence < 0.5: flag for manual review.
- Zero entities extracted from non-empty story: flag for manual review.
- Contradictions detected: flag for manual resolution.

---

## 2.5 Stage: Knowledge Normalization

### Purpose
Resolve ambiguities, detect aliases, merge duplicate entities.

### Input
- `KnowledgeNormalizationRequested` event.
- Contains: extracted knowledge object.

### Output
- `KnowledgeNormalized` event.
- Contains: normalized knowledge with normalization report.

### Dependencies
- Knowledge must be extracted.
- AI provider availability (Claude recommended for normalization).

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| AI provider failure | Failover to alternate provider | Yes |
| Normalization makes no changes | Emit event with empty normalization report | No |
| Ambiguity cannot be resolved | Flag entity with `requires_human_resolution` | No |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 3 retries.
- After 3 retries: emit with warnings, proceed.

### Manual Review Rules
- Unresolved ambiguities: flagged for human resolution.
- Merged entities: reviewer can approve or reject each merge.
- New aliases discovered: reviewer can accept or reject.

---

## 2.6 Stage: Knowledge Validation

### Purpose
Assess quality, completeness, and consistency of normalized knowledge.

### Input
- `KnowledgeValidationRequested` event.
- Contains: normalized knowledge object.

### Output
- `KnowledgeValidated` event.
- Contains: validation result (score, passed, warnings, issues).

### Dependencies
- Knowledge must be normalized.
- AI provider availability.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| AI provider failure | Failover to alternate provider | Yes |
| Validation score below threshold | Pass with warnings, flag for review | No |
| Schema violation detected | DLQ immediately | No |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 3 retries.

### Manual Review Rules
- Overall score < 0.6: mandatory human review.
- Completeness score < 0.5: flag for missing data.
- Warnings with severity "high": reviewer must acknowledge.
- Research gaps detected: logged, no blocking action.

---

## 2.7 Stage: Article Generation

### Purpose
Generate publication-ready articles from validated knowledge.

### Input
- `ArticleGenerationRequested` event.
- Contains: validated knowledge, article type config, language.

### Output
- `ArticleGenerated` event.
- Contains: article draft ID, storage URL, quality score.

### Dependencies
- Knowledge must be validated.
- AI provider availability.
- Prompt version must exist for requested article type.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| AI provider failure | Failover to alternate provider | Yes |
| Article too short (< minLength) | Retry with higher max tokens | Yes |
| Article exceeds maxLength | Retry with lower max tokens | Yes |
| Quality score < 0.5 | Retry once with different model | Yes |
| Language mismatch (wrong language output) | Retry with language enforcement | Yes |
| Hallucinated content (provenance check fails) | DLQ for manual review | No |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 4 retries.
- Different model on each retry if quality threshold not met.
- After 4 retries: DLQ.

### Manual Review Rules
- Article quality score < 0.7: recommended for review.
- Article quality score < 0.5: mandatory review.
- Factual inaccuracies: reviewer can edit or reject.
- Style/tonal issues: reviewer can edit.

---

## 2.8 Stage: Embedding Generation

### Purpose
Generate vector embeddings for knowledge artifacts and articles.

### Input
- `EmbeddingGenerationRequested` event.
- Contains: list of target IDs and content texts.

### Output
- `EmbeddingGenerated` event.
- Contains: list of embedding results with storage references.

### Dependencies
- Embedding model availability (text-embedding-3-large, gecko, bge-m3).
- Weaviate or vector storage availability.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| Embedding model rate limit | Batch retry with backoff | Yes |
| Vector storage write failure | Retry batch | Yes |
| Partial batch failure | Retry only failed items | Yes |
| Content too long for model | Truncate to max token limit, proceed | No |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes.
- Maximum: 3 retries per batch.
- Individual item retry: failed items re-queued.

### Manual Review Rules
- No manual review required for embedding generation.
- If batch failure rate > 50%: alert operator.

---

## 2.9 Stage: Graph Projection

### Purpose
Update the knowledge graph (Neo4j) with new or modified knowledge artifacts.

### Input
- `GraphProjectionRequested` event.
- Contains: validated knowledge with relationships.

### Output
- `GraphProjected` event.
- Contains: projection metadata (nodes/relationships created/updated).

### Dependencies
- Neo4j database availability.
- Knowledge must be validated.

### Failure Modes
| Failure | Handling | Retryable |
|---------|----------|-----------|
| Neo4j connection failure | Retry with backoff | Yes |
| Cypher query failure (constraint violation) | DLQ immediately | No |
| Partial graph write (some nodes fail) | Rollback transaction, retry | Yes |

### Retry Rules
- Strategy: 1 minute → 5 minutes → 15 minutes → 1 hour.
- Maximum: 4 retries.

### Manual Review Rules
- Graph constraint violations: manual review by data engineer.
- Orphaned nodes (no relationships): flag for review.

---

# 3. Job State Machine

## 3.1 Job States

The AI Platform uses a unified job state machine that applies to all pipeline stage jobs.

```
                    ┌─────────────────────────────────────────────┐
                    │                                             │
                    ▼                                             │
              ┌──────────┐                                       │
              │ SUBMITTED│                                       │
              └────┬─────┘                                       │
                   │                                             │
                   ▼                                             │
              ┌──────────┐                                       │
              │  QUEUED  │                                       │
              └────┬─────┘                                       │
                   │                                             │
                   ▼                                             │
              ┌────────────┐         ┌──────────────┐            │
              │ PROCESSING │────────►│ WAITING_     │            │
              └──────┬─────┘         │ PROVIDER     │            │
                     │               └──────┬───────┘            │
                     │                      │                    │
                     │                      ▼                    │
                     │               ┌───────────┐               │
                     │               │ RETRYING  │───────────────┘
                     │               └─────┬─────┘
                     │                     │
                     │                     ▼
                     │               ┌──────────────┐
                     │               │ MANUAL_      │
                     │               │ REVIEW       │
                     │               └──────┬───────┘
                     │                      │
                     ▼                      ▼
              ┌───────────┐         ┌───────────┐
              │ COMPLETED │         │  FAILED   │
              └───────────┘         └─────┬─────┘
                                          │
                                    ┌───────────┐
                                    │ CANCELLED │
                                    └───────────┘
```

## 3.2 State Definitions

| State | Description | Allowed Actions |
|-------|-------------|-----------------|
| **SUBMITTED** | Job has been created and written to the database but not yet published to queue. | `publish`, `cancel` |
| **QUEUED** | Job message has been published to Redpanda topic. Waiting for worker to pick it up. | `cancel` |
| **PROCESSING** | Worker has received the message and is actively processing. | `cancel` |
| **WAITING_PROVIDER** | Worker has called the AI provider and is waiting for a response. | `cancel`, `timeout` |
| **RETRYING** | A transient failure occurred; job is in the retry backoff window. | `cancel`, `force_fail` |
| **MANUAL_REVIEW** | Job requires human intervention to proceed. | `approve`, `reject`, `restart` |
| **COMPLETED** | Job finished successfully. Terminal state. | None |
| **FAILED** | Job failed after exhausting all retries. Terminal state. | `restart`, `replay` |
| **CANCELLED** | Job was manually cancelled by an operator. Terminal state. | `restart` |

## 3.3 State Transitions

| From | To | Trigger | Condition | Side Effects |
|------|----|---------|-----------|-------------|
| SUBMITTED | QUEUED | `publish` | Job written to DB | Message published to Redpanda topic |
| SUBMITTED | CANCELLED | `cancel` | — | Job removed, no message published |
| QUEUED | PROCESSING | `worker_acquired` | Worker receives message | Update `started_at` timestamp |
| QUEUED | CANCELLED | `cancel` | — | Message skipped on consumption |
| PROCESSING | WAITING_PROVIDER | `ai_call_started` | Provider request initiated | Log provider + model + tokens |
| PROCESSING | COMPLETED | `success` | Business logic done | Emit result event, update DB |
| PROCESSING | FAILED | `non_retryable_error` | Schema/business logic error | Send to DLQ, emit PipelineFailed |
| PROCESSING | RETRYING | `retryable_error` | Transient failure | Increment retry count |
| PROCESSING | CANCELLED | `cancel` | Operator intervention | Cleanup resources |
| WAITING_PROVIDER | PROCESSING | `ai_response_received` | Provider returns result | Log latency + token usage |
| WAITING_PROVIDER | RETRYING | `provider_timeout` | >120s no response | Increment retry count |
| WAITING_PROVIDER | RETRYING | `provider_error` | Provider returns error (429, 5xx) | Increment retry count |
| WAITING_PROVIDER | CANCELLED | `cancel` | — | Cancel provider request |
| RETRYING | QUEUED | `requeue` | Retry delay elapsed | Message re-published to topic |
| RETRYING | MANUAL_REVIEW | `max_retries_exceeded` | Retry count >= 5 | Notify operator, send to DLQ |
| RETRYING | FAILED | `force_fail` | Operator decision | Send to DLQ |
| RETRYING | CANCELLED | `cancel` | — | Cleanup |
| MANUAL_REVIEW | COMPLETED | `approve` | Reviewer approves | Emit result event with `manual_review=true` |
| MANUAL_REVIEW | FAILED | `reject` | Reviewer rejects | Emit event with rejection reason |
| MANUAL_REVIEW | SUBMITTED | `restart` | Reviewer requests re-run | Create new job, reset retry count |
| FAILED | SUBMITTED | `restart` | Operator decides to retry | Create new job |
| FAILED | QUEUED | `replay` | Operator replays from DLQ | Message re-published |
| CANCELLED | SUBMITTED | `restart` | Operator decides to retry | Create new job |

## 3.4 Job Persistence

```sql
CREATE TABLE ai_platform.jobs (
    job_id UUID PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL,
        -- story_extraction, knowledge_extraction, knowledge_normalization,
        -- knowledge_validation, article_generation, embedding_generation,
        -- graph_projection, metadata_import, transcript_import, transcript_normalization
    correlation_id UUID NOT NULL,
    aggregate_id UUID NOT NULL,          -- sourceId, storyId, knowledgeId, etc.
    aggregate_type VARCHAR(100) NOT NULL, -- source, story, knowledge, article
    pipeline_id UUID,                     -- links jobs in same pipeline
    status VARCHAR(50) NOT NULL DEFAULT 'submitted',
        -- submitted, queued, processing, waiting_provider,
        -- retrying, manual_review, completed, failed, cancelled
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 5,
    current_provider VARCHAR(100),       -- gemini, claude, openai
    provider_attempts INTEGER NOT NULL DEFAULT 0,
    prompt_version VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    execution_cost DECIMAL(10,6),
    execution_time_ms INTEGER,
    error_message TEXT,
    error_type VARCHAR(100),             -- transient, schema, business_logic, poison
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    provider_called_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,           -- when retry delay expires
    metadata JSONB NOT NULL DEFAULT '{}'  -- extensible metadata
);

CREATE INDEX idx_jobs_correlation ON ai_platform.jobs(correlation_id);
CREATE INDEX idx_jobs_aggregate ON ai_platform.jobs(aggregate_id, aggregate_type);
CREATE INDEX idx_jobs_status ON ai_platform.jobs(status);
CREATE INDEX idx_jobs_next_retry ON ai_platform.jobs(next_retry_at)
    WHERE status = 'retrying';
CREATE INDEX idx_jobs_pipeline ON ai_platform.jobs(pipeline_id);
```

---

# 4. Story Processing State Machine

## 4.1 Pipeline State per Source

The story processing pipeline tracks the overall state of a source as it moves through extraction stages.

```
METADATA_PENDING
    │
    ▼
METADATA_READY
    │
    ▼
TRANSCRIPT_PENDING
    │
    ▼
TRANSCRIPT_READY
    │
    ▼
STORY_EXTRACTION_PENDING
    │
    ▼
STORY_EXTRACTED
    │
    ▼
KNOWLEDGE_EXTRACTION_PENDING
    │
    ▼
KNOWLEDGE_EXTRACTED
    │
    ▼
NORMALIZATION_PENDING
    │
    ▼
NORMALIZED
    │
    ▼
VALIDATION_PENDING
    │
    ▼
VALIDATED
    │
    ▼
COMPLETED
    │
    ▼
FAILED (any stage)
REVIEW_NEEDED (any stage)
```

## 4.2 State Definitions

| State | Description | Jobs Active |
|-------|-------------|-------------|
| METADATA_PENDING | Source registered, metadata not yet imported | metadata_import job |
| METADATA_READY | Metadata imported successfully | None |
| TRANSCRIPT_PENDING | Waiting for transcript | transcript_import job |
| TRANSCRIPT_READY | Transcript imported and normalized | None |
| STORY_EXTRACTION_PENDING | Ready for story extraction | story_extraction job |
| STORY_EXTRACTED | Canonical story extracted | None |
| KNOWLEDGE_EXTRACTION_PENDING | Ready for knowledge extraction | knowledge_extraction job |
| KNOWLEDGE_EXTRACTED | Knowledge extracted, pending normalization | None |
| NORMALIZATION_PENDING | Ready for normalization | knowledge_normalization job |
| NORMALIZED | Knowledge normalized, pending validation | None |
| VALIDATION_PENDING | Ready for validation | knowledge_validation job |
| VALIDATED | Knowledge validated | None |
| COMPLETED | All story processing complete | None |
| FAILED | Irrecoverable failure at any stage | None |
| REVIEW_NEEDED | Manual review required at any stage | None |

## 4.3 Transitions

| From | To | Trigger | Side Effects |
|------|----|---------|-------------|
| METADATA_PENDING | METADATA_READY | SourceMetadataImported consumed | Queue transcript import |
| METADATA_PENDING | FAILED | Metadata import failed after retries | Emit PipelineFailed |
| METADATA_PENDING | REVIEW_NEEDED | Metadata incomplete | Notify operator |
| METADATA_READY | TRANSCRIPT_PENDING | Transcript import requested | Create transcript_import job |
| TRANSCRIPT_PENDING | TRANSCRIPT_READY | TranscriptNormalized consumed | Queue story extraction |
| TRANSCRIPT_PENDING | FAILED | Transcript import failed after retries | Emit PipelineFailed |
| TRANSCRIPT_PENDING | REVIEW_NEEDED | Transcript unavailable, manual upload needed | Notify operator |
| TRANSCRIPT_READY | STORY_EXTRACTION_PENDING | Story extraction requested | Create story_extraction job, publish CanonicalStoryExtractionRequested |
| STORY_EXTRACTION_PENDING | STORY_EXTRACTED | CanonicalStoryExtracted consumed | Queue knowledge extraction |
| STORY_EXTRACTION_PENDING | FAILED | Extraction failed after retries | Emit PipelineFailed |
| STORY_EXTRACTION_PENDING | REVIEW_NEEDED | Extraction quality < 0.6 | Notify reviewer |
| STORY_EXTRACTED | KNOWLEDGE_EXTRACTION_PENDING | Knowledge extraction requested | Create knowledge_extraction job, publish KnowledgeExtractionRequested |
| KNOWLEDGE_EXTRACTION_PENDING | KNOWLEDGE_EXTRACTED | KnowledgeExtracted consumed | Queue normalization |
| KNOWLEDGE_EXTRACTION_PENDING | FAILED | Extraction failed after retries | Emit PipelineFailed |
| KNOWLEDGE_EXTRACTED | NORMALIZATION_PENDING | Normalization requested | Create normalization job, publish KnowledgeNormalizationRequested |
| NORMALIZATION_PENDING | NORMALIZED | KnowledgeNormalized consumed | Queue validation |
| NORMALIZATION_PENDING | FAILED | Normalization failed after retries | Emit PipelineFailed |
| NORMALIZED | VALIDATION_PENDING | Validation requested | Create validation job, publish KnowledgeValidationRequested |
| VALIDATION_PENDING | VALIDATED | KnowledgeValidated consumed | Pipeline stage complete |
| VALIDATION_PENDING | REVIEW_NEEDED | Validation score < 0.6 | Notify reviewer |
| VALIDATION_PENDING | FAILED | Validation failed after retries | Emit PipelineFailed |
| VALIDATED | COMPLETED | All downstream stages done | Emit PipelineCompleted |
| REVIEW_NEEDED | STORY_EXTRACTION_PENDING | Reviewer approves, re-extract | Restart extraction |
| REVIEW_NEEDED | VALIDATION_PENDING | Reviewer approves, continue | Continue pipeline |
| REVIEW_NEEDED | FAILED | Reviewer rejects source | Emit PipelineFailed |
| FAILED | METADATA_PENDING | Operator restarts from beginning | Re-create pipeline |
| FAILED | STORY_EXTRACTION_PENDING | Operator restarts from extraction | Re-extract |

## 4.4 Pipeline State Persistence

```sql
CREATE TABLE ai_platform.pipeline_states (
    source_id UUID PRIMARY KEY,
    current_state VARCHAR(100) NOT NULL,
    previous_state VARCHAR(100),
    pipeline_id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    stage_retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    error_stage VARCHAR(100),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pipeline_state ON ai_platform.pipeline_states(current_state);
CREATE INDEX idx_pipeline_tenant ON ai_platform.pipeline_states(tenant_id);
```

---

# 5. Knowledge Processing State Machine

## 5.1 Knowledge Object States

```
              ┌──────────────────────────────────────┐
              │                                      │
              ▼                                      │
        ┌──────────┐                                 │
        │ EXTRACTED│                                 │
        └────┬─────┘                                 │
             │                                       │
             ▼                                       │
        ┌──────────┐                                 │
        │NORMALIZED│                                 │
        └────┬─────┘                                 │
             │                                       │
             ▼                                       │
        ┌───────────┐                                │
        │ VALIDATED │                                │
        └─────┬─────┘                                │
              │                                      │
              ▼                                      │
        ┌──────────┐                                 │
        │ PERSISTED│                                 │
        └────┬─────┘                                 │
             │                                       │
             ▼                                       │
        ┌────────────┐                               │
        │ ARTICLES_  │                               │
        │ GENERATED  │                               │
        └─────┬──────┘                               │
              │                                      │
              ▼                                      │
        ┌──────────┐                                 │
        │EMBEDDED  │                                 │
        └────┬─────┘                                 │
             │                                       │
             ▼                                       │
        ┌──────────┐                                 │
        │ FINISHED │                                 │
        └──────────┘                                 │
                                                     │
        ┌──────────┐                                 │
        │  FLAGGED │─────────────────────────────────┘
        └────┬─────┘   (contradiction / gap found)
             │
             ▼
        ┌───────────┐
        │  REVIEWED │
        └───────────┘
```

## 5.2 State Definitions

| State | Description | Editable |
|-------|-------------|----------|
| EXTRACTED | Knowledge extracted from story, raw | Yes |
| NORMALIZED | Aliases resolved, duplicates merged | Yes |
| VALIDATED | Quality check passed | Limited |
| PERSISTED | Written to knowledge-service database | No |
| ARTICLES_GENERATED | Articles created from this knowledge | No |
| EMBEDDED | Vector embeddings generated | No |
| FINISHED | Complete lifecycle done | No |
| FLAGGED | Contradiction or quality issue detected | Yes |
| REVIEWED | Human reviewed and resolved | No |

## 5.3 Transitions

| From | To | Trigger | Condition | Side Effects |
|------|----|---------|-----------|-------------|
| EXTRACTED | NORMALIZED | KnowledgeNormalized consumed | Normalization complete | Update knowledge object |
| EXTRACTED | FLAGGED | Low confidence (< 0.5) | AI confidence threshold | Notify reviewer |
| NORMALIZED | VALIDATED | KnowledgeValidated consumed | Validation passed (score >= 0.6) | Update knowledge object |
| NORMALIZED | FLAGGED | Validation score < 0.6 | Quality threshold | Notify reviewer |
| VALIDATED | PERSISTED | Write to knowledge-service | Persistence success | Emit KnowledgePersisted |
| VALIDATED | FLAGGED | Contradiction detected | New evidence | Emit ContradictionDetected |
| PERSISTED | ARTICLES_GENERATED | ArticleGenerated consumed | Article creation success | Update pipeline state |
| PERSISTED | FLAGGED | Article generation failed | Non-retryable error | Notify reviewer |
| ARTICLES_GENERATED | EMBEDDED | EmbeddingGenerated consumed | Embedding success | Update pipeline state |
| EMBEDDED | FINISHED | Pipeline completed | All jobs done | Emit PipelineCompleted |
| FLAGGED | REVIEWED | Human review complete | Reviewer action | Update provenance audit |
| FLAGGED | EXTRACTED | Re-extract requested | Reviewer decision | Create new extraction job |
| FLAGGED | NORMALIZED | Re-normalize requested | Reviewer decision | Create new normalization job |
| REVIEWED | FINISHED | All issues resolved | — | Emit PipelineCompleted |
| REVIEWED | EXTRACTED | Re-extract with corrections | Reviewer decision | Create new extraction job |

## 5.4 Knowledge Object Persistence

```sql
CREATE TABLE ai_platform.knowledge_objects (
    knowledge_id UUID PRIMARY KEY,
    canonical_story_id UUID NOT NULL,
    source_id UUID NOT NULL,
    pipeline_id UUID,
    state VARCHAR(50) NOT NULL DEFAULT 'extracted',
    version INTEGER NOT NULL DEFAULT 1,
    quality_score DECIMAL(4,3),
    confidence_score DECIMAL(4,3),
    completeness_score DECIMAL(4,3),
    consistency_score DECIMAL(4,3),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ai_platform.knowledge_flags (
    flag_id UUID PRIMARY KEY,
    knowledge_id UUID NOT NULL REFERENCES ai_platform.knowledge_objects(knowledge_id),
    flag_type VARCHAR(100) NOT NULL,  -- low_confidence, contradiction, research_gap, missing_data
    severity VARCHAR(20) NOT NULL,    -- low, medium, high
    description TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT false,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

# 6. Article Generation State Machine

## 6.1 Article States

```
              ┌───────────────────────────────────┐
              │                                   │
              ▼                                   │
        ┌──────────┐                              │
        │REQUESTED │                              │
        └────┬─────┘                              │
             │                                    │
             ▼                                    │
        ┌────────────┐                            │
        │ GENERATING │                            │
        └──────┬─────┘                            │
               │                                  │
               ▼                                  │
        ┌──────────┐                              │
        │ GENERATED│                              │
        └────┬─────┘                              │
             │                                    │
             ▼                                    │
        ┌──────────┐                              │
        │  DRAFT   │                              │
        └────┬─────┘                              │
             │                                    │
             ▼                                    │
        ┌───────────┐                             │
        │  REVIEW   │                             │
        └─────┬─────┘                             │
              │                                   │
        ┌─────┴─────┐                             │
        ▼           ▼                             │
   ┌────────┐ ┌──────────┐                       │
   │APPROVED│ │ REJECTED │                       │
   └────┬───┘ └─────┬────┘                       │
        │           │                            │
        ▼           └──────────► DRAFT           │
   ┌───────────┐                                  │
   │ PUBLISHED │                                  │
   └─────┬─────┘                                  │
         │                                        │
         ▼                                        │
   ┌──────────┐                                   │
   │ ARCHIVED │                                   │
   └──────────┘                                   │
                                                  │
        ┌──────┐                                  │
        │FAILED│──────────────────────────────────┘
        └──────┘
```

## 6.2 State Definitions

| State | Description | Editable | Published |
|-------|-------------|----------|-----------|
| REQUESTED | Article generation requested, not yet started | No | No |
| GENERATING | AI provider is generating the article | No | No |
| GENERATED | AI response received, article created | No | No |
| DRAFT | Article is in draft, can be edited | Yes | No |
| REVIEW | Submitted for editorial review | No | No |
| APPROVED | Passed editorial review | No | No |
| REJECTED | Failed editorial review | Yes | No |
| PUBLISHED | Article is live | No | Yes |
| ARCHIVED | Removed from publication | No | Previously |
| FAILED | Generation failed after retries | N/A | No |

## 6.3 Transitions

| From | To | Trigger | Condition | Side Effects |
|------|----|---------|-----------|-------------|
| REQUESTED | GENERATING | Worker acquires job | — | Update started_at |
| REQUESTED | FAILED | Queue message lost | Timeout | Notify operator |
| GENERATING | GENERATED | AI response received | Quality score >= 0.5 | Log token usage, cost |
| GENERATING | REQUESTED | Transient error | Retry eligible | Re-queue |
| GENERATING | FAILED | Non-retryable error | Schema, hallucination | Send to DLQ |
| GENERATED | DRAFT | Store article in DB | — | Emit ArticleGenerated |
| DRAFT | REVIEW | Editor submits for review | — | Emit ReviewRequested |
| DRAFT | FAILED | Editor discards draft | — | Archive |
| REVIEW | APPROVED | Reviewer approves | — | Emit ReviewApproved |
| REVIEW | REJECTED | Reviewer rejects | — | Emit ReviewRejected |
| APPROVED | PUBLISHED | Publication action | — | Emit PublicationRequested |
| APPROVED | DRAFT | Unapprove | Admin action | — |
| REJECTED | DRAFT | Editor resubmits | Changes made | — |
| PUBLISHED | ARCHIVED | Archive action | — | Emit ArticleArchived |
| PUBLISHED | DRAFT | Unpublish | Admin action | Emit ArticleArchived |
| FAILED | REQUESTED | Retry requested | Operator action | Create new job |

## 6.4 Article Persistence

```sql
CREATE TABLE ai_platform.article_drafts (
    article_draft_id UUID PRIMARY KEY,
    canonical_story_id UUID NOT NULL,
    knowledge_id UUID NOT NULL,
    source_id UUID NOT NULL,
    pipeline_id UUID,
    article_type VARCHAR(50) NOT NULL,  -- narrative, knowledge, news, creative
    state VARCHAR(50) NOT NULL DEFAULT 'requested',
    title VARCHAR(500),
    language VARCHAR(10) NOT NULL DEFAULT 'id',
    word_count INTEGER,
    quality_score DECIMAL(4,3),
    model_used VARCHAR(100),
    prompt_version VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    execution_cost DECIMAL(10,6),
    storage_url VARCHAR(1000),
    review_id UUID,
    published_article_id UUID,
    version INTEGER NOT NULL DEFAULT 1,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

# 7. Failure Handling

## 7.1 Failure Classification

| Category | Code | Description | Retryable | Examples |
|----------|------|-------------|-----------|----------|
| **transient** | T-001 | AI provider rate limit | Yes | 429 Too Many Requests |
| **transient** | T-002 | AI provider unavailable | Yes | 503 Service Unavailable |
| **transient** | T-003 | Network timeout | Yes | Connection reset, DNS failure |
| **transient** | T-004 | Database connection failure | Yes | PostgreSQL connection refused |
| **transient** | T-005 | Queue unavailable | Yes | Redpanda broker down |
| **schema** | S-001 | Payload validation failure | No | Missing required field |
| **schema** | S-002 | Schema registry mismatch | No | Incompatible schema evolution |
| **schema** | S-003 | Unknown event type | No | Producer sends unregistered type |
| **business_logic** | B-001 | Invalid state transition | No | Job already completed |
| **business_logic** | B-002 | Missing reference data | No | Source not found in DB |
| **business_logic** | B-003 | Empty AI output | Partial | AI returns empty response |
| **business_logic** | B-004 | Malformed AI output | Partial | Invalid JSON, wrong structure |
| **business_logic** | B-005 | Hallucination detected | No | Provenance check failed |
| **business_logic** | B-006 | Quality score below threshold | Partial | Score < 0.3 |
| **poison** | P-001 | Corrupt message | No | Binary data in text field |
| **poison** | P-002 | Unprocessable payload | No | Infinite loop detected |
| **poison** | P-003 | Size exceeds limit | No | 100MB message in 10MB topic |

## 7.2 Provider Failure Handling

### Rate Limit (429)

```
Detection: HTTP 429 response from AI provider
Action:
  1. Check Retry-After header (default: 60s)
  2. Log: provider={provider}, model={model}, retry_after={seconds}
  3. Route to RETRYING state
  4. Set next_retry_at = now() + Retry-After + jitter(0-10s)
  5. On next retry: try same provider or failover to alternate
```

### Timeout

```
Detection: Provider call exceeds timeout (default: 120s)
Action:
  1. Cancel provider request
  2. Log: provider={provider}, model={model}, timeout_after={timeout}s
  3. Route to RETRYING state
  4. Failover to alternate provider on next retry
  5. Reduce max_tokens by 20% if timeout persists
```

### Provider Unavailable (5xx)

```
Detection: HTTP 500/502/503 from AI provider
Action:
  1. Log: provider={provider}, status_code={code}
  2. Route to RETRYING state
  3. Failover to alternate provider immediately
  4. Circuit breaker: if 3 consecutive 5xx from same provider,
     mark as DEGRADED for 5 minutes
```

### Provider Failover Order

```
Primary:   gemini-2.5-pro
Secondary: claude-sonnet-4
Tertiary:  gpt-4o

On each retry, rotate through providers:
  Retry 1: gemini → claude → gpt-4o
  Retry 2: claude → gpt-4o → gemini
  Retry 3: gpt-4o → gemini → claude
  Retry 4: gemini → claude → gpt-4o
  Retry 5: claude → gpt-4o → gemini
```

## 7.3 Malformed Output Handling

### Invalid JSON

```python
def handle_malformed_output(response_text: str, retry_count: int):
    if retry_count < 3:
        # Retry with stricter prompt
        return RetryAction(
            reason="invalid_json",
            new_temperature=0.0,  # Deterministic mode
            add_instruction="Respond with valid JSON only. No markdown, no explanation."
        )
    else:
        # Route to manual review
        return ManualReviewAction(
            reason="persistent_malformed_output",
            severity="high"
        )
```

### Schema Violation

```python
def handle_schema_violation(validation_errors: list, retry_count: int):
    if retry_count < 2:
        return RetryAction(
            reason="schema_violation",
            add_instruction=f"Fix these schema issues: {validation_errors}"
        )
    else:
        return DlqAction(
            reason="persistent_schema_violation",
            errors=validation_errors
        )
```

## 7.4 Partial Success Handling

Some stages may succeed partially. The system MUST handle partial success gracefully.

### Partial Extraction (Some types extracted, some failed)

```
Scenario: Knowledge extraction extracts entities and themes but fails on rituals.
Action:
  1. Emit KnowledgeExtracted with partial results
  2. Include warnings array: [{type: "extraction_failed", target: "rituals", ...}]
  3. Set knowledge state to EXTRACTED (not failed)
  4. Downstream stages process available data
  5. Missing types are flagged for later enrichment
```

### Partial Batch (Embeddings, some targets succeed, some fail)

```
Scenario: 10/12 embedding targets succeed, 2 fail.
Action:
  1. Emit EmbeddingGenerated with successCount=10, failedCount=2
  2. Include failed items in results with error info
  3. Orchestration creates a new embedding job for failed items only
  4. Max 3 retry attempts for failed items
```

## 7.5 Circuit Breaker

A circuit breaker protects the system from cascading failures when an AI provider is degraded.

```
States:
  CLOSED:   Normal operation, requests pass through
  OPEN:     Provider degraded, requests blocked (failover to alternate)
  HALF_OPEN: Testing if provider has recovered

Transitions:
  CLOSED → OPEN:   3 consecutive failures within 5 minutes
  OPEN → HALF_OPEN: After 5 minutes cooldown
  HALF_OPEN → CLOSED: 1 successful request
  HALF_OPEN → OPEN: 1 failure during half-open
```

**Circuit breaker data:**
```sql
CREATE TABLE ai_platform.provider_circuit_breakers (
    provider VARCHAR(100) PRIMARY KEY,
    state VARCHAR(20) NOT NULL DEFAULT 'closed',  -- closed, open, half_open
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_failure_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    half_open_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ
);
```

---

# 8. Human Review Workflow

## 8.1 Review Queue

When a job enters the `MANUAL_REVIEW` state, an entry is created in the review queue:

```sql
CREATE TABLE ai_platform.review_queue (
    review_id UUID PRIMARY KEY,
    pipeline_id UUID NOT NULL,
    job_id UUID NOT NULL,
    source_id UUID,
    target_type VARCHAR(100) NOT NULL,
        -- story_extraction, knowledge_extraction, normalization,
        -- validation, article_generation, transcript_import, metadata_import
    target_id UUID NOT NULL,
    review_reason VARCHAR(100) NOT NULL,
        -- low_quality, missing_transcript, extraction_failure,
        -- schema_violation, hallucination_detected, contradiction,
        -- unresolved_ambiguity, manual_upload_required
    severity VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    description TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}',  -- relevant data for reviewer
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
        -- pending, assigned, in_review, resolved, rejected
    assigned_to UUID,                  -- reviewer user ID
    assigned_at TIMESTAMPTZ,
    resolved_by UUID,
    resolution VARCHAR(100),           -- approve, reject, restart, edit
    resolution_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_review_queue_status ON ai_platform.review_queue(status, severity);
CREATE INDEX idx_review_queue_pipeline ON ai_platform.review_queue(pipeline_id);
```

## 8.2 Review Process

```
1. Job enters MANUAL_REVIEW state
2. Review queue entry created with context data
3. Notification sent to reviewer (email, Slack, in-app)
4. Reviewer opens review dashboard
5. Reviewer inspects the artifact:
   - For story extraction: view transcript + extracted story side-by-side
   - For knowledge extraction: view extracted entities with source evidence
   - For article generation: view article draft
   - For validation: view quality scores + warnings
6. Reviewer takes action:
   
   APPROVE:
   - Artifact accepted as-is
   - Pipeline continues to next stage
   - Event emitted with `manual_review=true`
   
   REJECT:
   - Artifact rejected
   - Job moves to FAILED state
   - Source pipeline moves to REVIEW_NEEDED or FAILED
   - Rejection reason + feedback stored
   
   EDIT:
   - Reviewer modifies artifact inline
   - Modified artifact saved
   - Pipeline continues with modified version
   - Original + edit both stored for audit
   
   RESTART:
   - Pipeline returns to previous stage
   - New job created with modified config (e.g., different prompt)
   - Review notes passed as context
```

## 8.3 Approval Criteria

| Stage | Auto-Approval Threshold | Manual Review Required |
|-------|------------------------|----------------------|
| Story Extraction | Quality >= 0.8 | Quality < 0.6 or any hallucination flag |
| Knowledge Extraction | Confidence >= 0.7 | Confidence < 0.5 or contradictions detected |
| Knowledge Normalization | Ambiguity resolved >= 90% | Unresolved ambiguities |
| Knowledge Validation | Score >= 0.8, no high warnings | Score < 0.6 or high severity warnings |
| Article Generation | Quality >= 0.75 | Quality < 0.6 or factual accuracy concern |

## 8.4 Reprocessing

When a reviewer chooses RESTART, the pipeline reprocesses with modifications:

```python
def restart_pipeline(review: ReviewQueueEntry, modifications: dict):
    job = get_job(review.job_id)
    
    if review.target_type == 'story_extraction':
        new_job = create_job(
            job_type='story_extraction',
            aggregate_id=job.aggregate_id,
            config={
                'prompt_version': modifications.get('prompt_version', job.prompt_version),
                'model': modifications.get('model', job.current_provider),
                'temperature': modifications.get('temperature', 0.3),
                'review_notes': review.resolution_notes
            }
        )
        transition_pipeline_state(job.aggregate_id, 'STORY_EXTRACTION_PENDING')
        publish_event('CanonicalStoryExtractionRequested', new_job)
    
    elif review.target_type == 'knowledge_extraction':
        new_job = create_job(
            job_type='knowledge_extraction',
            aggregate_id=job.aggregate_id,
            config={
                'extraction_types': modifications.get('extraction_types'),
                'model': modifications.get('model', job.current_provider),
                'review_notes': review.resolution_notes
            }
        )
        transition_pipeline_state(job.aggregate_id, 'KNOWLEDGE_EXTRACTION_PENDING')
        publish_event('KnowledgeExtractionRequested', new_job)
```

## 8.5 Rollback

Rollback reverses the pipeline to a previous state.

```
Trigger: Manual operator action or automated quality gate failure

Rollback levels:
  Level 1 (Article): Unpublish article, return to DRAFT state
  Level 2 (Knowledge): Remove knowledge from DB, return to EXTRACTED state
  Level 3 (Story): Delete story, return to TRANSCRIPT_READY state
  Level 4 (Source): Delete all artifacts, return to METADATA_READY state

Implementation:
  1. Create rollback job in ai_platform.jobs
  2. Execute cleanup queries per level
  3. Update pipeline_state to target state
  4. Emit PipelineRollback event
  5. Log in audit trail
```

---

# 9. Recovery Strategy

## 9.1 Recovery Operations

| Operation | Scope | When to Use | Command |
|-----------|-------|-------------|---------|
| **Restart** | Single job | Job failed, operator wants to retry as-is | `restart_job(job_id)` |
| **Replay** | Single message | DLQ message needs reprocessing | `redpanda-replay --dlq {topic}.dlq --topic {topic}` |
| **Rehydrate** | Source pipeline | Pipeline stuck, rebuild state from DB | `rehydrate_pipeline(source_id)` |
| **Backfill** | Bulk reprocess | Schema change or prompt update | `backfill_pipeline --source-type youtube --stage extraction` |

## 9.2 Restart

Restart creates a new job for a failed or cancelled job and publishes it to the queue.

```python
def restart_job(job_id: UUID) -> Job:
    original_job = get_job(job_id)
    
    new_job = Job(
        job_id=uuid4(),
        job_type=original_job.job_type,
        correlation_id=original_job.correlation_id,
        aggregate_id=original_job.aggregate_id,
        aggregate_type=original_job.aggregate_type,
        pipeline_id=original_job.pipeline_id,
        status='submitted',
        retry_count=0,
        max_retries=original_job.max_retries,
        metadata={
            'restarted_from': str(job_id),
            'original_error': original_job.error_message
        }
    )
    
    insert_job(new_job)
    publish_to_topic(new_job)
    
    log_audit(
        action='job_restart',
        job_id=job_id,
        new_job_id=new_job.job_id,
        reason='operator_initiated'
    )
    
    return new_job
```

**CLI:**
```bash
# Restart a specific job
ai-cli jobs restart --job-id e5f6a7b8-c901-2def-3456-789012345678

# Restart all failed jobs for a source
ai-cli jobs restart --source-id b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e

# Restart all failed jobs of a type
ai-cli jobs restart --job-type story_extraction --limit 50
```

## 9.3 Replay

Replay moves messages from a DLQ topic back to the source topic.

```bash
# Replay all messages from DLQ
redpanda-replay \
  --dlq story.extraction.requested.dlq \
  --topic story.extraction.requested \
  --bootstrap localhost:9092

# Replay a single message by eventId
redpanda-replay \
  --dlq knowledge.validated.dlq \
  --topic knowledge.validated \
  --message-id 3a1b2c3d-4e5f-6789-abcd-ef0123456789

# Replay with rate limiting (10 msg/s)
redpanda-replay \
  --dlq source.submitted.dlq \
  --topic source.submitted \
  --rate-limit 10
```

**Automated Replay for Schema Fixes:**
```bash
# After deploying a schema compatibility fix, replay all schema failures
ai-cli dlq replay --failure-type schema --topic source.submitted
```

## 9.4 Rehydrate

Rehydrate rebuilds pipeline state from the database when a pipeline is stuck due to missed events or state corruption.

```python
def rehydrate_pipeline(source_id: UUID) -> PipelineState:
    """
    Rebuild pipeline state by scanning the most recent events and job results.
    """
    # 1. Check what stages have completed
    stages = {
        'metadata': check_metadata_exists(source_id),
        'transcript': check_transcript_exists(source_id),
        'story': check_story_exists(source_id),
        'knowledge': check_knowledge_exists(source_id),
        'validation': check_validation_exists(source_id),
        'articles': check_articles_exist(source_id),
        'embeddings': check_embeddings_exist(source_id),
        'graph': check_graph_exists(source_id),
    }
    
    # 2. Determine the next uncompleted stage
    pipeline_order = [
        'metadata', 'transcript', 'story', 'knowledge',
        'validation', 'articles', 'embeddings', 'graph'
    ]
    
    last_completed = None
    for stage in pipeline_order:
        if stages[stage]:
            last_completed = stage
        else:
            break
    
    # 3. Transition to the correct state
    state_map = {
        None: 'METADATA_PENDING',
        'metadata': 'TRANSCRIPT_PENDING',
        'transcript': 'STORY_EXTRACTION_PENDING',
        'story': 'KNOWLEDGE_EXTRACTION_PENDING',
        'knowledge': 'NORMALIZATION_PENDING',
        'validation': 'ARTICLES_PENDING',
        'articles': 'EMBEDDINGS_PENDING',
        'embeddings': 'GRAPH_PENDING',
        'graph': 'COMPLETED',
    }
    
    target_state = state_map[last_completed]
    update_pipeline_state(source_id, target_state)
    
    # 4. If there's an uncompleted stage, trigger it
    if last_completed and last_completed != 'graph':
        trigger_next_stage(source_id, last_completed)
    
    return get_pipeline_state(source_id)
```

**CLI:**
```bash
# Rehydrate a single source pipeline
ai-cli pipelines rehydrate --source-id b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e

# Rehydrate all stuck pipelines (not COMPLETED/FAILED, no recent activity)
ai-cli pipelines rehydrate --stuck --older-than 24h
```

## 9.5 Backfill

Backfill reprocesses sources through a specific pipeline stage, typically after a prompt update or model improvement.

```bash
# Backfill all sources through story extraction with new prompt
ai-cli pipelines backfill \
  --stage extraction \
  --prompt-version story-extraction-v4 \
  --model gemini-2.5-pro \
  --limit 100

# Backfill specific sources
ai-cli pipelines backfill \
  --stage normalization \
  --source-ids source1.txt  # file with UUIDs, one per line

# Backfill with dry-run (show what would be done)
ai-cli pipelines backfill \
  --stage validation \
  --older-than 2026-01-01 \
  --dry-run
```

**Backfill process:**
```
1. Query sources matching criteria (source type, date range, stage completed)
2. For each source:
   a. Rollback pipeline to target stage
   b. Create new job for target stage
   c. Publish job message to queue
   d. Log in audit trail with backfill_id
3. Monitor: all backfill jobs share a correlation_id prefix
```

---

# 10. Operational Runbooks

## 10.1 Incident Response: Consumer Down

**Symptoms:**
- Alert: `ConsumerDown` for an AI worker.
- Queue depth increasing for the topic the consumer subscribes to.
- Pipeline jobs stuck in `QUEUED` state.

**Severity:** Critical

**Response Steps:**

```
1. ACKNOWLEDGE the alert (within 5 minutes)
2. CHECK consumer status:
   kubectl get pods -n ai-platform | grep extraction-service
   
3. DIAGNOSE:
   kubectl logs -n ai-platform pod/extraction-service-xxx --tail 100
   Check for OOMKilled, CrashLoopBackOff, or other errors
   
4. RESTART (if crash loop):
   kubectl rollout restart deployment/extraction-service -n ai-platform
   
5. SCALE (if overloaded):
   kubectl scale deployment/extraction-service -n ai-platform --replicas=5
   
6. VERIFY recovery:
   Check consumer group lag:
   rpk group describe extraction-story
   Lag should start decreasing
   
7. MONITOR for 10 minutes:
   - Lag returning to 0
   - No new crash loops
   - Pipeline jobs transitioning out of QUEUED

8. POST-MORTEM:
   - Determine root cause (OOM, bug, config change)
   - Update deployment config if needed
   - Add alert if missing
```

**Escalation:** If consumer cannot be restored within 15 minutes, escalate to Platform Engineering team.

---

## 10.2 Incident Response: Stuck Jobs

**Symptoms:**
- Jobs in `PROCESSING` or `WAITING_PROVIDER` state for > 30 minutes.
- No worker actively processing the job.
- Pipeline state not advancing.

**Severity:** High

**Response Steps:**

```
1. IDENTIFY stuck jobs:
   SELECT job_id, job_type, status, started_at
   FROM ai_platform.jobs
   WHERE status IN ('processing', 'waiting_provider')
     AND started_at < now() - interval '30 minutes'
   ORDER BY started_at;
   
2. CHECK if worker is hung:
   kubectl logs -n ai-platform deployment/orchestration-service --tail 50
   Look for last processed event, check if consumer is still alive
   
3. FORCE FAIL the stuck job:
   ai-cli jobs fail --job-id {job_id} --reason "stuck_for_30min"
   
4. CHECK pipeline state:
   SELECT current_state FROM ai_platform.pipeline_states
   WHERE source_id = '{source_id}';
   
5. RESTART if needed:
   ai-cli jobs restart --job-id {original_job_id}
   
6. MONITOR new job for normal progression:
   - Should transition to QUEUED → PROCESSING within seconds
   - Should complete or show progress within expected duration
   
7. INVESTIGATE root cause:
   - Was there a provider timeout without proper handling?
   - Was there a network partition?
   - Did the consumer crash without releasing the message?
```

**Prevention:** Implement `max_processing_time` per job type. If exceeded, auto-fail the job.

---

## 10.3 Incident Response: Retry Storms

**Symptoms:**
- Large number of jobs entering `RETRYING` state simultaneously.
- AI provider returning 429 for all requests.
- Circuit breakers tripping for all providers.
- Logs filled with retry messages.

**Severity:** High

**Response Steps:**

```
1. PAUSE retry queue (stop publishing retry messages):
   ai-cli queues pause --topic story.extraction.requested
   ai-cli queues pause --topic knowledge.extraction.requested
   (Pause all 'requested' topics)
   
2. CHECK provider status:
   - Gemini: https://status.cloud.google.com/
   - Claude: https://status.anthropic.com/
   - OpenAI: https://status.openai.com/
   
3. CHECK circuit breaker states:
   SELECT * FROM ai_platform.provider_circuit_breakers;
   
4. FAILOVER: If primary provider is down, switch to alternate:
   ai-cli providers set-primary --provider claude-sonnet-4
   
5. DRAIN retry queue: Let existing retries complete or fail
   Wait 10 minutes for retry backoff to clear
   
6. RESUME queue:
   ai-cli queues resume --topic story.extraction.requested
   
7. MONITOR:
   - Retry rate should normalize
   - Circuit breakers should close
   - Jobs should start completing
   
8. If storm persists, THROTTLE:
   ai-cli queues throttle --topic story.extraction.requested --max-concurrent 10
```

**Prevention:**
- Implement per-provider rate limiting (max 100 RPM per provider).
- Circuit breaker opens after 3 consecutive failures.
- Retry jitter prevents thundering herd.

---

## 10.4 Incident Response: Queue Backlog

**Symptoms:**
- High consumer lag for one or more topics.
- Alert: `HighConsumerLag` (>1000) or `CriticalConsumerLag` (>5000).
- Processing latency increasing for end users.

**Severity:** Varies (Warning at 1000, Critical at 5000)

**Response Steps:**

```
1. ASSESS backlog:
   for topic in source.submitted story.extraction.requested knowledge.validated; do
     echo "=== $topic ==="
     rpk group describe $(rpk group list | grep $topic | awk '{print $1}')
   done
   
2. IDENTIFY bottleneck:
   - Which topic has the highest lag?
   - Which consumer group is falling behind?
   - Is the consumer processing slower than the producer?
   
3. SCALE consumer:
   kubectl scale deployment/extraction-service -n ai-platform --replicas=10
   
   Note: Scaling is only effective if partitions > replicas.
   If partitions == 3, max 3 consumers in the same group.
   
4. INCREASE partitions (if consistently backlogged):
   rpk topic alter story.extraction.requested --partitions 12
   
   Note: Partition count can only be increased, never decreased.
   This requires re-deploying consumers with updated partition count.
   
5. PRIORITIZE messages:
   Not natively supported in Kafka/Redpanda.
   Workaround: Create high-priority topics for urgent sources.
   
6. MONITOR lag decreasing:
   watch 'rpk group describe extraction-story'
   
7. RESCALE down after backlog clears:
   kubectl scale deployment/extraction-service -n ai-platform --replicas=3
```

**Prevention:**
- Right-size partitions during initial deployment (6 for high-throughput topics).
- Auto-scaling based on consumer lag (HPA with custom metrics).
- Alert at lower thresholds so action is taken before critical.

---

## 10.5 Operational Runbook: DLQ Management

**Scheduled Task (Daily):**
```bash
# Check DLQ topics for accumulated messages
for topic in $(rpk topic list | grep .dlq); do
  lag=$(rpk topic describe $topic | grep -E 'total\.(records|messages)' | awk '{print $2}')
  if [ "$lag" -gt 0 ]; then
    echo "WARNING: $topic has $lag messages"
  fi
done
```

**Response to DLQ Accumulation:**
```
1. REVIEW DLQ messages:
   rpk consume source.submitted.dlq --num=10
   
2. CLASSIFY failures:
   - Schema violations: Fix schema or producer, then replay
   - Business logic errors: Fix code, then replay
   - Transient (DLQ due to max retries): Usually safe to replay
   - Poison messages: Delete, cannot be processed
   
3. REPLAY (for retryable failures):
   redpanda-replay --dlq source.submitted.dlq --topic source.submitted
   
4. DELETE (for poison messages):
   rpk topic delete source.submitted.dlq
   # Topic will be recreated by create-topics.sh
```

---

## 10.6 Operational Runbook: Provider Circuit Breaker Recovery

**Symptoms:**
- Circuit breaker in OPEN state for a provider.
- All jobs failing over to alternate providers.
- Increased latency due to failover overhead.

**Response:**
```
1. CHECK circuit breaker:
   SELECT * FROM ai_platform.provider_circuit_breakers;
   
2. VERIFY provider status:
   - Check provider status page
   - Make test API call
   
3. MANUALLY RESET if provider recovered:
   ai-cli providers reset-circuit-breaker --provider gemini
   
4. MONITOR for 5 minutes:
   - Circuit breaker should stay CLOSED
   - No new failures on this provider
   
5. If circuit breaker trips again immediately:
   - Provider is still degraded
   - Wait for provider incident resolution
   - Check: has our API key been rate limited?
```

---

## 10.7 Operational Runbook: Pipeline Health Check

**Regular Checks (Every Shift):**

```sql
-- Check for stuck pipelines
SELECT source_id, current_state, updated_at
FROM ai_platform.pipeline_states
WHERE current_state NOT IN ('COMPLETED', 'FAILED', 'CANCELLED')
  AND updated_at < now() - interval '4 hours'
ORDER BY updated_at;

-- Check for high retry counts
SELECT job_id, job_type, retry_count, error_message
FROM ai_platform.jobs
WHERE status = 'retrying'
  AND retry_count > 3
ORDER BY retry_count DESC;

-- Check for review queue items
SELECT review_id, target_type, severity, created_at
FROM ai_platform.review_queue
WHERE status = 'pending'
ORDER BY severity, created_at;

-- Check job success rate (last 24 hours)
SELECT 
  job_type,
  COUNT(*) AS total,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
  SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
FROM ai_platform.jobs
WHERE created_at > now() - interval '24 hours'
GROUP BY job_type;
```

**Automated Health Dashboard (Grafana):**

```
Panel: Pipeline Health
  Row 1: Total active pipelines, Completed (24h), Failed (24h), Stuck
  Row 2: Jobs by status (stacked bar chart)
  Row 3: Provider success rate (per provider, per model)
  Row 4: Average processing time per stage
  Row 5: Retry storm detection (retry_rate > 10/min = alert)
  Row 6: Review queue depth (pending items by severity)
  Row 7: DLQ accumulation (messages per DLQ topic)
```

---

# References

- **ADR-004:** Event-Driven Architecture with Transactional Outbox
- **ADR-009:** AI Pipeline Integration
- **PRD.md:** AI Platform Product Requirements Document
- **docs/ai-platform/domain-event-catalog.md:** AI Platform Domain Event Catalog
- **docs/ai-platform/queue-contract-specification.md:** AI Platform Queue Contract Specification
- **docs/workflows/state-machine-specification.md:** Platform State Machine Specification
- **services/workflow-service:** Workflow service implementation
- **services/knowledge-service:** Knowledge service implementation
- **services/content-service:** Content service implementation