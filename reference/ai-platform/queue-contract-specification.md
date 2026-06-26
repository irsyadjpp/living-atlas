# AI Platform Queue Contract Specification

## The Living Atlas of Indonesian Mystery Culture

**Version:** 1.0  
**Status:** Draft  
**Owner:** AI Platform Team  

---

# Table of Contents

1. [Queue Architecture Overview](#1-queue-architecture-overview)
2. [Queue Ownership Model](#2-queue-ownership-model)
3. [Topic Naming Standards](#3-topic-naming-standards)
4. [Topic Catalog](#4-topic-catalog)
5. [Message Envelope Standard](#5-message-envelope-standard)
6. [Message Schema Governance](#6-message-schema-governance)
7. [Retry Strategy](#7-retry-strategy)
8. [Idempotency Strategy](#8-idempotency-strategy)
9. [Security](#9-security)
10. [Monitoring](#10-monitoring)

---

# 1. Queue Architecture Overview

## 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND (Spring Boot)                        │
│                                                                     │
│  content-service    knowledge-service    workflow-service           │
│       │                   │                    │                    │
│  ┌────┴────┐        ┌────┴────┐          ┌────┴────┐               │
│  │ Outbox  │        │ Outbox  │          │ Outbox  │               │
│  │  Table  │        │  Table  │          │  Table  │               │
│  └────┬────┘        └────┬────┘          └────┬────┘               │
│       │                  │                    │                    │
└───────┼──────────────────┼────────────────────┼────────────────────┘
        │                  │                    │
        ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         REDPANDA CLUSTER                            │
│                                                                     │
│  Topics: source.submitted     knowledge.validated                   │
│          transcript.imported  article.generated                     │
│          story.extracted      review.approved                       │
│          ... (23 topics)                                            │
│                                                                     │
│  DLQ Topics: source.submitted.dlq  knowledge.validated.dlq          │
│              ... (one DLQ per source topic)                         │
└─────────┬──────────────────┬──────────────────┬─────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AI WORKERS (Python)                          │
│                                                                     │
│  orchestration-service   extraction-service   normalization-service │
│  ingestion-service       validation-service    article-service      │
│  embedding-service                                                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL (ai_platform schema)                             │   │
│  │  - processed_events (dedup)                                  │   │
│  │  - jobs (pipeline tracking)                                  │   │
│  │  - pipeline_state (per-source state machine)                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
          │                  │                    │
          ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PROJECTION WORKERS                              │
│                                                                     │
│  neo4j-sync (graph projection)    weaviate-sync (vector projection) │
└─────────────────────────────────────────────────────────────────────┘
```

## 1.2 Data Flow

```
Backend Service
  │
  │  1. Write to outbox table (transactional)
  │  2. Outbox publisher reads pending rows
  │  3. Publish to Redpanda topic
  ▼
Redpanda Topic
  │
  │  4. AI Worker consumes from topic
  │  5. Check dedup table (skip if already processed)
  │  6. Process message
  │  7. Write result to PostgreSQL
  │  8. Publish result event to next topic
  ▼
Next Redpanda Topic (or DLQ on failure)
```

## 1.3 Infrastructure Requirements

| Component | Specification |
|-----------|--------------|
| Message Broker | Redpanda 24.x+ (Kafka API compatible) |
| Minimum Partitions | 3 per topic (default) |
| Replication Factor | 3 (production) / 1 (development) |
| Message Retention | 7 days (default) / 30 days (DLQ) |
| Max Message Size | 10 MB (default) / 50 MB (transcript topics) |
| Compression | `lz4` (default) / `zstd` (transcript topics) |
| ACK Mode | `all` (producer) |
| Auto Offset Reset | `earliest` (new consumers) |
| Enable Idempotence | `true` (producer) |

## 1.4 Consumer Group Naming Convention

Consumer groups follow the pattern:

```
{service-name}-{topic-shorthand}
```

Examples:

| Consumer Group | Service | Topic Consumed |
|---------------|---------|----------------|
| `orchestration-source` | orchestration-service | source.submitted |
| `orchestration-transcript` | orchestration-service | transcript.imported |
| `extraction-story` | extraction-service | story.extraction.requested |
| `extraction-knowledge` | extraction-service | knowledge.extraction.requested |
| `normalization-knowledge` | normalization-service | knowledge.normalization.requested |
| `validation-knowledge` | validation-service | knowledge.validation.requested |
| `article-generation` | article-service | article.generation.requested |
| `embedding-generation` | embedding-service | embedding.generation.requested |
| `content-source` | content-service | source.metadata.imported |
| `content-story` | content-service | story.extracted |
| `content-article` | content-service | article.generated |
| `knowledge-extracted` | knowledge-service | knowledge.extracted |
| `knowledge-validated` | knowledge-service | knowledge.validated |
| `workflow-review` | workflow-service | review.requested |
| `neo4j-graph` | neo4j-sync | graph.projection.requested |
| `weaviate-embedding` | weaviate-sync | embedding.generated |

---

# 2. Queue Ownership Model

## 2.1 Ownership Principles

- **Topic ownership** is assigned to the service that produces messages to the topic.
- **Schema ownership** is assigned to the service that defines the message payload schema.
- **Version ownership** follows the producer — the producer decides when to evolve a schema.
- **Consumer responsibility** is to tolerate schema evolution within the compatibility guarantees.

## 2.2 Topic Ownership Matrix

| Topic | Owner | Producer | Schema Owner | Version Authority |
|-------|-------|----------|-------------|-------------------|
| `source.submitted` | Backend | content-service | content-service | content-service |
| `source.metadata.imported` | AI Platform | ingestion-service | ingestion-service | ingestion-service |
| `transcript.imported` | AI Platform | ingestion-service | ingestion-service | ingestion-service |
| `transcript.normalized` | AI Platform | ingestion-service | ingestion-service | ingestion-service |
| `story.extraction.requested` | AI Platform | orchestration-service | orchestration-service | orchestration-service |
| `story.extracted` | AI Platform | extraction-service | extraction-service | extraction-service |
| `knowledge.extraction.requested` | AI Platform | orchestration-service | orchestration-service | orchestration-service |
| `knowledge.extracted` | AI Platform | extraction-service | extraction-service | extraction-service |
| `knowledge.normalization.requested` | AI Platform | orchestration-service | orchestration-service | orchestration-service |
| `knowledge.normalized` | AI Platform | normalization-service | normalization-service | normalization-service |
| `knowledge.validation.requested` | AI Platform | orchestration-service | orchestration-service | orchestration-service |
| `knowledge.validated` | AI Platform | validation-service | validation-service | validation-service |
| `article.generation.requested` | AI Platform | orchestration-service | orchestration-service | orchestration-service |
| `article.generated` | AI Platform | article-service | article-service | article-service |
| `embedding.generation.requested` | AI Platform | orchestration-service | orchestration-service | orchestration-service |
| `embedding.generated` | AI Platform | embedding-service | embedding-service | embedding-service |
| `graph.projection.requested` | AI Platform | orchestration-service | orchestration-service | orchestration-service |
| `graph.projected` | Data Platform | neo4j-sync | neo4j-sync | neo4j-sync |
| `review.requested` | Backend | orchestration-service / content-service | workflow-service | workflow-service |
| `review.approved` | Backend | workflow-service | workflow-service | workflow-service |
| `review.rejected` | Backend | workflow-service | workflow-service | workflow-service |
| `publication.requested` | Backend | workflow-service | workflow-service | workflow-service |
| `publication.completed` | Backend | content-service | content-service | content-service |

## 2.3 Ownership Responsibilities

### Topic Owner Responsibilities
- Define the topic configuration (partitions, retention, compaction).
- Define the message schema and versioning policy.
- Ensure backward compatibility for at least 90 days.
- Document the schema in the event catalog.
- Provide sample messages for consumer testing.

### Consumer Responsibilities
- Accept messages within the compatibility guarantee.
- Handle unknown fields gracefully (ignore, do not crash).
- Implement idempotent processing (dedup by `eventId`).
- Report consumer lag and health status.
- Tolerate message replay without side effects.

## 2.4 Cross-Boundary Topics

Topics that cross the Backend ↔ AI Platform boundary require special coordination:

| Topic | Direction | Coordination |
|-------|-----------|-------------|
| `source.submitted` | Backend → AI | Schema defined in `AiBridgeEvent` envelope. Backend owns schema. |
| `source.metadata.imported` | AI → Backend | Schema defined in `AiBridgeEvent` envelope. AI Platform owns schema. |
| `story.extracted` | AI → Backend | Schema defined in `AiBridgeEvent` envelope. AI Platform owns schema. |
| `article.generated` | AI → Backend | Schema defined in `AiBridgeEvent` envelope. AI Platform owns schema. |
| `review.approved` | Backend → AI | Schema defined in `AiBridgeEvent` envelope. Backend owns schema. |
| `review.rejected` | Backend → AI | Schema defined in `AiBridgeEvent` envelope. Backend owns schema. |
| `publication.completed` | Backend → AI | Schema defined in `AiBridgeEvent` envelope. Backend owns schema. |

**Coordination rules:**
1. Schema changes on cross-boundary topics require a minimum 2-week notice.
2. Both sides must approve major version changes.
3. A compatibility test suite must pass before deployment.
4. The `EventTopics.java` file in `packages/shared-events` is the single source of truth for cross-boundary topic names.

---

# 3. Topic Naming Standards

## 3.1 Naming Convention

Topics use **dot-separated lowercase** with the following structure:

```
{domain}.{action}[.{qualifier}]
```

| Segment | Description | Examples |
|---------|-------------|----------|
| `{domain}` | The domain area | `source`, `transcript`, `story`, `knowledge`, `article`, `embedding`, `graph`, `review`, `publication` |
| `{action}` | The action or state | `submitted`, `imported`, `extraction`, `normalized`, `validated`, `generation`, `generated`, `projection`, `projected`, `requested`, `approved`, `rejected`, `completed` |
| `{qualifier}` | Optional sub-domain | `requested` (for command events), `dlq` (for dead letter queues) |

## 3.2 Topic Name Patterns

| Pattern | Semantics | Examples |
|---------|-----------|----------|
| `{domain}.{past_tense}` | Factual event (something happened) | `source.submitted`, `transcript.imported`, `story.extracted` |
| `{domain}.{past_participle}` | State transformation | `transcript.normalized`, `knowledge.validated` |
| `{domain}.{action}.requested` | Command (request an action) | `story.extraction.requested`, `article.generation.requested` |
| `{domain}.{past_tense}.dlq` | Dead letter queue | `source.submitted.dlq`, `knowledge.validated.dlq` |

## 3.3 Complete Topic List

```
source.submitted
source.metadata.imported
source.submitted.dlq
source.metadata.imported.dlq

transcript.imported
transcript.normalized
transcript.imported.dlq
transcript.normalized.dlq

story.extraction.requested
story.extracted
story.extraction.requested.dlq
story.extracted.dlq

knowledge.extraction.requested
knowledge.extracted
knowledge.normalization.requested
knowledge.normalized
knowledge.validation.requested
knowledge.validated
knowledge.extraction.requested.dlq
knowledge.extracted.dlq
knowledge.normalization.requested.dlq
knowledge.normalized.dlq
knowledge.validation.requested.dlq
knowledge.validated.dlq

article.generation.requested
article.generated
article.generation.requested.dlq
article.generated.dlq

embedding.generation.requested
embedding.generated
embedding.generation.requested.dlq
embedding.generated.dlq

graph.projection.requested
graph.projected
graph.projection.requested.dlq
graph.projected.dlq

review.requested
review.approved
review.rejected
review.requested.dlq
review.approved.dlq
review.rejected.dlq

publication.requested
publication.completed
publication.requested.dlq
publication.completed.dlq
```

## 3.4 Topic Name Registration

All topic names MUST be registered in the `EventTopics.java` file located at:

```
packages/shared-events/src/main/java/id/livingatlas/sharedevents/EventTopics.java
```

This file is the single source of truth for topic names used in cross-boundary communication. AI Platform workers MUST reference topic names from configuration, not hardcoded strings.

---

# 4. Topic Catalog

## 4.1 Topic Configuration Template

Each topic is configured with the following parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `partitions` | Number of partitions | 3 |
| `replication.factor` | Replication factor | 3 (prod) / 1 (dev) |
| `retention.ms` | Message retention period | 604800000 (7 days) |
| `retention.bytes` | Max bytes per partition | -1 (unlimited) |
| `cleanup.policy` | Log cleanup policy | `delete` |
| `compression.type` | Message compression | `lz4` |
| `max.message.bytes` | Max message size | 10485760 (10 MB) |
| `min.insync.replicas` | Min in-sync replicas for acks=all | 2 (prod) / 1 (dev) |

## 4.2 Complete Topic Catalog

### 4.2.1 Source Topics

#### `source.submitted`

| Property | Value |
|----------|-------|
| **Producer** | content-service (Spring Boot) |
| **Consumer** | orchestration-service (Python) |
| **Partition Key** | `sourceId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `sourceId` (same partition = same source) |
| **DLQ Topic** | `source.submitted.dlq` |
| **DLQ Retention** | 30 days |
| **Schema Registry** | Required |

#### `source.metadata.imported`

| Property | Value |
|----------|-------|
| **Producer** | ingestion-service (Python) |
| **Consumer** | content-service (Spring Boot), orchestration-service (Python) |
| **Partition Key** | `sourceId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `sourceId` |
| **DLQ Topic** | `source.metadata.imported.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.2 Transcript Topics

#### `transcript.imported`

| Property | Value |
|----------|-------|
| **Producer** | ingestion-service (Python) |
| **Consumer** | orchestration-service (Python), content-service (Spring Boot) |
| **Partition Key** | `sourceId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `zstd` (large transcript payloads) |
| **Max Message Size** | 50 MB (transcripts can be large) |
| **Ordering** | Ordered per `sourceId` |
| **DLQ Topic** | `transcript.imported.dlq` |
| **DLQ Retention** | 30 days |

#### `transcript.normalized`

| Property | Value |
|----------|-------|
| **Producer** | ingestion-service (Python) |
| **Consumer** | orchestration-service (Python) |
| **Partition Key** | `transcriptId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `zstd` |
| **Max Message Size** | 50 MB |
| **Ordering** | Ordered per `transcriptId` |
| **DLQ Topic** | `transcript.normalized.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.3 Story Topics

#### `story.extraction.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) |
| **Consumer** | extraction-service (Python) |
| **Partition Key** | `jobId` (UUID as string) |
| **Partitions** | 6 (higher throughput expected) |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 50 MB (includes full transcript) |
| **Ordering** | No ordering requirements (parallel extraction) |
| **DLQ Topic** | `story.extraction.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `story.extracted`

| Property | Value |
|----------|-------|
| **Producer** | extraction-service (Python) |
| **Consumer** | orchestration-service (Python), content-service (Spring Boot) |
| **Partition Key** | `canonicalStoryId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `canonicalStoryId` |
| **DLQ Topic** | `story.extracted.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.4 Knowledge Topics

#### `knowledge.extraction.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) |
| **Consumer** | extraction-service (Python) |
| **Partition Key** | `jobId` (UUID as string) |
| **Partitions** | 6 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | No ordering requirements |
| **DLQ Topic** | `knowledge.extraction.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `knowledge.extracted`

| Property | Value |
|----------|-------|
| **Producer** | extraction-service (Python) |
| **Consumer** | orchestration-service (Python), knowledge-service (Spring Boot) |
| **Partition Key** | `knowledgeId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `knowledgeId` |
| **DLQ Topic** | `knowledge.extracted.dlq` |
| **DLQ Retention** | 30 days |

#### `knowledge.normalization.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) |
| **Consumer** | normalization-service (Python) |
| **Partition Key** | `jobId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | No ordering requirements |
| **DLQ Topic** | `knowledge.normalization.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `knowledge.normalized`

| Property | Value |
|----------|-------|
| **Producer** | normalization-service (Python) |
| **Consumer** | orchestration-service (Python), knowledge-service (Spring Boot) |
| **Partition Key** | `knowledgeId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `knowledgeId` |
| **DLQ Topic** | `knowledge.normalized.dlq` |
| **DLQ Retention** | 30 days |

#### `knowledge.validation.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) |
| **Consumer** | validation-service (Python) |
| **Partition Key** | `jobId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | No ordering requirements |
| **DLQ Topic** | `knowledge.validation.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `knowledge.validated`

| Property | Value |
|----------|-------|
| **Producer** | validation-service (Python) |
| **Consumer** | orchestration-service (Python), knowledge-service (Spring Boot) |
| **Partition Key** | `knowledgeId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `knowledgeId` |
| **DLQ Topic** | `knowledge.validated.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.5 Article Topics

#### `article.generation.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) |
| **Consumer** | article-service (Python) |
| **Partition Key** | `jobId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | No ordering requirements |
| **DLQ Topic** | `article.generation.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `article.generated`

| Property | Value |
|----------|-------|
| **Producer** | article-service (Python) |
| **Consumer** | orchestration-service (Python), workflow-service (Spring Boot, via bridge) |
| **Partition Key** | `articleDraftId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `articleDraftId` |
| **DLQ Topic** | `article.generated.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.6 Embedding Topics

#### `embedding.generation.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) |
| **Consumer** | embedding-service (Python) |
| **Partition Key** | `jobId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | No ordering requirements |
| **DLQ Topic** | `embedding.generation.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `embedding.generated`

| Property | Value |
|----------|-------|
| **Producer** | embedding-service (Python) |
| **Consumer** | orchestration-service (Python), weaviate-sync (Python) |
| **Partition Key** | `jobId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | No ordering requirements |
| **DLQ Topic** | `embedding.generated.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.7 Graph Projection Topics

#### `graph.projection.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) |
| **Consumer** | neo4j-sync (Python) |
| **Partition Key** | `projectionId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `projectionId` |
| **DLQ Topic** | `graph.projection.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `graph.projected`

| Property | Value |
|----------|-------|
| **Producer** | neo4j-sync (Python) |
| **Consumer** | orchestration-service (Python) |
| **Partition Key** | `projectionId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `projectionId` |
| **DLQ Topic** | `graph.projected.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.8 Review Topics

#### `review.requested`

| Property | Value |
|----------|-------|
| **Producer** | orchestration-service (Python) / content-service (Spring Boot) |
| **Consumer** | workflow-service (Spring Boot) |
| **Partition Key** | `reviewId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `compact` (keep latest review state per key) |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `reviewId` |
| **DLQ Topic** | `review.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `review.approved`

| Property | Value |
|----------|-------|
| **Producer** | workflow-service (Spring Boot) |
| **Consumer** | orchestration-service (Python, via bridge), content-service (Spring Boot), knowledge-service (Spring Boot) |
| **Partition Key** | `reviewId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `compact` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `reviewId` |
| **DLQ Topic** | `review.approved.dlq` |
| **DLQ Retention** | 30 days |

#### `review.rejected`

| Property | Value |
|----------|-------|
| **Producer** | workflow-service (Spring Boot) |
| **Consumer** | orchestration-service (Python, via bridge), content-service (Spring Boot), knowledge-service (Spring Boot) |
| **Partition Key** | `reviewId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `compact` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `reviewId` |
| **DLQ Topic** | `review.rejected.dlq` |
| **DLQ Retention** | 30 days |

### 4.2.9 Publication Topics

#### `publication.requested`

| Property | Value |
|----------|-------|
| **Producer** | workflow-service (Spring Boot) |
| **Consumer** | content-service (Spring Boot) |
| **Partition Key** | `publicationId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `publicationId` |
| **DLQ Topic** | `publication.requested.dlq` |
| **DLQ Retention** | 30 days |

#### `publication.completed`

| Property | Value |
|----------|-------|
| **Producer** | content-service (Spring Boot) |
| **Consumer** | orchestration-service (Python, via bridge), knowledge-service (Spring Boot), research-service (Spring Boot) |
| **Partition Key** | `publicationId` (UUID as string) |
| **Partitions** | 3 |
| **Retention** | 7 days |
| **Cleanup Policy** | `delete` |
| **Compression** | `lz4` |
| **Max Message Size** | 10 MB |
| **Ordering** | Ordered per `publicationId` |
| **DLQ Topic** | `publication.completed.dlq` |
| **DLQ Retention** | 30 days |

## 4.3 Topic Creation Script

Topics are created using the Redpanda CLI or Admin API. Example script:

```bash
#!/bin/bash
# create-topics.sh — Run against Redpanda cluster

RP_ADMIN="rpk topic create"
BOOTSTRAP="localhost:9092"

# Source topics
$RP_ADMIN source.submitted \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN source.metadata.imported \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

# Transcript topics (large messages, zstd compression)
$RP_ADMIN transcript.imported \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=zstd,max.message.bytes=52428800

$RP_ADMIN transcript.normalized \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=zstd,max.message.bytes=52428800

# Story topics
$RP_ADMIN story.extraction.requested \
  --partitions 6 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4,max.message.bytes=52428800

$RP_ADMIN story.extracted \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

# Knowledge topics
$RP_ADMIN knowledge.extraction.requested \
  --partitions 6 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN knowledge.extracted \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN knowledge.normalization.requested \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN knowledge.normalized \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN knowledge.validation.requested \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN knowledge.validated \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

# Article topics
$RP_ADMIN article.generation.requested \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN article.generated \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

# Embedding topics
$RP_ADMIN embedding.generation.requested \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN embedding.generated \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

# Graph projection topics
$RP_ADMIN graph.projection.requested \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN graph.projected \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

# Review topics (compacted — keep latest state per key)
$RP_ADMIN review.requested \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,cleanup.policy=compact,compression.type=lz4

$RP_ADMIN review.approved \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,cleanup.policy=compact,compression.type=lz4

$RP_ADMIN review.rejected \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,cleanup.policy=compact,compression.type=lz4

# Publication topics
$RP_ADMIN publication.requested \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

$RP_ADMIN publication.completed \
  --partitions 3 --replication-factor 3 \
  --config retention.ms=604800000,compression.type=lz4

# ============================================================
# Dead Letter Queue Topics (one per source topic)
# ============================================================
# DLQ topics use longer retention and compact cleanup
for topic in \
  source.submitted.dlq source.metadata.imported.dlq \
  transcript.imported.dlq transcript.normalized.dlq \
  story.extraction.requested.dlq story.extracted.dlq \
  knowledge.extraction.requested.dlq knowledge.extracted.dlq \
  knowledge.normalization.requested.dlq knowledge.normalized.dlq \
  knowledge.validation.requested.dlq knowledge.validated.dlq \
  article.generation.requested.dlq article.generated.dlq \
  embedding.generation.requested.dlq embedding.generated.dlq \
  graph.projection.requested.dlq graph.projected.dlq \
  review.requested.dlq review.approved.dlq review.rejected.dlq \
  publication.requested.dlq publication.completed.dlq; do
  $RP_ADMIN "$topic" \
    --partitions 1 --replication-factor 3 \
    --config retention.ms=2592000000,cleanup.policy=delete,compression.type=lz4
done
```

---

# 5. Message Envelope Standard

## 5.1 Envelope Structure

Every message published to any AI Platform topic MUST use the standard envelope defined in `AiBridgeEvent.java`:

```json
{
  "eventId": "3a1b2c3d-4e5f-6789-abcd-ef0123456789",
  "eventType": "SourceSubmitted",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T14:30:00.000Z",
  "producer": "content-service",
  "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "dataJson": "{\"sourceId\":\"b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e\",\"sourceType\":\"youtube_video\",...}",
  "tenantId": "00000000-0000-0000-0000-000000000001",
  "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f"
}
```

## 5.2 Envelope Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventId` | UUID | Yes | Unique identifier for this specific event occurrence. Used for deduplication. |
| `eventType` | String | Yes | PascalCase event name (e.g., `SourceSubmitted`, `KnowledgeValidated`). |
| `eventVersion` | Integer | Yes | Schema version of the `dataJson` payload. Starts at 1. |
| `occurredAt` | ISO8601 | Yes | Timestamp when the event was produced. UTC. |
| `producer` | String | Yes | Name of the service that produced the event (e.g., `content-service`, `extraction-service`). |
| `aggregateId` | UUID | Yes | Identifier of the domain aggregate this event relates to. Used as the partition key. |
| `dataJson` | String (JSON) | Yes | The event-specific payload serialized as a JSON string. |
| `tenantId` | UUID | No | Multi-tenant scope identifier. Required for tenant-isolated topics. |
| `correlationId` | UUID | No | End-to-end tracing identifier. Propagated across all events in a flow. |

## 5.3 Java Implementation (Producer Side)

The `AiBridgeEvent` record in `packages/shared-events`:

```java
public record AiBridgeEvent(
    UUID eventId,
    String eventType,
    int eventVersion,
    OffsetDateTime occurredAt,
    String producer,
    UUID aggregateId,
    String dataJson,
    UUID tenantId,
    UUID correlationId
) {
    public AiBridgeEvent {
        eventId = UUID.randomUUID();
        occurredAt = OffsetDateTime.now();
        eventVersion = 1;
    }

    public AiBridgeEvent(String eventType, String producer, UUID aggregateId, String dataJson) {
        this(null, eventType, 1, null, producer, aggregateId, dataJson, null, null);
    }

    public AiBridgeEvent(String eventType, String producer, UUID aggregateId, String dataJson, UUID tenantId) {
        this(null, eventType, 1, null, producer, aggregateId, dataJson, tenantId, null);
    }
}
```

## 5.4 Python Implementation (Consumer Side)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class AiBridgeEvent(BaseModel):
    eventId: UUID
    eventType: str
    eventVersion: int
    occurredAt: datetime
    producer: str
    aggregateId: UUID
    dataJson: str
    tenantId: Optional[UUID] = None
    correlationId: Optional[UUID] = None

    def parse_data(self) -> dict:
        """Parse the dataJson string into a Python dictionary."""
        import json
        return json.loads(self.dataJson)
```

## 5.5 Full Message Example (Wire Format)

When serialized to the Redpanda topic, the message key and value are:

**Key:** `b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e` (the `aggregateId` as string)

**Value:**
```json
{
  "eventId": "3a1b2c3d-4e5f-6789-abcd-ef0123456789",
  "eventType": "SourceSubmitted",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T14:30:00.000Z",
  "producer": "content-service",
  "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "dataJson": "{\"sourceId\":\"b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e\",\"sourceType\":\"youtube_video\",\"externalUrl\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\",\"platformSourceId\":\"dQw4w9WgXcQ\",\"channelId\":\"a1b2c3d4-e5f6-7890-abcd-ef1234567890\",\"title\":\"Misteri Kuntilanak di Desa Sukamaju\",\"description\":\"Dokumentasi wawancara dengan warga...\",\"language\":\"id\",\"submittedBy\":\"f1e2d3c4-b5a6-7890-fedc-ba9876543210\",\"submittedAt\":\"2026-06-20T14:30:00Z\"}",
  "tenantId": "00000000-0000-0000-0000-000000000001",
  "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f"
}
```

## 5.6 Headers

The following standard headers MUST be set on every message:

| Header | Value | Description |
|--------|-------|-------------|
| `content-type` | `application/json` | Message content type |
| `ce-specversion` | `1.0` | CloudEvents specification version |
| `ce-type` | `SourceSubmitted` | CloudEvents type (same as `eventType`) |
| `ce-source` | `content-service` | CloudEvents source (same as `producer`) |
| `ce-id` | `3a1b2c3d-...` | CloudEvents ID (same as `eventId`) |
| `ce-correlationid` | `c1d2e3f4-...` | CloudEvents correlation ID |
| `x-tenant-id` | `00000000-...` | Tenant ID for multi-tenant routing |

## 5.7 Message Key Strategy

The message key determines partition assignment and ordering guarantees.

| Topic Type | Key | Rationale |
|-----------|-----|-----------|
| Source topics | `sourceId` | All events for a source must be ordered |
| Transcript topics | `transcriptId` | All events for a transcript must be ordered |
| Story topics | `canonicalStoryId` | All events for a story must be ordered |
| Knowledge topics | `knowledgeId` | All events for a knowledge object must be ordered |
| Request topics | `jobId` | No ordering needed; parallel processing desired |
| Review topics | `reviewId` | All events for a review must be ordered |
| Publication topics | `publicationId` | All events for a publication must be ordered |

---

# 6. Message Schema Governance

## 6.1 Schema Registry

All topics MUST be registered in the Redpanda Schema Registry (or Apicurio for Spring Boot services).

**Schema Registry URL:** `http://redpanda-schema-registry:8081`

**Registration requirements:**
- Every event type + version combination gets a unique schema ID.
- Schemas are registered in `AVRO` or `JSON Schema` format.
- Compatibility mode: `BACKWARD` (default).

## 6.2 Schema Evolution Rules

| Change | Allowed? | Compatibility | Example |
|--------|----------|---------------|---------|
| Add optional field | Yes | BACKWARD | Add `warnings` array to validation result |
| Add required field | No (new version) | FORWARD | Must create new major version |
| Remove field | No (new version) | FORWARD | Must create new major version |
| Rename field | No (new version) | NONE | Must create new major version |
| Change field type | No (new version) | NONE | Must create new major version |
| Relax constraint | Yes | BACKWARD | Change `minLength` from 10 to 5 |
| Tighten constraint | No (new version) | FORWARD | Change `minLength` from 5 to 10 |
| Add enum value | Yes | BACKWARD | Add new `sourceType` value |
| Remove enum value | No (new version) | FORWARD | Must create new major version |

## 6.3 Schema Registration Process

```
1. Developer defines schema in the service's schema directory
   e.g., ai-platform/extraction-service/schemas/story-extracted-v1.json

2. On deployment, schema is registered with Schema Registry
   POST /subjects/story.extracted-value/versions
   {
     "schema": "{...JSON Schema...}",
     "schemaType": "JSON"
   }

3. Schema Registry validates compatibility
   - If BACKWARD compatible: accepted
   - If not compatible: rejected, deployment fails

4. Producer and consumer both reference the schema ID
   - Producer: includes schema ID in message headers
   - Consumer: validates message against registered schema
```

## 6.4 Schema Validation

### Producer-Side Validation
- Every producer MUST validate messages against the registered schema before publishing.
- Validation failure MUST prevent publishing and log an error.
- Schema validation is the first line of defense against contract violations.

### Consumer-Side Validation
- Every consumer SHOULD validate incoming messages against the registered schema.
- Schema validation failures MUST be routed to DLQ immediately (no retry).
- Consumers MUST tolerate unknown fields (ignore, do not crash).

### Validation Implementation

**Python (AI Workers):**
```python
from jsonschema import validate, ValidationError
import json

def validate_message(event_type: str, event_version: int, data: dict):
    schema = load_schema(event_type, event_version)
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise SchemaValidationError(f"Schema validation failed: {e.message}")
```

**Java (Spring Boot):**
```java
// Using Spring Kafka with JsonSerializer/JsonDeserializer
// Validation is implicit via type binding
// Explicit validation can be added with a Validator bean
```

## 6.5 Schema Directory Structure

Schemas are stored alongside the service that owns them:

```
ai-platform/
├── ingestion-service/
│   └── schemas/
│       ├── source-metadata-imported-v1.json
│       ├── transcript-imported-v1.json
│       └── transcript-normalized-v1.json
├── extraction-service/
│   └── schemas/
│       ├── story-extracted-v1.json
│       └── knowledge-extracted-v1.json
├── normalization-service/
│   └── schemas/
│       └── knowledge-normalized-v1.json
├── validation-service/
│   └── schemas/
│       └── knowledge-validated-v1.json
├── article-service/
│   └── schemas/
│       └── article-generated-v1.json
├── embedding-service/
│   └── schemas/
│       └── embedding-generated-v1.json
├── orchestration-service/
│   └── schemas/
│       ├── story-extraction-requested-v1.json
│       ├── knowledge-extraction-requested-v1.json
│       ├── knowledge-normalization-requested-v1.json
│       ├── knowledge-validation-requested-v1.json
│       ├── article-generation-requested-v1.json
│       ├── embedding-generation-requested-v1.json
│       └── graph-projection-requested-v1.json
└── shared/
    └── schemas/
        ├── ai-bridge-event-envelope.json
        └── dlq-envelope.json
```

## 6.6 Example Schema (JSON Schema)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://livingatlas.id/schemas/knowledge-validated-v1.json",
  "title": "KnowledgeValidated",
  "description": "Schema for the KnowledgeValidated event (v1)",
  "type": "object",
  "properties": {
    "knowledgeId": {
      "type": "string",
      "format": "uuid",
      "description": "The knowledge object that was validated"
    },
    "canonicalStoryId": {
      "type": "string",
      "format": "uuid"
    },
    "sourceId": {
      "type": "string",
      "format": "uuid"
    },
    "jobId": {
      "type": "string",
      "format": "uuid"
    },
    "validatedAt": {
      "type": "string",
      "format": "date-time"
    },
    "validationResult": {
      "type": "object",
      "properties": {
        "overallScore": { "type": "number", "minimum": 0, "maximum": 1 },
        "passed": { "type": "boolean" },
        "schemaValid": { "type": "boolean" },
        "completenessScore": { "type": "number" },
        "confidenceScore": { "type": "number" },
        "consistencyScore": { "type": "number" }
      },
      "required": ["overallScore", "passed"]
    },
    "warnings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },
          "target": { "type": "string" },
          "targetId": { "type": "string", "format": "uuid" },
          "message": { "type": "string" },
          "severity": { "type": "string", "enum": ["low", "medium", "high"] }
        }
      }
    },
    "issues": { "type": "array" },
    "validationMetadata": {
      "type": "object",
      "properties": {
        "modelUsed": { "type": "string" },
        "promptVersion": { "type": "string" },
        "inputTokens": { "type": "integer" },
        "outputTokens": { "type": "integer" },
        "executionCost": { "type": "number" },
        "executionTimeMs": { "type": "integer" }
      }
    }
  },
  "required": [
    "knowledgeId", "canonicalStoryId", "sourceId",
    "jobId", "validatedAt", "validationResult"
  ]
}
```

---

# 7. Retry Strategy

## 7.1 Retry Classification

| Failure Category | Retryable? | Examples |
|-----------------|-----------|----------|
| **Transient** | Yes | Rate limit (429), temporary outage (5xx), timeout, network failure |
| **Schema** | No | Validation failure, unknown field type, missing required field |
| **Business Logic** | No | Invalid state transition, missing reference data, corrupt payload |
| **Poison Message** | No | Message that consistently fails with the same business logic error |

## 7.2 Retry Schedule

| Retry | Delay | Cumulative |
|-------|-------|------------|
| 1 | 1 minute | 1 minute |
| 2 | 5 minutes | 6 minutes |
| 3 | 15 minutes | 21 minutes |
| 4 | 1 hour | 1 hour 21 minutes |
| 5 | 1 hour | 2 hours 21 minutes |

**Total time before DLQ:** ~2 hours 21 minutes.

## 7.3 Retry Implementation

### Python Worker (AI Platform)

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import aiokafka

class TransientError(Exception):
    """Retryable error (rate limit, timeout, network)."""
    pass

class NonRetryableError(Exception):
    """Non-retryable error (schema, business logic)."""
    pass

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=60, max=3600),
    retry=retry_if_exception_type(TransientError),
    before_sleep=lambda retry_state: log.warning(
        f"Retry {retry_state.attempt_number}/5 after {retry_state.outcome.exception()}"
    )
)
async def process_message(message: AiBridgeEvent):
    try:
        data = message.parse_data()
        validate_schema(message.eventType, message.eventVersion, data)
        await process_business_logic(data)
    except SchemaValidationError as e:
        raise NonRetryableError(str(e)) from e
    except BusinessLogicError as e:
        raise NonRetryableError(str(e)) from e
    except (ConnectionError, TimeoutError) as e:
        raise TransientError(str(e)) from e
```

### Spring Boot Consumer (Backend)

```java
@KafkaListener(topics = "${topic.source.metadata.imported}", groupId = "content-source")
public void onSourceMetadataImported(
    @Payload AiBridgeEvent event,
    @Header(KafkaHeaders.RECEIVED_KEY) String key,
    Acknowledgment ack
) {
    try {
        processEvent(event);
        ack.acknowledge();
    } catch (TransientException e) {
        // Will be retried by Spring Kafka's retry template
        throw e;
    } catch (NonRetryableException e) {
        // Send to DLQ immediately
        deadLetterPublisher.publish(event, e);
        ack.acknowledge();
    }
}
```

## 7.4 Dead Letter Queue (DLQ)

### DLQ Topic Naming

Each source topic has a corresponding DLQ topic:

```
{source-topic}.dlq
```

Example: `source.submitted` → `source.submitted.dlq`

### DLQ Message Envelope

```json
{
  "originalEvent": {
    "eventId": "3a1b2c3d-4e5f-6789-abcd-ef0123456789",
    "eventType": "SourceSubmitted",
    "eventVersion": 1,
    "occurredAt": "2026-06-20T14:30:00.000Z",
    "producer": "content-service",
    "aggregateId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "dataJson": "{...}",
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f"
  },
  "dlqMetadata": {
    "failedAt": "2026-06-20T16:00:00.000Z",
    "failedConsumer": "extraction-service",
    "consumerGroup": "extraction-story",
    "failureReason": "Rate limit exceeded after 5 retries",
    "failureType": "rate_limit",
    "retryCount": 5,
    "lastError": "429 Too Many Requests",
    "lastErrorTraceback": "Traceback (most recent call last):\n  ..."
  }
}
```

### DLQ Configuration

| Parameter | Value |
|-----------|-------|
| Partitions | 1 (single partition for ordered inspection) |
| Replication Factor | 3 (production) |
| Retention | 30 days |
| Cleanup Policy | `delete` |
| Compression | `lz4` |

## 7.5 Replay Strategy

### Automated Replay (CLI Tool)

```bash
# Replay all messages from DLQ back to source topic
redpanda-replay \
  --dlq source.submitted.dlq \
  --topic source.submitted \
  --bootstrap localhost:9092

# Replay a specific message by eventId
redpanda-replay \
  --dlq source.submitted.dlq \
  --topic source.submitted \
  --message-id 3a1b2c3d-4e5f-6789-abcd-ef0123456789

# Replay with rate limiting (messages per second)
redpanda-replay \
  --dlq knowledge.validated.dlq \
  --topic knowledge.validated \
  --rate-limit 10
```

### Manual Replay (PostgreSQL Dead Letter Table)

For Spring Boot services using transactional outbox:

```sql
-- View dead letter events
SELECT * FROM system.dead_letter_events
WHERE status = 'quarantined'
ORDER BY created_at DESC;

-- Replay a specific event
UPDATE system.dead_letter_events
SET status = 'pending', resolved_at = now(), resolved_by = 'admin'
WHERE id = '...';

-- The outbox publisher will pick it up and republish
```

---

# 8. Idempotency Strategy

## 8.1 Duplicate Prevention

Every consumer MUST maintain a deduplication store to prevent processing the same message twice.

### Deduplication Table (PostgreSQL)

```sql
CREATE TABLE ai_platform.processed_events (
    event_id UUID PRIMARY KEY,
    consumer VARCHAR(255) NOT NULL,       -- consumer group name
    topic VARCHAR(255) NOT NULL,
    partition INTEGER NOT NULL,
    offset BIGINT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT now() + interval '30 days'
);

-- Index for cleanup queries
CREATE INDEX idx_processed_events_expires
    ON ai_platform.processed_events(expires_at);

-- Unique constraint to prevent race conditions
CREATE UNIQUE INDEX idx_processed_events_unique
    ON ai_platform.processed_events(event_id, consumer);
```

### Deduplication Logic (Python)

```python
import asyncpg

class DeduplicationStore:
    def __init__(self, pool: asyncpg.Pool, consumer: str):
        self.pool = pool
        self.consumer = consumer

    async def is_already_processed(self, event_id: str) -> bool:
        """Check if an event has already been processed."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT 1 FROM ai_platform.processed_events "
                "WHERE event_id = $1 AND consumer = $2",
                event_id, self.consumer
            )
            return result is not None

    async def mark_processed(self, event_id: str, topic: str,
                              partition: int, offset: int):
        """Mark an event as processed."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO ai_platform.processed_events "
                "(event_id, consumer, topic, partition, offset) "
                "VALUES ($1, $2, $3, $4, $5) "
                "ON CONFLICT (event_id, consumer) DO NOTHING",
                event_id, self.consumer, topic, partition, offset
            )
```

### Deduplication Logic (Java)

```java
@Component
public class DeduplicationStore {

    @Autowired
    private JdbcTemplate jdbc;

    public boolean isAlreadyProcessed(UUID eventId, String consumer) {
        Integer count = jdbc.queryForObject(
            "SELECT 1 FROM ai_platform.processed_events " +
            "WHERE event_id = ? AND consumer = ?",
            Integer.class, eventId, consumer
        );
        return count != null && count > 0;
    }

    @Transactional
    public void markProcessed(UUID eventId, String consumer,
                               String topic, int partition, long offset) {
        jdbc.update(
            "INSERT INTO ai_platform.processed_events " +
            "(event_id, consumer, topic, partition, offset) " +
            "VALUES (?, ?, ?, ?, ?) " +
            "ON CONFLICT (event_id, consumer) DO NOTHING",
            eventId, consumer, topic, partition, offset
        );
    }
}
```

## 8.2 Consumer Processing Flow

```
1. Receive message from Redpanda
2. Parse envelope (AiBridgeEvent)
3. Check dedup store for eventId + consumer
   ├── If found: log "duplicate", acknowledge, skip
   └── If not found: continue
4. Validate schema
   ├── If invalid: send to DLQ, acknowledge, stop
   └── If valid: continue
5. Process business logic
   ├── If transient error: retry (up to 5 times)
   ├── If non-retryable error: send to DLQ, acknowledge, stop
   └── If success: continue
6. Mark event as processed in dedup store
7. Publish result event (if applicable)
8. Acknowledge message (commit offset)
```

## 8.3 Idempotent Writes

All database writes MUST be idempotent:

```sql
-- Use ON CONFLICT for upserts
INSERT INTO ai_platform.jobs (job_id, job_type, status, ...)
VALUES ($1, $2, $3, ...)
ON CONFLICT (job_id) DO NOTHING;

-- Use idempotent updates
UPDATE ai_platform.jobs
SET status = 'completed', completed_at = now()
WHERE job_id = $1 AND status != 'completed';
```

## 8.4 Safe Message Replay

Messages can be replayed from DLQ or from the original topic at any time. The system MUST handle replay safely:

1. **Dedup table prevents double processing:** Replayed messages with the same `eventId` are silently skipped.
2. **Idempotent writes prevent data corruption:** `INSERT ... ON CONFLICT DO NOTHING` ensures no duplicate rows.
3. **Deterministic AI calls:** Identical input produces identical output (same model, same prompt, same temperature).
4. **No side effects on replay:** External API calls (e.g., webhooks, emails) must be idempotent or guarded by the dedup store.

## 8.5 Dedup Table Cleanup

The dedup table retains entries for 30 days. A scheduled job cleans expired entries:

```sql
-- Run daily via cron/scheduler
DELETE FROM ai_platform.processed_events
WHERE expires_at < now();
```

---

# 9. Security

## 9.1 Encryption

### In-Transit Encryption

All Redpanda communication MUST use TLS 1.3:

```
redpanda.bootstrap-servers=redpanda-cluster:9093
redpanda.security.protocol=SASL_SSL
redpanda.ssl.truststore.location=/etc/redpanda/certs/ca.pem
redpanda.ssl.keystore.location=/etc/redpanda/certs/client.pem
redpanda.ssl.keystore.password=${SSL_KEYSTORE_PASSWORD}
```

### At-Rest Encryption

Redpanda data directories MUST be encrypted at the filesystem level (LUKS or equivalent).

## 9.2 Authentication

### SASL/SCRAM Authentication

All producers and consumers MUST authenticate using SASL/SCRAM-SHA-512:

**Python (AI Workers):**
```python
consumer = AIOKafkaConsumer(
    bootstrap_servers='redpanda-cluster:9093',
    security_protocol='SASL_SSL',
    sasl_mechanism='SCRAM-SHA-512',
    sasl_plain_username='${REDPANDA_USERNAME}',
    sasl_plain_password='${REDPANDA_PASSWORD}',
    ssl_context=ssl_context,
    group_id='extraction-story'
)
```

**Java (Spring Boot):**
```yaml
spring:
  kafka:
    bootstrap-servers: redpanda-cluster:9093
    properties:
      security.protocol: SASL_SSL
      sasl.mechanism: SCRAM-SHA-512
      sasl.jaas.config: >
        org.apache.kafka.common.security.scram.ScramLoginModule
        required
        username="${REDPANDA_USERNAME}"
        password="${REDPANDA_PASSWORD}";
    ssl:
      truststore-location: classpath:redpanda-ca.pem
      truststore-password: ${SSL_TRUSTSTORE_PASSWORD}
```

### Service Accounts

| Service | Redpanda Username | Permissions |
|---------|------------------|-------------|
| content-service | `svc-content` | Produce: `source.submitted`, `publication.completed`; Consume: `source.metadata.imported`, `story.extracted`, `article.generated`, `review.approved`, `review.rejected` |
| knowledge-service | `svc-knowledge` | Consume: `knowledge.extracted`, `knowledge.validated` |
| workflow-service | `svc-workflow` | Produce: `review.approved`, `review.rejected`, `publication.requested`; Consume: `review.requested` |
| orchestration-service | `svc-orchestration` | Produce: `story.extraction.requested`, `knowledge.extraction.requested`, `knowledge.normalization.requested`, `knowledge.validation.requested`, `article.generation.requested`, `embedding.generation.requested`, `graph.projection.requested`; Consume: `source.submitted`, `transcript.imported`, `transcript.normalized`, `story.extracted`, `knowledge.extracted`, `knowledge.normalized`, `knowledge.validated`, `article.generated`, `embedding.generated`, `graph.projected`, `review.approved`, `review.rejected`, `publication.completed` |
| ingestion-service | `svc-ingestion` | Produce: `source.metadata.imported`, `transcript.imported`, `transcript.normalized`; Consume: `source.submitted` |
| extraction-service | `svc-extraction` | Produce: `story.extracted`, `knowledge.extracted`; Consume: `story.extraction.requested`, `knowledge.extraction.requested` |
| normalization-service | `svc-normalization` | Produce: `knowledge.normalized`; Consume: `knowledge.normalization.requested` |
| validation-service | `svc-validation` | Produce: `knowledge.validated`; Consume: `knowledge.validation.requested` |
| article-service | `svc-article` | Produce: `article.generated`; Consume: `article.generation.requested` |
| embedding-service | `svc-embedding` | Produce: `embedding.generated`; Consume: `embedding.generation.requested` |
| neo4j-sync | `svc-neo4j` | Produce: `graph.projected`; Consume: `graph.projection.requested` |
| weaviate-sync | `svc-weaviate` | Consume: `embedding.generated` |

## 9.3 Authorization (ACLs)

Redpanda ACLs enforce topic-level access control:

```bash
# Grant producer permissions
rpk acl create --allow-principal User:svc-content \
  --operation write --operation describe \
  --topic source.submitted

# Grant consumer permissions
rpk acl create --allow-principal User:svc-orchestration \
  --operation read --operation describe \
  --topic source.submitted \
  --consumer-group orchestration-source

# Grant DLQ producer permissions (for failed messages)
rpk acl create --allow-principal User:svc-orchestration \
  --operation write --operation describe \
  --topic source.submitted.dlq

# Deny all other access (default deny)
rpk acl create --deny-principal User:svc-content \
  --operation all --topic source.submitted.dlq
```

### ACL Matrix

| Topic | Producers | Consumers |
|-------|-----------|-----------|
| `source.submitted` | svc-content | svc-orchestration |
| `source.metadata.imported` | svc-ingestion | svc-content, svc-orchestration |
| `transcript.imported` | svc-ingestion | svc-orchestration, svc-content |
| `transcript.normalized` | svc-ingestion | svc-orchestration |
| `story.extraction.requested` | svc-orchestration | svc-extraction |
| `story.extracted` | svc-extraction | svc-orchestration, svc-content |
| `knowledge.extraction.requested` | svc-orchestration | svc-extraction |
| `knowledge.extracted` | svc-extraction | svc-orchestration, svc-knowledge |
| `knowledge.normalization.requested` | svc-orchestration | svc-normalization |
| `knowledge.normalized` | svc-normalization | svc-orchestration, svc-knowledge |
| `knowledge.validation.requested` | svc-orchestration | svc-validation |
| `knowledge.validated` | svc-validation | svc-orchestration, svc-knowledge |
| `article.generation.requested` | svc-orchestration | svc-article |
| `article.generated` | svc-article | svc-orchestration, svc-workflow |
| `embedding.generation.requested` | svc-orchestration | svc-embedding |
| `embedding.generated` | svc-embedding | svc-orchestration, svc-weaviate |
| `graph.projection.requested` | svc-orchestration | svc-neo4j |
| `graph.projected` | svc-neo4j | svc-orchestration |
| `review.requested` | svc-orchestration, svc-content | svc-workflow |
| `review.approved` | svc-workflow | svc-orchestration, svc-content, svc-knowledge |
| `review.rejected` | svc-workflow | svc-orchestration, svc-content, svc-knowledge |
| `publication.requested` | svc-workflow | svc-content |
| `publication.completed` | svc-content | svc-orchestration, svc-knowledge, svc-research |

## 9.4 Tenant Isolation

### Topic-Level Isolation

For multi-tenant deployments, topics can be prefixed with the tenant ID:

```
{tenant-id}.source.submitted
{tenant-id}.knowledge.validated
```

**When to use:**
- Regulatory requirements (data residency, GDPR).
- Hard isolation between tenants.
- Different retention policies per tenant.

**When NOT to use:**
- Single-tenant deployments.
- Shared infrastructure with logical isolation (prefer `tenantId` field).

### Logical Isolation (Default)

Tenant isolation is achieved via the `tenantId` field in the message envelope:

```json
{
  "tenantId": "00000000-0000-0000-0000-000000000001",
  ...
}
```

Consumers MUST filter by `tenantId` and MUST NOT process messages for tenants they are not authorized for.

### Tenant Authorization

```python
async def process_message(message: AiBridgeEvent):
    if not is_authorized_for_tenant(message.tenantId):
        raise AuthorizationError(
            f"Consumer not authorized for tenant {message.tenantId}"
        )
    # Continue processing...
```

---

# 10. Monitoring

## 10.1 Consumer Lag Monitoring

Every consumer group MUST be monitored for lag.

### Lag Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `consumer_lag` | Number of messages behind the latest offset | > 1000 |
| `consumer_lag_ms` | Estimated time behind in milliseconds | > 60000 (1 minute) |
| `consumer_lag_max` | Maximum lag across all partitions | > 5000 |

### Lag Monitoring Command

```bash
# Check lag for all consumer groups
rpk group list
rpk group describe orchestration-source
rpk group describe extraction-story
```

### Lag Monitoring (Prometheus + Redpanda Exporter)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'redpanda'
    static_configs:
      - targets: ['redpanda-exporter:9644']
```

**Key metrics from Redpanda exporter:**
```
# Consumer lag per group + topic + partition
kafka_consumer_group_lag{group="extraction-story", topic="story.extraction.requested", partition="0"}

# Consumer offset
kafka_consumer_group_current_offset{group="extraction-story", topic="story.extraction.requested"}

# Producer offset (latest)
kafka_topic_partition_current_offset{topic="story.extraction.requested"}
```

## 10.2 Consumer Health

### Health Check Endpoint

Every consumer MUST expose a `/health` endpoint:

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
      "consumerGroup": "extraction-story",
      "partitionAssignments": [0, 1, 2],
      "lag": 0,
      "lastProcessed": "2026-06-20T15:08:30Z",
      "messagesProcessed": 1542,
      "messagesFailed": 3
    },
    "knowledge.extraction.requested": {
      "status": "RUNNING",
      "consumerGroup": "extraction-knowledge",
      "partitionAssignments": [3, 4],
      "lag": 5,
      "lastProcessed": "2026-06-20T15:12:00Z",
      "messagesProcessed": 892,
      "messagesFailed": 1
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

### Consumer Status States

| State | Description |
|-------|-------------|
| `RUNNING` | Consumer is active and processing messages |
| `STOPPED` | Consumer is not running |
| `STALLED` | Consumer is running but not making progress (lag increasing) |
| `DEGRADED` | Consumer is running with errors (high failure rate) |
| `UNKNOWN` | Health check could not determine status |

## 10.3 Queue Depth Monitoring

### Queue Depth Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| `queue_depth` | Current number of unprocessed messages | Redpanda exporter |
| `queue_depth_rate` | Rate of messages entering the queue | Redpanda exporter |
| `queue_depth_avg` | Average queue depth over 5 minutes | Prometheus |

### Alert Rules

```yaml
# prometheus-rules.yml
groups:
  - name: queue_alerts
    rules:
      - alert: HighConsumerLag
        expr: kafka_consumer_group_lag > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Consumer lag > 1000 for {{ $labels.group }} on {{ $labels.topic }}"

      - alert: CriticalConsumerLag
        expr: kafka_consumer_group_lag > 5000
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Consumer lag > 5000 for {{ $labels.group }} on {{ $labels.topic }}"

      - alert: ConsumerDown
        expr: up{job="ai-worker"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AI worker {{ $labels.instance }} is down"

      - alert: HighFailureRate
        expr: rate(ai_events_failed_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Failure rate > 10% for {{ $labels.consumer }} on {{ $labels.event_type }}"

      - alert: DLQMessagesAccumulating
        expr: sum(kafka_topic_partition_current_offset{topic=~".*\\.dlq"}) > 0
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Messages accumulating in DLQ topics"
```

## 10.4 Failure Rate Monitoring

### Failure Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ai_events_produced_total` | Counter | `event_type`, `producer` | Total events produced |
| `ai_events_consumed_total` | Counter | `event_type`, `consumer` | Total events consumed |
| `ai_events_failed_total` | Counter | `event_type`, `consumer`, `failure_type` | Total events that failed |
| `ai_events_retry_total` | Counter | `event_type`, `consumer`, `retry_count` | Total events retried |
| `ai_events_dlq_total` | Counter | `event_type`, `failure_type` | Total events sent to DLQ |
| `ai_event_processing_duration_ms` | Histogram | `event_type`, `consumer` | Processing time per event |
| `ai_consumer_lag` | Gauge | `consumer_group`, `topic`, `partition` | Current consumer lag |

### Failure Rate Dashboard (Grafana)

```
Panel: Events Processed (rate)
  - Query: rate(ai_events_consumed_total[5m])
  - Group by: event_type

Panel: Failure Rate
  - Query: rate(ai_events_failed_total[5m]) / rate(ai_events_consumed_total[5m])
  - Group by: consumer
  - Threshold: 0.05 (5%)

Panel: DLQ Accumulation
  - Query: sum(ai_events_dlq_total) by (event_type)
  - Show: bar chart

Panel: Consumer Lag
  - Query: ai_consumer_lag
  - Group by: consumer_group, topic
  - Show: table with color coding

Panel: Processing Duration (p95)
  - Query: histogram_quantile(0.95, rate(ai_event_processing_duration_ms_bucket[5m]))
  - Group by: event_type
```

## 10.5 Logging

### Structured Log Format

All workers MUST emit structured JSON logs:

```json
{
  "timestamp": "2026-06-20T15:08:30.123Z",
  "level": "INFO",
  "service": "extraction-service",
  "consumer": "extraction-story",
  "eventId": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "topic": "story.extraction.requested",
  "partition": 2,
  "offset": 1542,
  "message": "Message processed successfully",
  "extras": {
    "processingTimeMs": 12450,
    "inputTokens": 4502,
    "outputTokens": 1280
  }
}
```

### Log Levels

| Level | Usage |
|-------|-------|
| `ERROR` | Non-retryable failures, DLQ routing, schema validation failures |
| `WARN` | Retryable failures, transient errors, high latency |
| `INFO` | Message processed, job started/completed, state transitions |
| `DEBUG` | Detailed processing steps, AI provider responses (enable only for debugging) |

## 10.6 Alerting

### PagerDuty / OpsGenie Integration

| Alert | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| Consumer down | Critical | 5 minutes | Restart consumer |
| Lag > 5000 | Critical | 15 minutes | Scale consumer, investigate bottleneck |
| Lag > 1000 | Warning | 1 hour | Monitor, investigate if persistent |
| Failure rate > 10% | Warning | 1 hour | Investigate error logs |
| DLQ messages accumulating | Warning | 4 hours | Review DLQ, replay if appropriate |
| Schema validation errors | Warning | 4 hours | Check schema compatibility, fix producer |

---

# References

- **ADR-004:** Event-Driven Architecture with Transactional Outbox
- **ADR-009:** AI Pipeline Integration
- **PRD.md:** AI Platform Product Requirements Document
- **docs/ai-platform/domain-event-catalog.md:** AI Platform Domain Event Catalog (complement)
- **EventTopics.java:** Topic registry in `packages/shared-events`
- **AiBridgeEvent.java:** Event envelope implementation in `packages/shared-events`
- **RedpandaConfig.java:** Spring Boot Redpanda configuration in `services/content-service`
- **AiEventPublisher.java:** Event publishing implementation in `services/content-service`