# ADR-004: Queue-Driven AI Platform — No REST, Events Only

# Status

Accepted

# Context

## Business Context

The AI Platform is the intelligence engine of The Living Atlas of Indonesian Mystery Culture. It transforms raw transcripts into canonical stories, knowledge objects, claims, articles, and embeddings. These operations are computationally expensive, involve calls to external AI providers (Gemini, Claude, OpenAI), and can take anywhere from 30 seconds to several minutes per operation.

The AI Platform is not user-facing. It is an internal processing platform. Users never interact with it directly. All AI processing is triggered by events from the backend domain services (content-service, knowledge-service, workflow-service) and results are consumed by the backend and projection workers.

The platform must process 100,000 stories, 10,000,000 transcript segments, and 1,000,000 knowledge objects. Each story may require 5–10 AI operations (extraction, normalization, validation, article generation, embedding generation). This means millions of AI operations over the platform's lifetime.

## Technical Context

The AI Platform consists of 7 Python services:

| Service | Purpose |
|---------|---------|
| orchestration-service | Pipeline coordination, job scheduling, retry management |
| ingestion-service | Metadata and transcript normalization |
| extraction-service | Canonical story and knowledge extraction via LLMs |
| normalization-service | Entity resolution, alias consolidation, deduplication |
| validation-service | Confidence scoring, schema validation, gap detection |
| article-service | Narrative, knowledge, news, and creative article generation |
| embedding-service | Vector embedding generation for all content types |

These services communicate with external AI providers (Gemini primary, Claude fallback, OpenAI secondary fallback) through a provider abstraction layer. Provider calls can take 10–120 seconds and are subject to rate limits, timeouts, and transient failures.

The backend (Java/Spring Boot modular monolith) publishes events to Redpanda. The AI Platform consumes these events, processes them, writes results to PostgreSQL, and publishes completion events back to Redpanda.

## Constraints

1. **No REST APIs**: The AI Platform PRD explicitly forbids Frontend → AI and Backend → AI REST calls. All communication must be asynchronous through Redpanda.
2. **Stateless workers**: AI workers must not store state in memory. State must reside in PostgreSQL, the queue, or object storage. Workers must be replaceable at any time without data loss.
3. **Idempotent processing**: Every job must support re-execution without data corruption. Duplicate messages must be safely ignored.
4. **Provider agnosticism**: Business logic must never depend on a specific AI provider. The platform must support Gemini, Claude, OpenAI, and future providers through a common interface.
5. **Human review gate**: AI outputs must not be automatically published. Results are written to PostgreSQL in a "review required" state. Only after human approval are projection events emitted.
6. **Cost governance**: Every AI execution must record provider, model, prompt version, token counts, cost, and execution time. Cost analytics must be available per story, article, tenant, workspace, and provider.
7. **99.5% availability**: AI Platform failures must not cause data loss. Processing must resume from the last known good state after recovery.
8. **Backend API performance**: Backend p95 < 300ms, p99 < 1 second. AI processing must not block backend response times. This is only achievable with asynchronous queue-driven processing.

## Problem Statement

How do we architect the AI Platform so that it is fully decoupled from the backend, communicates exclusively through events, handles long-running and failure-prone AI provider calls, scales independently, controls costs, and integrates with the human review workflow — all without exposing any REST endpoints?

# Decision

**The AI Platform exposes no REST APIs. The AI Platform consumes queue messages only. The backend communicates with the AI Platform exclusively through Redpanda events. AI workers write results to PostgreSQL and publish completion events. No synchronous communication path exists between the backend and the AI Platform.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Backend (Java Modular Monolith)                  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Content    │  │  Knowledge   │  │   Workflow   │  │  Research   │  │
│  │   Module     │  │   Module     │  │   Module     │  │   Module    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬─────┘  │
│         │                 │                 │                 │         │
│         ▼                 ▼                 ▼                 ▼         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     PostgreSQL 18                                │   │
│  │  ┌───────────────────────────────────────────────────────────┐  │   │
│  │  │  Transactional Outbox (content_outbox, knowledge_outbox,  │  │   │
│  │  │  workflow_outbox, research_outbox)                        │  │   │
│  │  └──────────────────────────┬────────────────────────────────┘  │   │
│  └─────────────────────────────┼───────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Outbox Publisher                              │   │
│  │  Publishes to Redpanda topics: content.evt, knowledge.evt,      │   │
│  │  workflow.evt, research.evt                                     │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
└─────────────────────────────────┼──────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Redpanda                                       │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Backend → AI Topics                    AI → Backend Topics      │   │
│  │  ──────────────────                    ──────────────────       │   │
│  │  content.evt:                          ai.internal:              │   │
│  │    TranscriptImported                    extraction.completed     │   │
│  │    StoryCreated                          knowledge.extracted      │   │
│  │    StoryVersionCreated                   knowledge.normalized     │   │
│  │                                          knowledge.validated      │   │
│  │  workflow.evt:                           article.generated        │   │
│  │    ReviewApproved                        embedding.generated      │   │
│  │    ReviewRejected                        graph.projected          │   │
│  │                                          pipeline.completed       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       AI Platform (Python Workers)                       │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │   │
│  │  │  Orchestration  │  │   Ingestion     │  │   Extraction    │  │   │
│  │  │  Service        │  │   Service       │  │   Service       │  │   │
│  │  │                 │  │                 │  │                 │  │   │
│  │  │  - Pipeline     │  │  - Metadata     │  │  - Canonical    │  │   │
│  │  │    coordination │  │    normalization│  │    story ext.   │  │   │
│  │  │  - Job tracking │  │  - Transcript   │  │  - Knowledge    │  │   │
│  │  │  - Retry/DLQ    │  │    normalization│  │    extraction   │  │   │
│  │  │  - Progress     │  │  - Language     │  │  - Entity ext.  │  │   │
│  │  │    tracking     │  │    detection    │  │  - Claim ext.   │  │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │   │
│  │                                                                  │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │   │
│  │  │  Normalization  │  │   Validation    │  │   Article       │  │   │
│  │  │  Service        │  │   Service       │  │   Service       │  │   │
│  │  │                 │  │                 │  │                 │  │   │
│  │  │  - Alias        │  │  - Confidence   │  │  - Narrative    │  │   │
│  │  │    resolution   │  │    scoring      │  │    article      │  │   │
│  │  │  - Entity       │  │  - Schema       │  │  - Knowledge    │  │   │
│  │  │    consolidation│  │    validation   │  │    article      │  │   │
│  │  │  - Duplicate    │  │  - Contradiction│  │  - News article │  │   │
│  │  │    detection    │  │    review       │  │  - Creative     │  │   │
│  │  │  - Cultural     │  │  - Gap detection│  │    article      │  │   │
│  │  │    normalization│  │                 │  │                 │  │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │   │
│  │                                                                  │   │
│  │  ┌─────────────────┐  ┌──────────────────────────────────────┐  │   │
│  │  │  Embedding      │  │  AI Provider Abstraction Layer       │  │   │
│  │  │  Service        │  │                                      │  │   │
│  │  │                 │  │  ┌────────┐  ┌────────┐  ┌────────┐ │  │   │
│  │  │  - Story        │  │  │ Gemini │  │ Claude │  │ OpenAI │ │  │   │
│  │  │    embeddings   │  │  │Adapter │  │Adapter │  │Adapter │ │  │   │
│  │  │  - Knowledge    │  │  └────────┘  └────────┘  └────────┘ │  │   │
│  │  │    embeddings   │  └──────────────────────────────────────┘  │   │
│  │  │  - Claim emb.   │                                            │   │
│  │  └─────────────────┘                                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│                                  ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     PostgreSQL 18                                 │   │
│  │                                                                   │   │
│  │  AI Platform tables (ai_ schema):                                 │   │
│  │  - ai_jobs: Job tracking, state machine, retry count              │   │
│  │  - ai_pipeline_runs: Pipeline execution tracking                  │   │
│  │  - ai_cost_log: Per-execution cost tracking                      │   │
│  │  - ai_output: Extracted stories, knowledge, articles (review      │   │
│  │    required state)                                                │   │
│  │  - ai_errors: Detailed error records for debugging                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: No REST Endpoints on AI Platform

