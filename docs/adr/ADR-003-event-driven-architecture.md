# ADR-003: Event-Driven Architecture with Redpanda Backbone

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture processes content through a multi-stage pipeline: source ingestion → transcript normalization → canonical story extraction → knowledge extraction → normalization → validation → article generation → embedding generation → graph and vector projection. Each stage is owned by a different service (backend domain services or AI platform workers) and must operate asynchronously — no stage should block the previous stage.

Additionally, multiple business flows depend on state changes:
- A story being created should trigger AI extraction
- Knowledge being validated should trigger article generation
- Articles being published should trigger embedding generation
- Embeddings being ready should trigger graph and vector projections
- Review approvals should trigger publication workflows

These flows span bounded contexts. Direct synchronous calls between services would create temporal coupling, reduce resilience, and violate the architecture principle that the AI Platform must not expose REST endpoints.

## Technical Context

The platform stack includes Spring Boot 4 (Java backend) and Python 3.14 (AI workers), deployed as a modular monolith with a separate AI platform. The databases are PostgreSQL 18 (source of truth), Neo4j 5.26 (graph projection), and Weaviate 1.37 (vector projection). The modular monolith uses in-process events (Spring `ApplicationEventPublisher`) for synchronous cross-module flows, but asynchronous cross-process communication requires a message broker.

The AI Platform PRD explicitly forbids:
- Frontend → AI Platform direct calls
- Backend → AI Platform REST calls

All AI Platform communication must go through Redpanda.

## Constraints

1. **99.5% availability**: The event backbone must not become a single point of failure. Event loss is unacceptable.
2. **At-least-once delivery**: Duplicate events are acceptable (handlers are idempotent). Lost events are not.
3. **No message loss during producer failure**: If the backend crashes after committing a database transaction but before publishing the event, the event must not be lost. This requires the transactional outbox pattern.
4. **Event order matters for some flows**: Immutable versioning creates version chains (StoryCreated → StoryVersionCreated). Projection workers must process events in order for the same aggregate.
5. **Events are the audit trail**: Every event stored in the outbox serves as an immutable audit record. Events must not be deleted — only archived.
6. **Consumer isolation**: A slow or failing consumer must not affect other consumers. AI extraction being slow must not block graph projection.
7. **Scalability target**: 100,000 stories, 10,000,000 transcript segments, 1,000,000 knowledge objects. Event throughput must scale to handle peak loads during batch ingestion.

## Problem Statement

How do we implement an event-driven architecture that guarantees reliable event delivery across heterogeneous services (Java backend and Python AI workers), supports event replay for projection rebuilding, maintains consumer isolation, scales to the platform's target throughput, and provides a resilient foundation for failure recovery — all while using Redpanda as the event backbone and PostgreSQL for the transactional outbox?

# Decision