The AI Platform must not expose any HTTP endpoints. This includes:

- No REST APIs for triggering AI operations
- No health check endpoints (health is determined by Redpanda consumer group membership and job processing)
- No status query endpoints (status is read from PostgreSQL by the backend)
- No webhook receivers
- No gRPC services

**Enforcement**:
- AI Platform services are not deployed behind a load balancer
- AI Platform containers expose no ports to the backend network
- AI Platform services only connect to Redpanda (consumer), PostgreSQL (read/write), and external AI providers (outbound HTTPS)
- CI/CD pipeline scans for any HTTP server libraries in AI Platform dependencies

**Exception**: Internal health checks for container orchestration (Kubernetes liveness/readiness probes) are allowed but must not be accessible from outside the AI Platform's network namespace.

### Rule 2: All AI Operations Are Triggered by Redpanda Events

Every AI operation must be triggered by consuming a Redpanda event. The event contains all information needed to process the job:

```json
{
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "eventType": "extraction.requested",
  "eventVersion": 1,
  "occurredAt": "2026-06-25T01:00:00.000Z",
  "producer": "orchestration-service",
  "aggregateType": "Transcript",
  "aggregateId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "data": {
    "jobId": "job-001",
    "transcriptId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "transcriptText": "Full transcript text...",
    "metadata": {
      "sourceId": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
      "language": "id",
      "title": "Misteri Kuntilanak di Desa Sukamaju"
    },
    "promptVersion": "CANONICAL_STORY_V1",
    "tenantId": "11111111-2222-3333-4444-555555555555",
    "workspaceId": "66666666-7777-8888-9999-000000000000"
  },
  "metadata": {
    "tenantId": "11111111-2222-3333-4444-555555555555",
    "workspaceId": "66666666-7777-8888-9999-000000000000",
    "correlationId": "cccccccc-dddd-eeee-ffff-aaaaaaaaaaaa",
    "causationId": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
  }
}
```

**Event size consideration**: Transcript text can be large (50KB–500KB). Events containing full transcript text may exceed Redpanda's default message size limit (1MB). Mitigations:
- Set `max.message.bytes` to 2MB on AI Platform topics
- For transcripts exceeding 500KB, store the transcript in PostgreSQL and include only the `transcriptId` in the event. The AI worker reads the transcript from PostgreSQL directly.

### Rule 3: AI Workers Write Results to PostgreSQL

After processing, AI workers write results directly to PostgreSQL. They do not return data through Redpanda events. The completion event only contains metadata (job ID, status, summary).