**The platform is event-driven. Redpanda is the event backbone. All asynchronous operations use events. The transactional outbox pattern guarantees reliable event publication.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Modular Monolith (Java)                          │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │ Identity │  │ Content  │  │Knowledge │  │ Research/Workflow  │ │
│  │ Module   │  │ Module   │  │ Module   │  │ Modules            │ │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────────┬──────────┘ │
│        │             │             │                  │            │
│        ▼             ▼             ▼                  ▼            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    PostgreSQL 18                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │        Transactional Outbox (per bounded context)        │  │  │
│  │  │  identity_outbox │ content_outbox │ knowledge_outbox     │  │  │
│  │  │  research_outbox │ workflow_outbox                       │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  │                                                                │  │
│  │  Business tables committed in same transaction as outbox row   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                  │                                    │
│                                  ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Outbox Publisher (Background Process)            │  │
│  │  - Polls unpublished outbox rows                             │  │
│  │  - Publishes to Redpanda                                    │  │
│  │  - Updates published_at on success                          │  │
│  │  - Retries on failure (exponential backoff)                 │  │
│  │  - Dead letter queue after N retries                        │  │
│  └──────────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Redpanda                                      │
│                                                                      │
│  Topics (partitioned by aggregate_id):                               │
│                                                                      │
│  identity.evt      │ content.evt      │ knowledge.evt               │
│  ───────────       │ ──────────       │ ────────────                │
│  UserCreated       │ SourceRegistered │ KnowledgeExtracted          │
│  RoleAssigned      │ TranscriptImp.   │ KnowledgeValidated          │
│  TenantCreated     │ StoryCreated     │ KnowledgeNormalized         │
│  ApiKeyGenerated   │ ArticlePublished │ ClaimCreated                │
│                     │ StoryVerCreated  │ FolkloreRegistered          │
│                                                                      │
│  workflow.evt      │ research.evt     │ ai.internal                 │
│  ───────────       │ ───────────      │ ───────────                 │
│  ReviewRequested   │ CollectionCreated│ extraction.requested        │
│  ReviewApproved    │ AnnotationAdded  │ extraction.completed        │
│  PublicationPub.   │ ExportGenerated  │ embedding.requested         │
│                     │                  │ graph.projection.requested  │
│                     │                  │ graph.projected             │
└──────────┬──────────────────┬──────────────────┬─────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐
│  Domain      │   │  Projection  │   │  AI Platform Workers │
│  Services    │   │  Workers     │   │  (Python)            │
│  (Java)      │   │  (Python)    │   │                      │
│              │   │              │   │  - Extraction        │
│  Consume:    │   │  Consume:    │   │  - Normalization     │
│  - workflow  │   │  - graph.    │   │  - Validation        │
│    events    │   │    proj.     │   │  - Article gen       │
│  - ai.comp.  │   │  - embed.    │   │  - Embedding gen    │
│              │   │    requested │   │                      │
│              │   │              │   │  Write results to PG │
└──────────────┘   └──────────────┘   └──────────────────────┘
```

## Detailed Decision Rules

### Rule 1: All Asynchronous Operations Use Events

The following operations must always use events:

- **Cross-service communication**: Backend → AI Platform, AI Platform → Backend (completion events)
- **Projection triggers**: PostgreSQL → Neo4j, PostgreSQL → Weaviate
- **Long-running operations**: Knowledge extraction, article generation, embedding generation
- **Cross-domain workflows**: Story created → workflow review requested, review approved → article published
- **Notification triggers**: Content ready for review, publication complete, projection complete

The following operations must never use events (synchronous only):
- **User-facing queries**: Story detail, article content, search results — these read directly from PostgreSQL
- **Authentication and authorization**: These must complete within the HTTP request
- **Synchronous cross-module flows within the monolith**: Use Spring `ApplicationEventPublisher` (as defined in ADR-002)

### Rule 2: Redpanda Is the Event Backbone

Redpanda is chosen over Apache Kafka for:
- **Lower operational complexity**: Single binary, no ZooKeeper/KRaft dependency, self-managed
- **Better performance on commodity hardware**: Optimized for SSD/NVMe, no page cache dependency
- **Kafka-compatible protocol**: Standard Kafka client libraries work without modification
- **Built-in schema registry support**: Via Kafka-compatible Schema Registry integration
- **Exactly the right scale**: Kafka's ecosystem is designed for much larger deployments than the platform requires

Redpanda topics are organized by domain:

```
Domain topics:     identity.evt, content.evt, knowledge.evt, workflow.evt, research.evt
Internal topics:   ai.internal (for AI platform pipeline coordination)
Dead letter:       dlq.identity, dlq.content, dlq.knowledge, dlq.workflow, dlq.ai
Event archive:     archive.events (long-term storage, compacted)
```

### Rule 3: Transactional Outbox Guarantees Reliable Publication

The transactional outbox pattern ensures that event publication is atomic with the database transaction that produces the event. If the application crashes after committing the transaction but before publishing to Redpanda, the outbox publisher will pick up the unpublished event on the next poll cycle.

#### Outbox Table Schema

```sql
CREATE TABLE {domain}_outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Event identification
    event_id        UUID NOT NULL UNIQUE,         -- Globally unique event ID
    event_type      VARCHAR(255) NOT NULL,         -- e.g., 'StoryCreated', 'KnowledgeExtracted'
    event_version   INTEGER NOT NULL DEFAULT 1,    -- Schema version for this event type
    event_sequence  BIGINT,                        -- Monotonic sequence per aggregate (optional, for ordering)
    
    -- Aggregate identification
    aggregate_type  VARCHAR(100) NOT NULL,          -- e.g., 'Story', 'KnowledgeObject'
    aggregate_id    UUID NOT NULL,                  -- ID of the aggregate that produced the event
    
    -- Payload and metadata
    payload         JSONB NOT NULL,                 -- Event-specific data
    metadata        JSONB NOT NULL DEFAULT '{}',   -- tenant_id, workspace_id, correlation_id, causation_id, producer
    
    -- Processing state
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, published, failed, dead_letter
    published_at    TIMESTAMPTZ,                    -- NULL until successfully published to Redpanda
    retry_count     INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,                            -- Last error message for debugging
    
    -- Ordering for sequential processing
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ                     -- When status was last updated
);

-- Indexes for efficient polling
CREATE INDEX idx_{domain}_outbox_status_created 
    ON {domain}_outbox (status, created_at) 
    WHERE status = 'pending';
    
CREATE INDEX idx_{domain}_outbox_aggregate 
    ON {domain}_outbox (aggregate_type, aggregate_id, event_sequence);
```

#### Outbox Publisher Algorithm

```
LOOP:
  1. BEGIN transaction (read committed)
  2. SELECT * FROM {domain}_outbox 
     WHERE status = 'pending' 
     ORDER BY created_at ASC 
     LIMIT batch_size 
     FOR UPDATE SKIP LOCKED
  3. For each row:
     a. Construct Redpanda message from payload + metadata
     b. Produce to Redpanda topic
     c. On success:
        UPDATE status = 'published', published_at = NOW()
     d. On transient failure (timeout, broker unavailable):
        UPDATE retry_count = retry_count + 1
        If retry_count >= max_retries:
          UPDATE status = 'dead_letter'
        Else:
          Leave status = 'pending' (next poll will retry)
     e. On permanent failure (invalid payload, schema violation):
        UPDATE status = 'dead_letter', last_error = error_message
  4. COMMIT transaction
  5. Sleep poll_interval (default: 100ms, configurable)