**Write pattern**:
```python
async def process_extraction_job(job_id, transcript_id, prompt_version):
    try:
        # 1. Update job state to PROCESSING
        await db.execute(
            "UPDATE ai_jobs SET status = 'PROCESSING', started_at = NOW() WHERE id = $1",
            job_id
        )
        
        # 2. Read transcript from PostgreSQL
        transcript = await db.fetch_row(
            "SELECT text, metadata FROM content_transcripts WHERE id = $1",
            transcript_id
        )
        
        # 3. Call AI provider through abstraction layer
        provider = AIProviderFactory.get_provider()
        result = await provider.extract_canonical_story(
            transcript=transcript['text'],
            metadata=transcript['metadata'],
            prompt_version=prompt_version
        )
        
        # 4. Write results to PostgreSQL (review required state)
        story_id = uuid4()
        await db.execute("""
            INSERT INTO ai_output_canonical_stories 
                (id, job_id, transcript_id, story_data, confidence_score, 
                 prompt_version, provider, model, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'REVIEW_REQUIRED', NOW())
        """, story_id, job_id, transcript_id, 
             json.dumps(result['story']), result['confidence'],
             prompt_version, result['provider'], result['model'])
        
        # 5. Record cost
        await db.execute("""
            INSERT INTO ai_cost_log
                (job_id, provider, model, prompt_version,
                 input_tokens, output_tokens, cost, execution_time_ms,
                 tenant_id, workspace_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, job_id, result['provider'], result['model'], prompt_version,
             result['usage']['input_tokens'], result['usage']['output_tokens'],
             result['usage']['cost'], result['execution_time_ms'],
             result['tenant_id'], result['workspace_id'])
        
        # 6. Update job state to COMPLETED
        await db.execute(
            "UPDATE ai_jobs SET status = 'COMPLETED', completed_at = NOW() WHERE id = $1",
            job_id
        )
        
        # 7. Publish completion event to Redpanda
        await redpanda.produce(
            topic="ai.internal",
            key=job_id,
            value={
                "eventId": str(uuid4()),
                "eventType": "extraction.completed",
                "eventVersion": 1,
                "occurredAt": datetime.utcnow().isoformat(),
                "producer": "extraction-service",
                "aggregateType": "Transcript",
                "aggregateId": transcript_id,
                "data": {
                    "jobId": job_id,
                    "storyId": str(story_id),
                    "status": "COMPLETED",
                    "confidenceScore": result['confidence'],
                    "provider": result['provider'],
                    "model": result['model'],
                    "executionTimeMs": result['execution_time_ms'],
                    "cost": result['usage']['cost']
                },
                "metadata": {
                    "tenantId": result['tenant_id'],
                    "workspaceId": result['workspace_id'],
                    "correlationId": correlation_id,
                    "causationId": causation_id
                }
            }
        )
        
    except Exception as e:
        # Handle failure (Rule 6)
        await handle_job_failure(job_id, e)
```

### Rule 4: Stateless Workers with State in PostgreSQL

AI workers must not maintain any in-memory state that cannot be reconstructed. All state must be in PostgreSQL or Redpanda.

**What workers may keep in memory**:
- Configuration (loaded at startup, refreshed periodically)
- Connection pools (database, Redpanda, AI provider SDKs)
- Cached prompt templates (loaded from prompt registry)
- Rate limit state (current token bucket level, next available time)

**What workers must not keep in memory**:
- Job processing state (which jobs are in progress, their results, their status)
- Transcript or content data between restarts
- Provider response data that has not been persisted to PostgreSQL
- Queue offset state (managed by Redpanda consumer groups)

**Worker replacement guarantee**: Any worker can be killed and replaced at any time without data loss. In-flight jobs will be retried (idempotent handling ensures no duplicate data). The new worker will pick up unprocessed events from Redpanda based on consumer group offset.

### Rule 5: Idempotent Job Processing

Every job must be idempotent. The job state machine prevents duplicate processing:

```
                    ┌──────────┐
                    │ SUBMITTED│
                    └────┬─────┘
                         │
                         ▼
                    ┌──────────┐
              ┌─────│  QUEUED  │
              │     └────┬─────┘
              │          │
              │          ▼
              │     ┌───────────┐
              │     │PROCESSING │◄──── Duplicate event: check state,
              │     └─────┬─────┘      if PROCESSING, check deadline
              │           │            if expired, retry; if not, skip
              │     ┌─────┴──────┐
              │     │            │
              │     ▼            ▼
              │  ┌────────┐ ┌──────────┐
              │  │SUCCEEDED│ │  FAILED  │
              │  └────┬───┘ └─────┬────┘
              │       │           │
              │       │      ┌────┴────────┐
              │       │      │             │
              │       │      ▼             ▼
              │       │  ┌────────┐  ┌──────────┐
              │       │  │ RETRY  │  │DEAD LETTER│
              │       │  └───┬────┘  └──────────┘
              │       │      │
              │       │      └──► QUEUED (retry)
              │       │
              │       ▼
              │  ┌──────────┐
              └──│COMPLETED │  ← Final state. Duplicate events are ignored.
                 └──────────┘
```

**Idempotency implementation**:
```python
async def handle_extraction_event(event):
    job_id = event.data['jobId']
    
    # Check current job state
    job = await db.fetch_one(
        "SELECT status, retry_count, started_at FROM ai_jobs WHERE id = $1",
        job_id
    )
    
    if not job:
        # New job — create and process
        await create_job(job_id, event)
        return await process_job(job_id)
    
    if job['status'] == 'COMPLETED':
        # Already done — idempotent skip
        logger.info(f"Job {job_id} already completed, skipping duplicate event")
        return
    
    if job['status'] == 'PROCESSING':
        # Check if the processing deadline has passed
        deadline = job['started_at'] + timedelta(hours=1)
        if datetime.utcnow() < deadline:
            # Still within deadline — another worker is handling this
            logger.info(f"Job {job_id} is being processed by another worker, skipping")
            return
        else:
            # Deadline passed — worker may have crashed, retry
            logger.warning(f"Job {job_id} processing deadline exceeded, retrying")
            await db.execute(
                "UPDATE ai_jobs SET status = 'RETRY', retry_count = retry_count + 1 WHERE id = $1",
                job_id
            )
    
    if job['status'] in ('FAILED', 'RETRY'):
        if job['retry_count'] >= MAX_RETRIES:
            await db.execute(
                "UPDATE ai_jobs SET status = 'DEAD_LETTER' WHERE id = $1",
                job_id
            )
            await publish_to_dlq(job_id, event)
            return
        return await process_job(job_id)
```

### Rule 6: Provider Abstraction Layer

All AI provider calls go through a common abstraction layer. Business logic never calls a provider directly.

```python
class AIProvider(ABC):
    @abstractmethod
    async def extract_canonical_story(self, transcript: str, metadata: dict, prompt_version: str) -> ExtractionResult:
        pass
    
    @abstractmethod
    async def extract_knowledge(self, canonical_story: dict, prompt_version: str) -> KnowledgeResult:
        pass
    
    @abstractmethod
    async def generate_article(self, knowledge: dict, article_type: str, prompt_version: str) -> ArticleResult:
        pass
    
    @abstractmethod
    async def generate_embeddings(self, text: str, model: str) -> EmbeddingResult:
        pass

class GeminiProvider(AIProvider):
    # Implementation using Google Generative AI SDK
    pass

class ClaudeProvider(AIProvider):
    # Implementation using Anthropic SDK
    pass

class OpenAIProvider(AIProvider):
    # Implementation using OpenAI SDK
    pass

class AIProviderFactory:
    _providers = {
        'gemini': GeminiProvider,
        'claude': ClaudeProvider,
        'openai': OpenAIProvider,
    }
    
    _fallback_chain = ['gemini', 'claude', 'openai']
    
    @classmethod
    async def get_provider(cls, preferred: str = None) -> AIProvider:
        providers_to_try = []
        if preferred:
            providers_to_try.append(preferred)
        providers_to_try.extend([p for p in cls._fallback_chain if p != preferred])
        
        for provider_name in providers_to_try:
            provider_class = cls._providers.get(provider_name)
            if not provider_class:
                continue
            provider = provider_class()
            if await provider.is_available():
                return provider
        
        raise AllProvidersUnavailableError("No AI provider is currently available")
```

**Provider failover flow**:
1. Try primary provider (Gemini)
2. If rate limited, timeout, or service unavailable → try fallback (Claude)
3. If fallback also fails → try secondary fallback (OpenAI)
4. If all providers fail → mark job as FAILED, retry with exponential backoff
5. After max retries → move to dead letter queue

### Rule 7: Pipeline Orchestration via Events

The orchestration service coordinates the AI pipeline by consuming completion events and producing the next stage's request events. It does not call workers directly.

```
TranscriptImported (from backend)
    │
    ▼
Orchestration Service
    │
    ├──► produce: extraction.requested
    │
    ▼ (wait for extraction.completed)
    │
    ├──► produce: knowledge.extraction.requested
    │
    ▼ (wait for knowledge.extracted)
    │
    ├──► produce: knowledge.normalization.requested
    │
    ▼ (wait for knowledge.normalized)
    │
    ├──► produce: knowledge.validation.requested
    │
    ▼ (wait for knowledge.validated)
    │
    ├──► produce: article.generation.requested
    │
    ▼ (wait for article.generated)
    │
    ├──► produce: embedding.generation.requested
    │
    ▼ (wait for embedding.generated)
    │
    ├──► produce: graph.projection.requested
    │
    ▼ (wait for graph.projected)
    │
    └──► produce: pipeline.completed (to backend)
```

**Pipeline state tracking**:
```sql
CREATE TABLE ai_pipeline_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id       UUID NOT NULL,
    story_id            UUID,
    
    -- Pipeline state
    current_stage       VARCHAR(50) NOT NULL,  -- TRANSCRIPT_READY, CANONICAL_STORY_READY, etc.
    status              VARCHAR(50) NOT NULL DEFAULT 'RUNNING',  -- RUNNING, COMPLETED, FAILED, CANCELLED
    
    -- Stage tracking
    stages              JSONB NOT NULL DEFAULT '{}',
    -- Example:
    -- {
    --   "extraction":       { "status": "COMPLETED", "jobId": "...", "completedAt": "..." },
    --   "knowledge_extract": { "status": "RUNNING",  "jobId": "...", "startedAt": "..." },
    --   "normalization":    { "status": "PENDING" },
    --   "validation":       { "status": "PENDING" },
    --   "article":          { "status": "PENDING" },
    --   "embedding":        { "status": "PENDING" },
    --   "projection":       { "status": "PENDING" }
    -- }
    
    -- Metadata
    tenant_id           UUID NOT NULL,
    workspace_id        UUID NOT NULL,
    correlation_id      UUID NOT NULL,
    
    -- Timing
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Rule 8: Cost Tracking on Every Execution

Every AI provider call must record cost data. This is not optional — it is a hard requirement for cost governance.

```sql
CREATE TABLE ai_cost_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Job reference
    job_id              UUID NOT NULL REFERENCES ai_jobs(id),
    pipeline_run_id     UUID REFERENCES ai_pipeline_runs(id),
    
    -- Provider details
    provider            VARCHAR(50) NOT NULL,     -- 'gemini', 'claude', 'openai'
    model               VARCHAR(100) NOT NULL,    -- 'gemini-2.0-pro', 'claude-4-opus', etc.
    prompt_version      VARCHAR(100) NOT NULL,    -- 'CANONICAL_STORY_V1'
    
    -- Token usage
    input_tokens        INTEGER NOT NULL,
    output_tokens       INTEGER NOT NULL,
    total_tokens        INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    
    -- Cost (in USD, stored as micro-dollars for precision)
    input_cost_micro    BIGINT NOT NULL,          -- cost in micro-dollars (1/1,000,000)
    output_cost_micro   BIGINT NOT NULL,
    total_cost_micro    BIGINT GENERATED ALWAYS AS (input_cost_micro + output_cost_micro) STORED,
    
    -- Performance
    execution_time_ms   INTEGER NOT NULL,
    provider_latency_ms INTEGER NOT NULL,         -- Time waiting for provider response
    
    -- Tenant isolation
    tenant_id           UUID NOT NULL,
    workspace_id        UUID NOT NULL,
    
    -- Timing
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for cost analytics
CREATE INDEX idx_cost_log_tenant ON ai_cost_log (tenant_id, created_at);
CREATE INDEX idx_cost_log_provider ON ai_cost_log (provider, created_at);
CREATE INDEX idx_cost_log_prompt ON ai_cost_log (prompt_version, created_at);
```

**Cost analytics queries**:
```sql
-- Cost per story
SELECT pipeline_run_id, SUM(total_cost_micro) / 1000000.0 AS total_cost_usd
FROM ai_cost_log
WHERE pipeline_run_id = $1
GROUP BY pipeline_run_id;