```

#### Error Handling in Outbox Publisher

| Error Type | Behavior | Recovery |
|-----------|----------|----------|
| Redpanda broker unavailable | Retry with exponential backoff (100ms, 500ms, 1s, 5s, 30s) | Automatic when broker recovers |
| Redpanda topic not found | Dead letter immediately — operator must create topic | Manual intervention, replay from DLQ |
| Payload serialization error | Dead letter — likely a bug | Fix producer code, replay from DLQ |
| Database connection failure | Fail the batch, retry on next poll | Automatic when DB recovers |
| Transaction conflict | PostgreSQL handles via SKIP LOCKED + retry | Automatic |

### Rule 4: Event Schema with Versioning

Every event follows a versioned schema. Breaking changes increment the version number. Backward-compatible changes (adding fields) do not change the version.

```json
{
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "eventType": "StoryCreated",
  "eventVersion": 1,
  "occurredAt": "2026-06-25T01:00:00.000Z",
  "producer": "content-service",
  "aggregateType": "Story",
  "aggregateId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "data": {
    "storyId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Misteri Kuntilanak di Desa Sukamaju",
    "storyType": "FOLKLORE",
    "sourceId": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    "tenantId": "11111111-2222-3333-4444-555555555555"
  },
  "metadata": {
    "tenantId": "11111111-2222-3333-4444-555555555555",
    "workspaceId": "66666666-7777-8888-9999-000000000000",
    "correlationId": "cccccccc-dddd-eeee-ffff-aaaaaaaaaaaa",
    "causationId": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
  }
}
```

**Versioning Rules**:
- **Adding optional fields**: Backward-compatible. Consumers ignore unknown fields. No version bump.
- **Adding required fields**: Major version bump. Old consumers must be updated or they will fail.
- **Renaming fields**: Major version bump. Requires consumer coordination.
- **Removing fields**: Major version bump. Requires consumer coordination.
- **Changing field types**: Major version bump. Requires consumer coordination.

**Consumer Version Handling**:
- Consumers declare their supported event version range (min_version, max_version)
- The event backbone routes events to consumers based on version compatibility
- If no compatible consumer exists, events are routed to a dead letter queue for operator review
- Schema Registry (compatible with Redpanda) enforces versioning at the producer level

### Rule 5: Partitioning for Ordered Processing

Events for the same aggregate must be processed in order. Redpanda topics are partitioned by `aggregate_id`:

```
Topic: content.evt
Partitions: 8 (scalable)
Partition key: aggregate_id (UUID)
```

This ensures that events like `StoryCreated` → `StoryVersionCreated` → `StoryPublished` for the same story are delivered to the same partition and processed in order within that partition.

Partition count should be set based on expected throughput:
- Phase 1 (100–5,000 users): 8 partitions per topic
- Phase 2 (5,000–50,000 users): 16 partitions per topic
- Phase 3 (50,000+ users): Re-evaluate based on observed throughput

### Rule 6: Consumer Group Isolation

Each consumer group represents an independent consumer. Consumer groups operate independently — a slow consumer in one group does not affect other groups.

```
Consumer Groups:

Domain Services:
  group: identity-service        → topics: workflow.evt, ai.internal
  group: content-service         → topics: ai.internal, knowledge.evt
  group: knowledge-service       → topics: content.evt, ai.internal
  group: workflow-service        → topics: content.evt, knowledge.evt

Projection Workers:
  group: graph-projection-worker  → topics: graph.projection.requested
  group: vector-projection-worker → topics: embedding.requested

AI Platform:
  group: orchestration-service    → topics: content.evt, workflow.evt
  group: extraction-service       → topics: ai.internal
  group: normalization-service    → topics: ai.internal
  group: validation-service       → topics: ai.internal
  group: article-service          → topics: ai.internal
  group: embedding-service        → topics: ai.internal

Dead Letter Queue Processors:
  group: dlq-processor            → topics: dlq.*
```

**Isolation guarantees**:
- Each consumer group gets its own offset commit
- Consumer lag in one group does not affect others
- Consumer groups can be added or removed without affecting existing consumers
- Each consumer group can have its own retry and dead letter policy

### Rule 7: Event Replay

Event replay is the mechanism for rebuilding projections, recovering from data corruption, or re-processing failed events.

**Replay Sources**:
1. **Redpanda log retention**: Redpanda retains events based on retention policy (default: 7 days, configurable up to 30 days). For replay within this window, consumers reset their offsets to an earlier position.
2. **PostgreSQL outbox archive**: Outbox rows that have been published are archived with a TTL (default: 90 days). For replay beyond Redpanda retention, the outbox table can be replayed.
3. **Cold storage**: For replay beyond outbox archive TTL, events are exported to object storage (Parquet format on S3/MinIO). This is a future capability for Phase 3.

**Replay Mechanisms**:

| Scenario | Mechanism | Time to Replay (100K events) |
|----------|-----------|------------------------------|
| Re-process failed events (DLQ) | Manually move events from DLQ topic back to source topic | Minutes |
| Rebuild Neo4j projection | Reset graph-projection-worker offset to earliest, or use batch rebuild worker | 1–4 hours |
| Rebuild Weaviate projection | Reset vector-projection-worker offset to earliest, or use batch rebuild worker | 1–4 hours |
| Re-process AI extraction for all stories | Reset orchestration-service offset to earliest | Hours–days (AI provider rate limits apply) |
| Recovery from data corruption | Restore PostgreSQL from backup, then replay events for all affected aggregates | Depends on backup RPO |
| Add new projection type | Start new consumer group from earliest offset | Full replay time |

**Replay Safety**:
- All event handlers must be idempotent (Rule 8)
- Replay must not duplicate data — handlers check if the event was already processed
- Replay progress must be observable via consumer lag metrics
- Replay can be paused and resumed

### Rule 8: Idempotent Event Handlers

Every event handler must produce the same result regardless of how many times it processes the same event.

**Implementation strategies by consumer type**:

_Domain Services (Java/Spring Boot)_:
```java
@Component
public class StoryCreatedHandler {
    