-- Cost per tenant per month
SELECT tenant_id, DATE_TRUNC('month', created_at) AS month,
       SUM(total_cost_micro) / 1000000.0 AS total_cost_usd
FROM ai_cost_log
GROUP BY tenant_id, DATE_TRUNC('month', created_at)
ORDER BY month DESC;

-- Cost per provider
SELECT provider, SUM(total_cost_micro) / 1000000.0 AS total_cost_usd,
       COUNT(*) AS total_calls
FROM ai_cost_log
GROUP BY provider
ORDER BY total_cost_usd DESC;
```

### Rule 9: Retry Strategy with Exponential Backoff

AI provider calls are subject to transient failures. The retry strategy handles these without manual intervention.

```python
RETRY_CONFIG = {
    'max_retries': 5,
    'base_delay_seconds': 60,       # Start with 1 minute
    'max_delay_seconds': 3600,      # Cap at 1 hour
    'backoff_multiplier': 3,        # 1min → 3min → 9min → 27min → 81min → DLQ
    'jitter': True,                 # Add random jitter to prevent thundering herd
    
    'retryable_errors': [
        'RateLimitError',
        'TimeoutError',
        'ServiceUnavailable',
        'NetworkError',
        'InternalServerError',       # Provider-side 5xx
    ],
    
    'non_retryable_errors': [
        'InvalidRequestError',       # Bad prompt, invalid parameters
        'AuthenticationError',       # Invalid API key
        'AuthorizationError',        # Insufficient permissions
        'ContentFilterError',        # Content blocked by provider safety filters
        'SchemaValidationError',     # AI output doesn't match expected schema
    ]
}

async def handle_job_failure(job_id: str, error: Exception):
    error_type = type(error).__name__
    
    if error_type in RETRY_CONFIG['non_retryable_errors']:
        # Non-retryable — move to dead letter immediately
        await db.execute(
            "UPDATE ai_jobs SET status = 'DEAD_LETTER', last_error = $1 WHERE id = $2",
            str(error), job_id
        )
        await publish_to_dlq(job_id, error)
        return
    
    if error_type in RETRY_CONFIG['retryable_errors']:
        # Get current retry count
        job = await db.fetch_one(
            "SELECT retry_count FROM ai_jobs WHERE id = $1", job_id
        )
        
        if job['retry_count'] >= RETRY_CONFIG['max_retries']:
            # Max retries exceeded — dead letter
            await db.execute(
                "UPDATE ai_jobs SET status = 'DEAD_LETTER', last_error = $1 WHERE id = $2",
                str(error), job_id
            )
            await publish_to_dlq(job_id, error)
            return
        
        # Calculate delay with exponential backoff and jitter
        delay = min(
            RETRY_CONFIG['base_delay_seconds'] * (RETRY_CONFIG['backoff_multiplier'] ** job['retry_count']),
            RETRY_CONFIG['max_delay_seconds']
        )
        if RETRY_CONFIG['jitter']:
            delay = random.uniform(delay * 0.8, delay * 1.2)
        
        # Schedule retry
        retry_at = datetime.utcnow() + timedelta(seconds=delay)
        await db.execute(
            """UPDATE ai_jobs 
               SET status = 'RETRYING', retry_count = retry_count + 1, 
                   last_error = $1, retry_at = $2
               WHERE id = $3""",
            str(error), retry_at, job_id
        )
        
        # Re-produce the event with a delay (Redpanda does not support native delayed delivery)
        # Alternative: use a separate retry topic with a consumer that respects retry_at
        await redpanda.produce(
            topic="ai.retry",
            key=job_id,
            value=original_event,
            timestamp=retry_at  # Redpanda will make this available for consumption at this time
        )