    private final StoryRepository storyRepository;
    private final ProcessedEventTracker processedEventTracker;
    
    @EventListener
    @Transactional
    public void handle(StoryCreatedEvent event) {
        // Check if already processed (idempotency guard)
        if (processedEventTracker.isProcessed(event.getEventId())) {
            log.debug("Event already processed, skipping: {}", event.getEventId());
            return;
        }
        
        // Process event
        Story story = new Story(event.getData());
        storyRepository.save(story);
        
        // Mark as processed
        processedEventTracker.markProcessed(event.getEventId());
    }
}
```

_Projection Workers (Python)_:
```python
async def handle_graph_projection(event):
    # Check if already projected
    projection_state = await db.fetch_one(
        "SELECT projection_version FROM graph_projections "
        "WHERE source_id = $1 AND source_type = $2",
        event.aggregate_id, event.aggregate_type
    )
    
    # Idempotency: if we've already projected this version, skip
    if projection_state and projection_state['projection_version'] >= event.data['version']:
        logger.info(f"Skipping already projected event: {event.event_id}")
        return
    
    # Upsert graph data
    await neo4j_session.run(
        """
        MERGE (s:Story {id: $id})
        SET s.title = $title, s.version = $version
        """,
        id=event.aggregate_id,
        title=event.data['title'],
        version=event.data['version']
    )
    
    # Track projection state
    await db.execute(
        """
        INSERT INTO graph_projections (source_id, source_type, projection_version, projected_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (source_id, source_type) 
        DO UPDATE SET projection_version = $3, projected_at = NOW()
        """,
        event.aggregate_id, event.aggregate_type, event.data['version']
    )
```

AI Workers (Python) — idempotency via job state:
```python
async def extract_knowledge(job_id, transcript_id):
    # Check job state
    job = await db.fetch_one(
        "SELECT status FROM ai_jobs WHERE id = $1", job_id
    )
    
    if job['status'] in ('COMPLETED', 'PROCESSING'):
        # Already processed or being processed — may be a duplicate delivery
        # If PROCESSING, check if the processing deadline has passed
        if job['status'] == 'COMPLETED':
            return  # Idempotent: already done
        # For PROCESSING with expired deadline, treat as retry
        ...
    
    # Process...