```

### Rule 10: Human Review Gate

AI outputs are never automatically published. They are written to PostgreSQL in a `REVIEW_REQUIRED` state. Only after human approval are they made available for projection and publication.

```sql
-- All AI output tables use this pattern
CREATE TABLE ai_output_canonical_stories (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id              UUID NOT NULL REFERENCES ai_jobs(id),
    transcript_id       UUID NOT NULL,
    
    story_data          JSONB NOT NULL,           -- The extracted canonical story
    confidence_score    REAL NOT NULL DEFAULT 0.0,
    
    -- Review state
    status              VARCHAR(50) NOT NULL DEFAULT 'REVIEW_REQUIRED',
    -- REVIEW_REQUIRED → APPROVED → PUBLISHED
    -- REVIEW_REQUIRED → REJECTED → (reprocess)
    
    reviewed_by         UUID,                     -- User ID of reviewer
    reviewed_at         TIMESTAMPTZ,
    review_notes        TEXT,
    
    -- Provenance
    prompt_version      VARCHAR(100) NOT NULL,
    provider            VARCHAR(50) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    
    -- Tenant
    tenant_id           UUID NOT NULL,
    workspace_id        UUID NOT NULL,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Review workflow**:
1. AI worker writes result → status = `REVIEW_REQUIRED`
2. Backend workflow-service detects new review-required items (via event or polling)
3. Reviewer reviews the AI output through the frontend
4. Reviewer approves or rejects
5. If approved: status = `APPROVED` → triggers projection events
6. If rejected: status = `REJECTED` → optionally triggers reprocessing with updated prompt

**Projection gate**: Projection workers (Neo4j, Weaviate) only consume events for approved/published content. They never see `REVIEW_REQUIRED` data. This ensures that unverified AI outputs never appear in the knowledge graph or search results.

# Alternatives Considered

## Alternative 1: Backend Calls AI Platform via REST

**Description**: The backend calls the AI Platform directly via REST endpoints. The AI Platform exposes synchronous and asynchronous REST APIs. For long-running operations, the backend polls a status endpoint or receives a callback webhook.

**Advantages**:
- Simplest initial implementation — REST is well-understood and easy to debug
- Immediate feedback for short operations (e.g., simple validation)
- No message broker dependency for AI communication
- Easier to test — curl commands can trigger AI operations directly
- Existing team may have more REST experience than event-driven patterns

**Disadvantages**:
- **Direct violation of AI Platform PRD**: The PRD explicitly forbids Backend → AI Platform REST. This is a hard architectural constraint.
- **Temporal coupling**: Backend HTTP requests to AI Platform would timeout after 30–120 seconds for AI extraction. This would require complex async REST patterns (202 Accepted + polling) that are essentially reimplementing a message queue.
- **Backend thread blocking**: Each AI operation would consume a backend thread while waiting. At 100 concurrent AI operations, the backend's thread pool would be exhausted, degrading user-facing API performance below the p95 < 300ms target.
- **No built-in retry**: REST calls require custom retry logic with exponential backoff, idempotency keys, and dead letter handling. Redpanda provides these natively.
- **No event replay**: If a REST call fails and the data is lost, the entire pipeline must be re-triggered manually. With events, the failed event remains in the queue for retry.
- **Scaling mismatch**: Backend scaling is driven by user traffic. AI Platform scaling is driven by queue depth. REST coupling forces both to scale together, wasting resources.
- **No buffering**: If the AI Platform is down, REST calls fail immediately. With Redpanda, events are buffered until the AI Platform recovers.
- **Provider failover complexity**: If Gemini is rate-limited, the backend would need to retry with Claude. This logic belongs in the AI Platform, not the backend.

**Rejection rationale**: REST communication violates the PRD, introduces temporal coupling that degrades backend performance, lacks built-in retry and buffering, and forces scaling coupling between user-facing and internal systems. The queue-driven approach is architecturally superior for all AI Platform communication.

## Alternative 2: AI Platform Exposes gRPC for Streaming

**Description**: Use gRPC bidirectional streaming for AI Platform communication. The backend opens a gRPC stream to the AI Platform, sends requests, and receives responses asynchronously over the same connection.

**Advantages**:
- Bidirectional streaming enables real-time progress updates
- Strongly typed contracts via Protocol Buffers
- Better performance than REST (binary protocol, HTTP/2 multiplexing)
- Streaming responses for long-running operations
- Built-in deadline propagation and cancellation

**Disadvantages**:
- **Still violates the no-REST principle**: gRPC is still a synchronous communication pattern. The backend must maintain an open connection to the AI Platform, creating temporal coupling.
- **Connection management complexity**: gRPC streams require connection pooling, health checking, and reconnection logic. This adds significant operational complexity.
- **No built-in buffering**: If the AI Platform is down, gRPC connections fail. Events in transit are lost. Redpanda provides buffering.
- **No event replay**: gRPC streams are ephemeral. There is no persistent record of what was sent or received. The transactional outbox provides this.
- **Protocol Buffers schema management**: gRPC requires .proto files and code generation. Event-driven JSON schemas are simpler to evolve and debug.
- **Python gRPC ecosystem maturity**: Python gRPC has known issues with connection management, especially in async contexts. The AI Platform's Python workers would face these issues.
- **Scaling complexity**: gRPC load balancing requires client-side load balancing or a service mesh. Redpanda consumer groups handle load balancing natively.

**Rejection rationale**: gRPC provides better performance than REST but still creates synchronous coupling, lacks buffering and replay capabilities, and adds operational complexity that is not justified. The event-driven approach provides all the benefits of async communication without the connection management overhead.

## Alternative 3: AI Platform as Shared Library Within Backend

**Description**: Instead of a separate AI Platform, integrate AI processing directly into the Java backend as a shared library. Use Spring Boot's `@Async` for asynchronous processing. Call AI providers directly from the backend.

**Advantages**:
- Simplest deployment — single application, no separate AI Platform infrastructure
- No inter-service communication — no events, no REST, no gRPC
- Shared transaction context — AI results are written in the same transaction as business data
- No network latency between backend and AI logic
- No serialization/deserialization overhead

**Disadvantages**:
- **Language mismatch**: AI/ML ecosystem is Python-dominated. Java libraries for LLM integration (LangChain4j, Spring AI) are less mature. WhisperX, Pyannote, and many NLP libraries are Python-only.
- **Resource contention**: AI provider calls are I/O-bound and long-running (10–120 seconds). Running them in the same JVM as user-facing API requests would exhaust thread pools and degrade response times below the p95 < 300ms target.
- **No independent scaling**: AI processing and API serving would share the same JVM resources. Scaling for AI load would also scale the API layer, wasting resources.
- **Failure coupling**: An AI provider SDK crash (e.g., memory leak in the Gemini client) would crash the entire backend. The queue-driven approach isolates AI failures.
- **No provider failover isolation**: If Gemini is rate-limited, the backend's thread pool fills with retries, blocking user requests. With queue-driven architecture, retries happen in the AI Platform without affecting the backend.
- **No cost isolation**: AI processing costs would be mixed with backend operational costs. The separate AI Platform enables dedicated cost tracking and budget management.
- **Deployment coupling**: Updating an AI provider SDK would require redeploying the entire backend. With a separate AI Platform, AI updates are independent.

**Rejection rationale**: Integrating AI processing into the backend creates resource contention, failure coupling, and deployment coupling that are unacceptable for a platform with strict API performance requirements (p95 < 300ms). The language mismatch (Java vs. Python) further reinforces the need for a separate AI Platform.

## Alternative 4: AI Platform with REST for Control, Events for Data

**Description**: Use a hybrid approach: REST endpoints for control operations (trigger processing, check status, cancel jobs) and Redpanda events for data transfer (transcript content, extraction results). The AI Platform exposes a minimal REST API for operational control while using events for the actual data pipeline.

**Advantages**:
- REST provides immediate feedback for control operations (e.g., "is the AI Platform healthy?", "what is the status of job X?")
- Events handle the heavy data transfer, maintaining decoupling for the data path
- Easier operational debugging — operators can curl the AI Platform to check status
- Simpler integration with orchestration tools that expect HTTP endpoints

**Disadvantages**:
- **Still violates the PRD**: The AI Platform PRD says "Forbidden: Backend → AI Platform REST." Any REST endpoint, even for control, creates a path that could be abused.
- **Two communication channels to maintain**: REST for control, events for data. This doubles the integration surface area and testing burden.
- **REST creates implicit coupling**: If the backend calls REST to check job status, it now depends on the AI Platform's availability for read operations. With events-only, the backend reads status from PostgreSQL, which is always available.
- **Security surface area**: REST endpoints require authentication, rate limiting, and input validation. Events-only eliminates this attack surface.
- **No clear boundary**: Once a REST endpoint exists for "check status," it's tempting to add "trigger reprocessing" and "update prompt" endpoints. The REST surface area grows over time.
- **Operational complexity of maintaining both patterns**: The team must maintain expertise in both REST API design and event-driven patterns. Events-only simplifies the architecture.

**Rejection rationale**: The hybrid approach provides marginal operational convenience at the cost of architectural purity, increased security surface area, and potential for REST surface area growth. The events-only approach is simpler, more secure, and fully aligned with the PRD. Status information is available through PostgreSQL, which the backend already reads.

# Consequences

## Positive

1. **Complete decoupling**: The backend and AI Platform have zero synchronous dependencies. The backend publishes events and continues processing user requests. The AI Platform processes at its own pace. Backend API performance (p95 < 300ms) is completely isolated from AI processing latency (10–120 seconds per operation).

2. **Built-in buffering and load leveling**: Redpanda buffers events when the AI Platform is slow or unavailable. During batch ingestion of 1,000 transcripts, events queue up and the AI Platform processes them at its own pace. The backend never experiences backpressure.

3. **Resilience to AI Platform failures**: If the AI Platform crashes, events remain in Redpanda. When the AI Platform recovers, it resumes processing from the last committed offset. No data loss, no manual recovery.

4. **Independent scaling**: Backend scales based on user traffic (API requests/second). AI Platform scales based on queue depth (pending jobs). Each can be scaled independently without affecting the other.

5. **Cost isolation and governance**: Every AI operation records provider, model, token usage, and cost. Cost analytics are available per story, tenant, workspace, and provider. Budget alerts can be configured per tenant.

6. **Provider agnosticism with graceful failover**: The provider abstraction layer enables automatic failover between Gemini, Claude, and OpenAI. Adding a new provider requires implementing one interface — no backend changes needed.

7. **Human review gate enforced by architecture**: AI outputs are written to PostgreSQL in `REVIEW_REQUIRED` state. Projection workers only consume events for approved content. It is architecturally impossible for unverified AI outputs to appear in the knowledge graph or search results.

8. **Simplified security model**: The AI Platform has no inbound network ports (except container health checks). It only makes outbound connections to Redpanda, PostgreSQL, and AI providers. This dramatically reduces the attack surface.

9. **Event replay for AI pipeline recovery**: If an AI provider returns corrupted data, the pipeline can be replayed from the affected stage. The orchestration service resets the pipeline state and re-produces the request events.

## Negative

1. **No synchronous feedback**: The backend cannot immediately know if an AI operation succeeded or failed. It must wait for the completion event or poll PostgreSQL. This adds complexity to user-facing status tracking (e.g., "is my story processed yet?").

2. **Debugging complexity**: Tracing a single story through the AI pipeline requires correlating 5–10 events across 3–7 services. The correlation ID chain helps, but debugging is inherently harder than a synchronous call chain.

3. **Eventual consistency for AI results**: After the backend publishes a `TranscriptImported` event, there is a delay (seconds to minutes, depending on queue depth and AI provider latency) before the AI results are available in PostgreSQL. User-facing applications must handle this "processing" state.

4. **Operational overhead of Redpanda**: The AI Platform depends on Redpanda availability. If Redpanda is down, no AI processing occurs. This adds an infrastructure dependency that must be monitored and maintained.

5. **Duplicate event handling complexity**: Every AI worker must implement idempotency checks. This adds code complexity and a small performance overhead for database lookups before processing.

6. **AI provider latency variability**: Provider response times vary from 5 seconds to 120 seconds. Pipeline completion time is unpredictable. This makes it difficult to provide accurate ETA to users.

7. **Prompt version coordination**: When a prompt is updated, in-flight jobs may use the old prompt while new jobs use the new prompt. The prompt version is recorded in the job and cost log, but results may be inconsistent during the transition period.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Decoupling** | Backend and AI Platform have zero synchronous dependencies | No synchronous feedback — must poll or wait for events |
| **Resilience** | Events buffer during AI Platform outages | Depends on Redpanda availability |
| **Scaling** | Independent scaling per component | More infrastructure to manage |
| **Cost control** | Per-execution cost tracking | Every execution requires cost logging overhead |
| **Provider flexibility** | Easy to add/switch providers | Provider abstraction layer adds complexity |
| **Security** | No inbound ports on AI Platform | Cannot directly query AI Platform status |
| **Debugging** | Correlation ID provides end-to-end traceability | Async flows are harder to debug than sync |
| **Human review** | Architecturally enforced gate | Additional workflow complexity for review process |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **AI provider rate limits cause pipeline stalls** | High | Medium — delayed processing | Implement adaptive rate limiting in the provider abstraction layer. Queue depth monitoring alerts when rate limits are hit. Auto-failover to alternative provider. |
| **AI provider returns malformed output** | Medium | Medium — job failure, potential data corruption | Schema validation in the validation service catches malformed output. Non-retryable errors go to DLQ for operator review. |
| **Redpanda consumer offset commit causes duplicate processing** | Low | Medium — duplicate AI operations, increased cost | Idempotent job processing prevents duplicate data. Cost tracking may show duplicate charges. Mitigation: commit offsets after PostgreSQL write, not before. |
| **AI worker crashes mid-processing** | Medium | Low — job retries, no data loss | Job state machine detects PROCESSING state with expired deadline. Another worker picks up the job. Idempotent handling prevents duplicate data. |
| **PostgreSQL connection pool exhaustion from AI workers** | Medium | High — AI processing stalls | Use separate connection pools per AI worker service. Set pool size based on worker concurrency. Monitor connection usage. |
| **Large transcript payloads exceed Redpanda message size** | Low | Medium — event rejected | Set `max.message.bytes` to 2MB. For transcripts >500KB, store in PostgreSQL and pass only the ID in the event. |
| **Prompt version mismatch between pipeline stages** | Medium | Low — inconsistent results | Record prompt version per job stage. Orchestration service validates prompt version consistency. Alert on version mismatches. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **AI Platform deployment breaks event contract** | Medium | High — consumers fail to process events | Schema Registry enforces event schema compatibility. CI/CD runs consumer contract tests. Canary deployments for AI Platform changes. |
| **Cost overrun due to unexpected AI usage** | Medium | High — budget exceeded | Set per-tenant and per-workspace cost budgets. Alert when budget threshold exceeded. Implement hard cost caps (stop processing when budget exhausted). |
| **Dead letter queue grows unnoticed** | Medium | Medium — silent pipeline failures | Monitor DLQ count. Alert on any DLQ event. Require operator acknowledgement. Implement DLQ replay dashboard. |
| **AI provider API changes break the abstraction layer** | Low | High — provider unavailable until adapter updated | Pin provider SDK versions. Run integration tests against provider APIs in CI. Monitor provider changelogs. Maintain fallback providers. |
| **Pipeline state in PostgreSQL becomes inconsistent with actual processing** | Medium | Medium — incorrect status displayed to users | Implement periodic reconciliation: compare pipeline run states with actual job states. Alert on inconsistencies. |
| **Multiple AI workers process the same job due to consumer rebalancing** | Low | Low — duplicate processing, increased cost | Idempotent job handling prevents data issues. Cost impact is minimal (a few extra API calls). Mitigation: use a processing lease with TTL. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **AI provider costs increase significantly** | Increased operational cost | Provider abstraction layer enables switching to cheaper providers. Implement cost optimization strategies (model selection per task, caching, batching). |
| **New AI capabilities require real-time processing** | Queue-driven architecture may not meet latency requirements | For real-time AI features (e.g., chat, interactive analysis), consider a separate real-time path with direct provider calls. The queue-driven path remains for batch processing. |
| **Regulatory requirements mandate AI output explainability** | Additional data storage and processing requirements | The existing cost and job tracking infrastructure provides a foundation. Add explainability data (prompt, response, reasoning) to the job record. |
| **Self-hosted LLMs replace external providers** | Significant architectural change | The provider abstraction layer can accommodate a local model adapter. Queue-driven architecture remains valid. Resource requirements (GPU) would change. |
| **Multi-region deployment requires AI Platform replication** | Data sovereignty and latency concerns | Deploy AI Platform per region with region-local Redpanda and PostgreSQL. Cross-region coordination is handled at the orchestration layer. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Real-time AI features are introduced**: If the platform needs real-time AI features (e.g., interactive story analysis, AI-assisted research), a separate synchronous path may be needed alongside the queue-driven path. This should be a separate ADR that defines the real-time architecture without modifying the queue-driven foundation.

2. **Self-hosted LLMs are deployed**: If the platform moves from external AI providers to self-hosted models, the provider abstraction layer needs a new adapter. The queue-driven architecture remains valid, but resource management (GPU scheduling, model loading) introduces new considerations.

3. **AI Platform services are merged or split**: If the AI Platform's service boundaries need adjustment (e.g., merging extraction and normalization, splitting article generation by type), the event contracts and pipeline state machine must be updated. The queue-driven pattern remains unchanged.

4. **Batch processing requirements emerge**: If the platform needs to process large batches (10,000+ transcripts) efficiently, the event-per-item pattern may need batching support. Consider batch events, chunked processing, and parallel pipeline runs.

5. **Cost governance requirements become more stringent**: If per-tenant budgets, real-time cost alerts, or automated cost optimization are required, the cost tracking infrastructure may need enhancement. The existing `ai_cost_log` table provides a foundation.

# References

- **Backend Platform PRD §3.3** — "Queue Driven AI Platform" — Forbidden: Frontend → AI, Backend → AI REST. Required: Backend → Redpanda → AI Workers → PostgreSQL.
- **AI Platform PRD §3.1** — "Queue Driven Architecture" — AI Platform does not expose APIs.
- **AI Platform PRD §3.2** — "Event Driven Processing" — Every AI operation triggered by events.
- **AI Platform PRD §3.3** — "Stateless Workers" — Workers must be stateless and replaceable.
- **AI Platform PRD §3.4** — "Idempotent Processing" — Every job must support re-execution.
- **AI Platform PRD §3.5** — "Model Agnostic Architecture" — Provider abstraction layer.
- **AI Platform PRD §3.7** — "Human Review Required" — AI outputs not automatically published.
- **AI Platform PRD §10** — "Job State Machine" — SUBMITTED → QUEUED → PROCESSING → ... → COMPLETED/FAILED.
- **AI Platform PRD §11** — "Pipeline State Machine" — TRANSCRIPT_READY → ... → FINISHED.
- **AI Platform PRD §12** — "Queue Architecture" — Required Redpanda topics.
- **AI Platform PRD §13** — "AI Provider Layer" — Provider interface with adapters.
- **AI Platform PRD §14** — "Provider Strategy" — Gemini primary, Claude fallback, OpenAI secondary.
- **AI Platform PRD §17** — "Cost Governance" — Per-execution cost tracking requirements.
- **AI Platform PRD §18** — "Retry Strategy" — Exponential backoff, max 5 retries, DLQ.
- **ADR-003: Event-Driven Architecture** — Transactional outbox, event schema, consumer groups, replay.
- **ADR-001: PostgreSQL as Source of Truth** — AI workers write to PostgreSQL, not directly to Neo4j/Weaviate.
- **Transactional Outbox Pattern** — https://microservices.io/patterns/data/transactional-outbox.html
- **Idempotent Consumer Pattern** — https://www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html
- **Dead Letter Channel Pattern** — https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html