```

### Rule 9: Dead Letter Queue with Replay

Events that cannot be processed after the maximum retry count are moved to a dead letter queue (DLQ). DLQ topics follow the naming convention `dlq.{domain}`.

**DLQ Flow**:
1. Consumer catches exception during event processing
2. Consumer retries based on retry policy (exponential backoff: 1s, 5s, 30s, 2min, 10min, 1hr)
3. After maximum retries (default: 6), event is published to DLQ topic
4. DLQ consumer logs the event and sends an alert
5. Operator investigates the failure
6. Operator fixes the issue (schema, bug, configuration)
7. Operator replays events from DLQ back to source topic
8. Consumer processes the replayed events normally

**DLQ Topic Schema**:
```json
{
  "originalEvent": { ... },        // The original event payload
  "originalTopic": "content.evt",
  "originalPartition": 3,
  "originalOffset": 15234,
  "failureReason": "org.postgresql.util.PSQLException: ERROR: duplicate key value violates unique constraint",
  "failureTimestamp": "2026-06-25T02:00:00.000Z",
  "retryCount": 6,
  "consumerGroup": "knowledge-service"
}
```

### Rule 10: Monitoring and Observability

Every event must be observable through the following dimensions:

**Metrics (Prometheus)**:

| Metric | Description | Labels |
|--------|-------------|--------|
| `events_produced_total` | Total events published to Redpanda | topic, event_type, producer |
| `events_consumed_total` | Total events consumed | topic, event_type, consumer_group, status (success/failure) |
| `events_lag_seconds` | Consumer lag in seconds | topic, partition, consumer_group |
| `events_dlq_total` | Events moved to dead letter queue | topic, consumer_group |
| `events_processing_duration_seconds` | Event processing time | topic, event_type, consumer_group |
| `outbox_poll_duration_seconds` | Outbox publisher poll cycle time | domain |
| `outbox_pending_total` | Number of pending events in outbox | domain |

**Alerting Rules**:

| Condition | Severity | Action |
|-----------|----------|--------|
| Consumer lag > 5 minutes | Warning | Scale consumer group, investigate bottleneck |
| Consumer lag > 30 minutes | Critical | Page on-call — potential pipeline stall |
| DLQ event rate > 1/min | Warning | Investigate processing failures |
| DLQ event rate > 10/min | Critical | Page on-call — systemic failure |
| Outbox pending > 1,000 | Warning | Outbox publisher may be failing |
| Outbox pending > 10,000 | Critical | Events not being published — data pipeline stalled |
| Event processing error rate > 1% | Warning | Investigate consumer failures |
| Event processing error rate > 5% | Critical | Page on-call — potential data corruption |

**Tracing (OpenTelemetry)**:
- Each event carries a `correlationId` that is propagated across all downstream events
- Each event carries a `causationId` that references the event that caused it
- This creates a trace: `TranscriptImported → ExtractionRequested → ExtractionCompleted → ProjectionRequested → Projected`
- Distributed tracing across Java backend and Python AI workers is possible via the correlation ID

# Event Catalog

## Domain Events (Backend)

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| `SourceRegistered` | content-service | ai-platform (orchestration) | New source/channel registered |
| `SourceMetadataImported` | content-service | ai-platform (ingestion) | Source metadata imported |
| `TranscriptImported` | content-service | ai-platform (orchestration) | Transcript ready for processing |
| `TranscriptNormalized` | ai-platform (ingestion) | ai-platform (orchestration) | Transcript normalized |
| `StoryCreated` | content-service | knowledge-service, workflow-service, ai-platform (orchestration) | Story created |
| `StoryVersionCreated` | content-service | knowledge-service, ai-platform | New story version created |
| `CanonicalStoryExtracted` | ai-platform (extraction) | ai-platform (orchestration), knowledge-service | Canonical story extracted |
| `KnowledgeExtracted` | ai-platform (extraction) | ai-platform (orchestration), knowledge-service | Knowledge objects extracted |
| `KnowledgeNormalized` | ai-platform (normalization) | ai-platform (orchestration) | Knowledge normalized |
| `KnowledgeValidated` | ai-platform (validation) | ai-platform (orchestration) | Knowledge validated |
| `ArticleGenerated` | ai-platform (article) | content-service, ai-platform (orchestration) | Article generated |
| `ArticlePublished` | content-service (workflow) | ai-platform (embedding), projection workers | Article published |
| `EmbeddingGenerated` | ai-platform (embedding) | ai-platform (orchestration), projection workers | Embeddings generated |
| `GraphProjectionRequested` | ai-platform (orchestration) | graph-projection-worker | Trigger graph projection |
| `GraphProjected` | graph-projection-worker | ai-platform (orchestration) | Graph projection completed |
| `ReviewRequested` | workflow-service | content-service, knowledge-service | Human review requested |
| `ReviewApproved` | workflow-service | content-service, knowledge-service, ai-platform | Review approved |
| `ReviewRejected` | workflow-service | content-service, knowledge-service, ai-platform | Review rejected — reprocess |
| `PublicationPublished` | workflow-service | content-service, ai-platform | Content published |

## Internal Events (AI Platform Pipeline)

| Event | Description |
|-------|-------------|
| `extraction.requested` | Trigger canonical story extraction |
| `extraction.completed` | Extraction finished |
| `knowledge.extraction.requested` | Trigger knowledge extraction |
| `knowledge.extracted` | Knowledge extraction finished |
| `knowledge.normalization.requested` | Trigger normalization |
| `knowledge.normalized` | Normalization finished |
| `knowledge.validation.requested` | Trigger validation |
| `knowledge.validated` | Validation finished |
| `article.generation.requested` | Trigger article generation |
| `article.generated` | Article generation finished |
| `embedding.generation.requested` | Trigger embedding generation |
| `embedding.generated` | Embedding generation finished |
| `graph.projection.requested` | Trigger graph projection |
| `graph.projected` | Graph projection finished |

# Alternatives Considered

## Alternative 1: Synchronous REST Communication

**Description**: Replace event-driven architecture with synchronous REST calls. Backend calls AI Platform directly via REST. Services communicate via REST/gRPC for all flows.

**Advantages**:
- Simplest mental model — request/response is universally understood
- Immediate consistency — caller knows the result before proceeding
- No message broker infrastructure to operate and maintain
- Easier debugging — single request trace, no async correlation
- Lower initial infrastructure cost — no Redpanda cluster

**Disadvantages**:
- **Violates AI Platform PRD**: The AI Platform PRD explicitly forbids Backend → AI Platform REST calls. This is a hard constraint.
- **Temporal coupling**: If the AI Platform is slow or down, the backend request fails or times out. AI extraction can take 30–120 seconds — this is unacceptable for user-facing HTTP requests.
- **No retry without complex infrastructure**: If a REST call fails mid-processing, the caller must implement complex retry logic. There is no built-in retry, dead letter, or replay mechanism.
- **No event replay**: Rebuilding projections requires re-running all AI extraction. With REST, this means replaying all source data through the pipeline. With events, the pipeline state is already recorded.
- **No audit trail**: REST calls are ephemeral. There is no persistent record of what processing occurred, when, and with what result. The transactional outbox provides an immutable audit log.
- **Scaling bottlenecks**: REST servers must handle peak load. Event-driven architecture buffers spikes via queues. The AI Platform can process at its own pace.
- **No consumer isolation**: A slow AI extraction blocks the backend thread. With events, the backend publishes and moves on.
- **Cross-service communication in modular monolith**: Even within the monolith, synchronous calls between modules for async operations create thread blocking and cascading failures.

**Rejection rationale**: Synchronous REST communication is unsuitable for long-running AI operations, violates the AI Platform architecture principles, and lacks the reliability, auditability, and replay capabilities that the platform requires.

## Alternative 2: Database Polling Without Redpanda

**Description**: Use the transactional outbox table as the sole event transport mechanism. Consumers poll the outbox table directly using SQL queries. No message broker is used.

**Advantages**:
- Zero additional infrastructure — PostgreSQL is already in the stack
- No message broker to operate, monitor, or scale
- Strong consistency — the outbox is in the same database as business data
- Simple implementation — no Kafka/Redpanda client libraries, no schema registry

**Disadvantages**:
- **No consumer isolation**: All consumers poll the same outbox table. Polling conflicts increase with the number of consumers. A slow consumer holding a row lock blocks others.
- **No ordered delivery guarantees**: Without partitions, maintaining event order across multiple consumers requires complex coordination (sequence numbers, locking).
- **No built-in offset management**: Each consumer must track its own processed position. Adding a new consumer requires replaying from the beginning.
- **Scalability bottleneck**: The outbox table becomes a contention point as event volume grows. At 100,000 stories with multiple events per story, polling contention degrades database performance for business operations.
- **High polling overhead**: N consumers × poll_interval → N× queries per second against the outbox table. With 10+ consumer groups polling every 100ms, that is 100+ queries/second just for polling.
- **No dead letter queue management**: Failed events and retry scheduling must be handled in-application. Standard DLQ patterns (separate topic, replay) are not available.
- **Python AI workers would need direct database access**: AI workers would query PostgreSQL directly, increasing database connection count and creating a coupling between AI workers and the database schema.
- **No partitioning**: Cannot parallelize processing of different aggregates across multiple worker instances without complex sharding logic.
- **No message retention beyond outbox TTL**: Once outbox rows are archived, events are lost. Redpanda provides configurable retention for replay.

**Rejection rationale**: Database polling works for simple event-driven architectures with few consumers and low throughput. This platform has multiple consumers (5+ domain services, 6+ AI workers, 2+ projection workers), needs consumer isolation, ordered delivery, and replay capabilities. The polling overhead and lack of partitioning make this approach unscalable at the target volume.

## Alternative 3: RabbitMQ as Event Backbone

**Description**: Use RabbitMQ instead of Redpanda as the message broker. RabbitMQ provides exchanges, queues, and routing for event distribution.

**Advantages**:
- Mature technology with extensive documentation and community support
- Flexible routing via exchanges (direct, topic, fanout, headers)
- Built-in dead letter exchanges and retry mechanisms
- Lighter weight than Kafka/Redpanda for smaller deployments
- Easier to operate for teams familiar with message queues

**Disadvantages**:
- **No log-based storage**: RabbitMQ is a message queue, not a log. Once a message is consumed and acknowledged, it is deleted. There is no built-in mechanism for replaying historical messages.
- **No partitioning for ordered delivery**: RabbitMQ queues are ordered, but parallel consumers on the same queue break ordering. Achieving ordered processing per aggregate requires complex routing (one queue per aggregate or consistent hashing exchange).
- **No offset management**: RabbitMQ uses acknowledgments. There is no concept of consumer offsets that can be reset for replay. Replaying requires re-publishing messages from storage.
- **Scaling limits**: RabbitMQ's performance degrades with many queues and high throughput. At the target scale of millions of events, RabbitMQ requires significant tuning and infrastructure.
- **No native schema registry**: Schema evolution must be handled externally or in-application.
- **Consumer group semantics are different**: RabbitMQ's competing consumer pattern is not directly equivalent to Kafka consumer groups. Adding/removing consumers requires queue reconfiguration.
- **Operational maturity**: Redpanda's Kafka API compatibility means the platform can use standard Kafka tooling and ecosystem. RabbitMQ requires a different operational skill set.
- **Long-term retention is not a core feature**: RabbitMQ is designed for transient messaging. The platform needs event retention for replay (7–90 days minimum). RabbitMQ requires plugins or external storage for this.

**Rejection rationale**: RabbitMQ is a good choice for command queues and work distribution, but the platform's event-driven architecture requires log-based storage for replay, ordered delivery per aggregate, consumer offset management, and long-term retention. Redpanda/Kafka's log-based model is a better fit for these requirements.

## Alternative 4: PostgreSQL LISTEN/NOTIFY for Real-Time Events

**Description**: Use PostgreSQL's `LISTEN`/`NOTIFY` mechanism for event distribution. Backend services and AI workers connect to PostgreSQL and receive notifications asynchronously when events are published.

**Advantages**:
- Trivially simple — built into PostgreSQL, no additional infrastructure
- No polling overhead — PostgreSQL pushes notifications to listeners
- Transactional — NOTIFY can be sent within the same transaction that modifies business data
- Zero latency — notifications are delivered immediately within the same transaction

**Disadvantages**:
- **No persistence**: If a listener is not connected, the notification is lost. There is no queue, no retention, no replay.
- **No consumer group semantics**: Every listener receives every notification. There is no way to distribute work across multiple consumer instances.
- **Single channel limit**: PostgreSQL's notification system is not designed for high throughput. At high event volumes, the notification channel becomes a bottleneck.
- **Payload size limit**: NOTIFY payload is limited to 8,000 bytes. Complex events must be truncated or stored in a table with a reference ID.
- **No ordering guarantees**: Notifications may be delivered out of order to different listeners.
- **No dead letter or retry**: If a listener fails to process a notification, there is no built-in retry mechanism. The notification is lost.
- **Not suitable for Python AI workers**: AI workers run as separate processes. Maintaining persistent PostgreSQL connections for all workers creates connection management overhead and couples workers to the database.
- **No partitioning**: All listeners receive all notifications. Cannot parallelize processing by aggregate.

**Rejection rationale**: `LISTEN`/`NOTIFY` is suitable for cache invalidation and lightweight event distribution within a single application. It is not suitable for the platform's requirements: persistent event streams, consumer isolation, replay capability, and cross-process communication with Python workers. The notification is lost if the consumer is not connected — this is unacceptable for the platform's reliability requirements.

# Consequences

## Positive

1. **Loose coupling between components**: Backend services, AI workers, and projection workers communicate exclusively through events. No component needs to know the location, availability, or implementation details of another component.

2. **Reliable event delivery**: The transactional outbox pattern guarantees that events are never lost, even if the producer crashes immediately after committing the database transaction. At-least-once delivery with idempotent handlers ensures every event is processed exactly once (effectively).

3. **Built-in audit trail**: Every event stored in the outbox is an immutable record of what happened, when, and why. The correlation ID chain provides end-to-end traceability across the entire pipeline.

4. **Event replay for recovery**: Projections can be rebuilt by replaying events. Data corruption can be recovered by restoring PostgreSQL from backup and replaying affected events. New projection types can be added by starting from the earliest event.

5. **Consumer isolation**: A slow consumer (e.g., AI extraction waiting for a provider response) does not affect other consumers (e.g., graph projection). Each consumer group maintains its own offset and processes at its own pace.

6. **Buffering for spike handling**: Redpanda buffers events during traffic spikes. The AI Platform processes at its own pace without backpressure on the backend. Backend response times remain stable even when AI processing is overloaded.

7. **Scalable processing**: Partitioned topics allow parallel processing by aggregate. Multiple consumer instances within a group distribute partitions across instances. Scaling is achieved by adding more consumer instances.

8. **Queue-driven AI alignment**: The event-driven architecture naturally implements the queue-driven AI Platform requirement. Backend publishes events → Redpanda buffers → AI workers consume → AI workers write results to PostgreSQL → AI workers publish completion events.

## Negative

1. **Eventual consistency**: After a backend operation completes, downstream consumers may not have processed the event yet. A user who creates a story may not see it in the knowledge graph immediately (until the projection worker processes the event). This delay is typically sub-second to seconds.

2. **Eventual consistency management**: Application code must handle the case where data is available in PostgreSQL but not yet in Neo4j or Weaviate. This adds complexity to read paths that combine data from multiple stores.

3. **Operational overhead of Redpanda**: Redpanda is an additional infrastructure component that must be deployed, monitored, backed up, and scaled. Broker failures, partition leadership changes, and disk space management add operational burden.

4. **Event schema evolution complexity**: Adding, removing, or changing event fields requires coordination between producers and consumers. Schema Registry helps but does not eliminate the need for version management and consumer migration planning.

5. **Debugging async flows is harder**: A user-reported issue may span 3–5 events across 2–3 services. Tracing the flow requires correlating events by correlationId across topics and services. Tooling (OpenTelemetry + distributed tracing) is essential.

6. **Duplicate event handling overhead**: Every event handler must implement idempotency guards. This adds code complexity and a small performance cost (checking if an event was already processed).

7. **Outbox table growth**: At scale, the outbox table grows with event production. Without archiving, the table becomes a performance concern. Archiving requires a cleanup strategy (TTL-based deletion or archival to cold storage).

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Reliability** | Transactional outbox guarantees no event loss | Requires idempotent handlers for duplicate events |
| **Decoupling** | Services evolve independently | Event schema changes require coordination |
| **Scalability** | Partitioned topics for parallel processing | Event ordering requires partitioning by aggregate_id |
| **Observability** | Built-in audit trail via event log | Async flows are harder to debug than sync |
| **Recovery** | Replay enables projection rebuilding | Replay at scale takes time (hours for full rebuild) |
| **Operational simplicity** | Consumer isolation by design | Requires operating Redpanda cluster |
| **AI Platform integration** | Queue-driven, no REST needed | AI workers must poll or subscribe to events |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Event loss due to outbox publisher failure** | Low | Critical — unrecoverable data | Outbox publisher runs as part of the monolith. If it crashes, it restarts and picks up pending events. For additional safety, implement a health check that alerts if outbox pending count exceeds threshold. |
| **Event loss due to Redpanda broker failure** | Low | Critical — unrecoverable data | Redpanda is deployed with replication factor 3. If the leader broker fails, a follower takes over. Events are persisted to disk before acknowledgment. Configure `min.insync.replicas=2`, `acks=all`. |
| **Out-of-order event processing** | Medium | Medium — projections may be temporarily inconsistent | Partitioning by aggregate_id guarantees order within a partition. Potential issue: events for different aggregates may appear out of order in projections that span aggregates. Mitigation: use database-level upserts, not sequential processing, for cross-aggregate projections. |
| **Duplicate events cause data corruption** | Medium | Medium — duplicate graph nodes or embeddings | All handlers are idempotent (checksum-based deduplication, upsert semantics, version checking). Run periodic reconciliation jobs to detect and fix duplicates. |
| **Event schema mismatch between producer and consumer** | Medium | High — consumer fails to process event | Schema Registry enforces compatibility. Consumers declare supported version range. Incompatible events are routed to DLQ for operator review. CI/CD pipeline runs consumer compatibility tests. |
| **Outbox table becomes too large** | Medium | Low — degraded query performance | Archive outbox rows older than TTL (default: 90 days) to a separate archive table or cold storage. Run archiving as a scheduled job during low-traffic periods. |
| **Consumer group rebalancing causes processing delays** | Medium | Low — temporary processing stall | Redpanda consumer group rebalancing is typically sub-second. During rebalancing, partitions are reassigned to available consumers. Unprocessed events remain in the partition and are processed after rebalancing completes. |
| **AI worker pipeline stall due to event backlog** | Medium | Medium — delayed AI processing | Monitor consumer lag for all AI workers. Auto-scale worker instances based on lag. If lag exceeds threshold, scale up workers. If AI provider rate limits are the bottleneck, implement adaptive throttling. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Outbox publisher not keeping up with event production** | Low | Medium — events pile up in outbox | Monitor outbox pending count. Scale outbox publisher as needed (multiple poller threads). Optimize Redpanda produce latency. |
| **Redpanda disk space exhaustion** | Low | High — broker crashes or rejects writes | Configure disk-based retention limits. Monitor disk usage. Set up alerts at 70%, 85%, 95% disk usage. Implement tiered storage for long-term retention. |
| **Dead letter queue grows unchecked** | Medium | Medium — silent data loss if DLQ is not monitored | Monitor DLQ count. Alert on any DLQ event. Require operator acknowledgement for each DLQ event. Implement DLQ replay workflow. |
| **Developer forgets to implement idempotency** | High | Medium — duplicate data on event replay | Enforce idempotency patterns in code review. Provide base classes/abstract handlers that include idempotency checks. Run replay drills in staging to catch missing idempotency. Add integration tests that publish duplicate events. |
| **Event schema change without consumer migration** | Medium | High — consumers fail silently | Schema Registry enforces schema validation. Any consumer that cannot handle the new schema will fail with a clear error. CI/CD prevents deployment of incompatible producers. |
| **Replay accidentally triggers production data changes** | Low | Critical — data corruption if replay is run on production | Replay should only be run in a controlled manner. Implement replay safeguards: confirm prompt, dry-run mode, rate-limited replay, rollback capability. Replay should only affect the target projection, not source data. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Event volume exceeds Redpanda capacity** | Degraded throughput, increased latency | Partition count can be increased (requires topic reconfiguration). Redpanda cluster can be scaled horizontally. Tiered storage offloads older events to object storage. |
| **New bounded context requires new event topics** | Additional operational overhead | Topic creation is a standard operational procedure. Follow established naming convention `{domain}.evt`. Document event catalog changes in ADRs. |
| **Event playback for new consumers becomes impractical at scale** | Full replay may take too long | Implement snapshot-based projections (current state stored in PostgreSQL, replay only processes events after snapshot). Consider CDC-based initial load for new consumers. |
| **Multi-region deployment requires cross-region event replication** | Significant architectural change | Redpanda cluster can span multiple regions (requires low-latency links). Alternative: deploy independent Redpanda clusters per region with asynchronous event forwarding for cross-region flows. |
| **Regulatory requirements mandate event retention beyond 90 days** | Increased storage cost, archival complexity | Export events to object storage (Parquet format on S3). Implement point-in-time replay from object storage archives. Consider Redpanda tiered storage for seamless archival. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Event volume exceeds Redpanda capacity**: If throughput exceeds 100,000 events/second or retention requirements exceed 90 days, the event architecture may need partitioning across multiple Redpanda clusters or tiered storage configuration.

2. **New bounded context added**: If a new domain service is introduced (e.g., a recommendation service, analytics service), revise the event catalog and topic structure. New topics should follow the established naming convention.

3. **Event schema versioning becomes unwieldy**: If event version proliferation (10+ versions per event type) makes consumer management impractical, consider schema evolution strategies (Avro, Protobuf, or event schema translation layer).

4. **Multi-region deployment required**: If the platform needs to serve users from multiple geographic regions, event replication across regions introduces complexity that may require a revised architecture.

5. **Real-time event processing requirements emerge**: If the platform needs sub-100ms event processing for real-time features, the asynchronous outbox polling (100ms latency) may need to be replaced with CDC-based (Change Data Capture) event publication using Debezium or pgoutput.

6. **Migration from modular monolith to microservices**: As modules are extracted into independent services (per ADR-002 extraction strategy), each service will need its own outbox publisher. The event contracts remain the same — only the producer process changes.

# References

- **Backend Platform PRD §3.2** — "Event Driven Architecture" — All asynchronous operations must use events.
- **Backend Platform PRD §10** — "Event Architecture" — Required events list.
- **AI Platform PRD §3.1** — "Queue Driven Architecture" — No REST, only Redpanda.
- **AI Platform PRD §3.2** — "Event Driven Processing" — Every AI operation triggered by events.
- **AI Platform PRD §12** — "Queue Architecture" — Required topics for AI pipeline.
- **ADR-001: PostgreSQL as Source of Truth** — Transactional outbox pattern for reliable event publication.
- **ADR-002: Modular Monolith First** — In-process events for synchronous cross-module flows, Redpanda for async.
- **ADR-004: Event-Driven Architecture (previous version)** — Earlier draft of this decision.
- **Transactional Outbox Pattern** — https://microservices.io/patterns/data/transactional-outbox.html
- **Redpanda Documentation** — https://docs.redpanda.com/ — Architecture, configuration, and operational guidance.
- **Apache Kafka Documentation** — https://kafka.apache.org/documentation/ — Consumer groups, partitioning, offset management.
- **Idempotent Consumer Pattern** — https://www.enterpriseintegrationpatterns.com/patterns/messaging/IdempotentReceiver.html
- **Dead Letter Channel Pattern** — https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html
- **Correlation Identifier Pattern** — https://www.enterpriseintegrationpatterns.com/patterns/messaging/CorrelationIdentifier.html
- **OpenTelemetry** — https://opentelemetry.io/ — Distributed tracing and metrics for event-driven systems.