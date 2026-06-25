# ADR-001: PostgreSQL as Single Source of Truth with Projection Architecture

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture operates across three distinct data paradigms:

1. **Transactional/Relational** — Stories, sources, transcripts, claims, articles, users, workflows, audit logs. Requires ACID compliance, strong consistency, complex queries across bounded contexts, and immutable versioning.
2. **Graph** — Knowledge graph of entities (spirits, creatures, locations, rituals, beliefs), their relationships, and cultural hierarchies. Requires traversal queries, path finding, and graph analytics.
3. **Vector** — Semantic search over embeddings for stories, knowledge objects, claims, and transcripts. Requires similarity search, clustering, and hybrid search over unstructured content.

Each paradigm demands a different database engine. Without clear ownership rules, three database systems would each claim to be authoritative, creating split-brain scenarios where data diverges across stores and provenance becomes unrecoverable.

## Technical Context

The platform stack includes:

- **PostgreSQL 18** — ACID-compliant relational database with native JSONB, logical replication, partitioning, and event triggers.
- **Neo4j 5.26** — Native graph database with Cypher query language, property graph model, and graph projection capabilities.
- **Weaviate 1.37** — Vector database with hybrid search, multi-tenancy, and built-in embedding support.
- **Redpanda** — Kafka-compatible event streaming backbone for asynchronous communication.

The AI Platform produces knowledge asynchronously via queue-driven workers that write results to PostgreSQL. The projection layer reads from PostgreSQL and synchronizes to Neo4j and Weaviate.

## Constraints

1. **Provenance requirement**: Every knowledge object must be traceable to its source transcript segment and original source material. Any write that bypasses this chain breaks provenance.
2. **Human review requirement**: AI-generated outputs must be reviewed before publication. Graph/vector projections must only reflect reviewed and approved data.
3. **Immutable versioning**: Updates create new versions — never overwrite. Projections must handle version chains correctly.
4. **Multi-tenant isolation**: All queries must be tenant-scoped. Projection logic must respect tenant boundaries.
5. **Event-driven AI**: Backend communicates with AI workers exclusively through Redpanda events. AI workers write results to PostgreSQL. No REST calls to AI services.
6. **99.5% availability target**: Recovery from projection failures must be automated and fast.

## Problem Statement

With three specialized databases in the architecture, how do we prevent data inconsistency, ensure provenance integrity, enable recoverability, and maintain operational simplicity at the target scale of 100,000 stories, 10,000,000 transcript segments, 1,000,000 knowledge objects, and 100,000,000 graph relationships?

# Decision

**PostgreSQL is the single source of truth for all operational data.**

**Neo4j is a read-only graph projection.**

**Weaviate is a read-only vector projection.**

**Applications must never write directly to Neo4j.**

**Applications must never write directly to Weaviate.**

**All projections originate from PostgreSQL events.**

## Architecture

```
                              ┌─────────────────────────────┐
                              │     Domain Services         │
                              │  (Identity, Content,        │
                              │   Knowledge, Research,      │
                              │   Workflow)                 │
                              │                              │
                              │  WRITE / READ                │
                              │         │                    │
                              └─────────┼────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────────────┐
                              │      PostgreSQL 18           │
                              │   (Single Source of Truth)   │
                              │                              │
                              │  ┌───────────────────────┐   │
                              │  │ Transactional Outbox  │   │
                              │  │ (outbox table per     │   │
                              │  │  bounded context)     │   │
                              │  └───────────┬───────────┘   │
                              └─────────────┼─────────────────┘
                                            │
                                            ▼
                              ┌─────────────────────────────┐
                              │       Redpanda               │
                              │                              │
                              │  Topics:                     │
                              │  - story.projected           │
                              │  - knowledge.projected       │
                              │  - graph.projection.requested│
                              │  - embedding.requested       │
                              └─────────────┬─────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
      ┌────────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
      │   Graph Projection    │  │ Vector Projection  │  │   AI Platform      │
      │   Worker              │  │ Worker             │  │   Workers          │
      │                       │  │                    │  │                    │
      │  Consumes:            │  │ Consumes:          │  │ Consumes:          │
      │  - graph.projection   │  │ - embedding.       │  │ - extraction.      │
      │    .requested         │  │   requested        │  │   requested        │
      │                       │  │                    │  │                    │
      │  Reads from PG        │  │ Reads from PG      │  │ Writes to PG       │
      └───────────┬───────────┘  └───────────┬────────┘  └────────────────────┘
                  │                          │
                  ▼                          ▼
      ┌────────────────────────┐  ┌────────────────────┐
      │      Neo4j 5.26        │  │   Weaviate 1.37    │
      │   (Read Only Graph)    │  │ (Read Only Vector) │
      │                        │  │                    │
      │  - Knowledge graph     │  │ - Story embeddings │
      │  - Entity relationships │  │ - Knowledge        │
      │  - Cultural hierarchies │  │   embeddings       │
      │  - Temporal graphs     │  │ - Claim embeddings │
      └────────────────────────┘  └────────────────────┘
```

## Detailed Decision Rules

### Rule 1: PostgreSQL Owns All Writes

Every create, update, and delete operation across all bounded contexts must go through PostgreSQL. This includes:

- Identity data (users, roles, tenants, workspaces, API keys)
- Source data (channels, sources, transcripts, metadata)
- Story data (stories, versions, relationships)
- Knowledge data (knowledge objects, claims, entities, folklore, beliefs, traditions)
- Article data (narrative, knowledge, news, creative articles)
- Workflow data (reviews, approvals, publications, moderation)
- Research data (collections, annotations, notes, exports)
- Audit data (audit logs, lineage records)
- AI Platform outputs (canonical stories, extracted knowledge, generated articles, embeddings metadata)

### Rule 2: Neo4j Is a Read-Only Graph Projection

Neo4j must only be updated by the graph projection worker. The worker:

- Reads new or changed data from PostgreSQL
- Transforms relational data into graph nodes and relationships
- Writes graph projections to Neo4j
- Handles idempotent upserts and deletes
- Logs projection status to PostgreSQL

Domain services must never import Neo4j drivers. All graph queries must go through a graph query service that reads from Neo4j but never writes.

### Rule 3: Weaviate Is a Read-Only Vector Projection

Weaviate must only be updated by the vector projection worker. The worker:

- Reads new or changed data from PostgreSQL
- Generates or retrieves embeddings
- Writes vector objects to Weaviate
- Handles idempotent upserts and deletes
- Logs projection status to PostgreSQL

Domain services must never import Weaviate clients. All vector search queries must go through a vector query service that reads from Weaviate but never writes.

### Rule 4: Projection Workers Consume Events, Not Database Triggers

Projection updates must be triggered by domain events consumed from Redpanda, not by PostgreSQL database triggers. Rationale:

- Database triggers couple projection logic to schema
- Triggers are hard to observe, monitor, and debug
- Event-driven projection allows replay, filtering, and batching
- Events carry semantic context (what changed, why)
- Events enable exactly-once processing semantics with idempotent handlers

The transactional outbox pattern ensures events are reliably published:

```sql
-- Each bounded context maintains an outbox table
CREATE TABLE story_outbox (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id    UUID NOT NULL,
    aggregate_type  VARCHAR(100) NOT NULL,
    event_type      VARCHAR(100) NOT NULL,  -- e.g., 'StoryCreated', 'StoryVersionCreated'
    payload         JSONB NOT NULL,
    metadata        JSONB,                   -- tenant_id, workspace_id, correlation_id
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at    TIMESTAMPTZ             -- NULL until published to Redpanda
);

-- Outbox publisher (background process or pg_cron):
-- 1. SELECT unpublished events ordered by created_at
-- 2. Publish to Redpanda
-- 3. UPDATE published_at = NOW()
-- 4. Optionally delete archived outbox rows after TTL
```

### Rule 5: Projection Workers Must Be Idempotent

Every projection operation must produce the same result regardless of how many times it is executed. Implementation:

- Use upsert semantics (MERGE or ON CONFLICT) for Neo4j and Weaviate writes
- Include a unique projection ID derived from the source row ID and version
- Track projection state in PostgreSQL: `projected_at`, `projection_version`, `projection_status`
- Ignore duplicate events by checking `projection_version >= event_version`

### Rule 6: AI Workers Write Only to PostgreSQL

AI workers (extraction, normalization, validation, article generation, embedding) must:

- Read input from PostgreSQL (via job assignment tables)
- Call AI providers (Gemini, Claude, OpenAI) through the provider abstraction layer
- Write results to PostgreSQL
- Emit completion events to Redpanda

AI workers must never write to Neo4j or Weaviate directly. The projection layer handles graph and vector synchronization.

# Alternatives Considered

## Alternative 1: Neo4j as Source of Truth

**Description**: Use Neo4j as the primary operational database for all knowledge-related data. Store graph, relational, and vector data in a polyglot configuration with PostgreSQL as a secondary store for non-graph data.

**Advantages**:
- Eliminates graph projection latency — data is immediately available as a graph
- Simplifies graph query architecture — no sync layer needed
- Leverages Neo4j's ACID compliance for graph transactions
- Reduces total database count for knowledge domain

**Disadvantages**:
- **Breaks provenance chain**: Neo4j lacks the mature audit, lineage, and immutable versioning capabilities that PostgreSQL provides. Implementing temporal versioning in Neo4j is significantly more complex.
- **No native support for crucial PostgreSQL features**: JSONB for flexible metadata, partitioning for multi-tenancy, event triggers, logical replication, and pg_cron for scheduling.
- **Higher operational maturity required**: Running Neo4j at scale requires specialized expertise that is harder to staff than PostgreSQL.
- **Vector search still requires Weaviate**: Neo4j's vector capabilities (added in 5.x) are not yet mature enough to replace Weaviate for production semantic search at the target scale.
- **Event sourcing integration is weaker**: PostgreSQL's transactional outbox pattern is a well-understood implementation. Neo4j's CDC (change data capture) is less mature.
- **Vendor lock-in risk**: Graph databases have fewer migration paths than relational databases. Moving away from Neo4j later would be costly.

**Rejection rationale**: Neo4j's graph capabilities are essential for traversal and analytics, but the database is not designed to be the system of record for this platform's requirements. The provenance, versioning, and operational maturity of PostgreSQL make it the correct source of truth.

## Alternative 2: Polyglot with No Clear Source of Truth

**Description**: Allow each domain to choose its own primary database. Stories in PostgreSQL, knowledge graph in Neo4j, embeddings in Weaviate, with no single authoritative store. Cross-domain queries use federated query or application-level joins.

**Advantages**:
- Maximum flexibility for each domain to use the optimal database
- No projection latency — each database is written to directly
- Simpler initial implementation for each domain individually
- Follows the "polyglot persistence" pattern used by some large-scale platforms

**Disadvantages**:
- **Provenance becomes impossible**: A knowledge object that exists in Neo4j must be traceable to a claim in PostgreSQL, which must be traceable to a transcript segment, which must be traceable to a source. Without a single source of truth, this chain cannot be enforced.
- **Split-brain scenarios**: If the story in PostgreSQL is updated but the Neo4j write fails, the graph becomes inconsistent with no clear recovery mechanism.
- **No consistent backup strategy**: Each database requires separate backup tooling and RPO/RTO calculations. Restoring to a consistent point across databases is extremely difficult.
- **Cross-domain queries require distributed transactions**: Coordinating writes across PostgreSQL, Neo4j, and Weaviate in a single operation is impractical without distributed transactions, which are not available across these different systems.
- **Multi-tenancy enforcement is fragmented**: Each database implements tenant isolation differently. A bug in one database's isolation layer could leak data across tenants.
- **Audit and compliance complexity**: Generating a unified audit trail requires correlating logs across three database systems, each with different logging formats and capabilities.
- **Team cognitive load**: Every developer must understand three database technologies deeply. Operational runbooks multiply in complexity.

**Rejection rationale**: For a platform that requires strong provenance, immutable versioning, multi-tenant isolation, and auditable data lineage, a polyglot approach without a clear source of truth creates unacceptable operational and consistency risks. The cost of managing eventual consistency between three databases for every write operation outweighs the benefits of direct writes.

## Alternative 3: PostgreSQL as Both Source of Truth and Graph Store

**Description**: Eliminate Neo4j entirely. Store graph data in PostgreSQL using recursive CTEs, adjacency lists stored in JSONB, or the Apache AGE extension for graph modeling within PostgreSQL.

**Advantages**:
- Single database eliminates all projection complexity
- Strong consistency for graph queries — no eventual consistency window
- Simplified backup, recovery, and operational management
- No synchronization layer to build, maintain, and debug
- Lower infrastructure cost and complexity

**Disadvantages**:
- **Recursive CTEs do not scale to 100,000,000 relationships**: PostgreSQL's recursive query performance degrades significantly at graph scale. Multi-hop traversals (e.g., "find all entities related to Kuntilanak within 5 degrees of separation") that take milliseconds in Neo4j can take seconds or minutes in PostgreSQL.
- **No graph-native query language**: Cypher enables expressive graph pattern matching that is verbose and slow in SQL. Graph analytics (centrality, community detection, path finding) are impractical in PostgreSQL.
- **Lack of graph visualization tooling**: Neo4j's ecosystem (Bloom, Browser, GraphQL integration) provides immediate value for researchers exploring the knowledge graph.
- **PostgreSQL extensions add complexity**: Apache AGE is still maturing and introduces its own operational overhead. Custom graph solutions are fragile and hard to maintain.
- **Missed opportunity for graph-native features**: Neo4j provides native graph storage, indexed adjacency, and optimized traversal algorithms that cannot be replicated in PostgreSQL.

**Rejection rationale**: Graph queries are a primary user-facing feature of the platform. Researchers, editors, and readers will explore the knowledge graph interactively. The performance and expressiveness requirements for graph traversal at the target scale of 100,000,000 relationships justify Neo4j as a dedicated projection. PostgreSQL as the source of truth with Neo4j as a specialized query projection provides the best combination of consistency and performance.

## Alternative 4: PostgreSQL with Read-Through Cache Strategy

**Description**: Use PostgreSQL as the sole database. Implement read-through caching at the application layer (Redis for graph-like queries, application-level materialized views for graph patterns). Graph exploration is handled by application code that transforms relational data into graph structures on read.

**Advantages**:
- Operational simplicity of a single database system
- No eventual consistency concerns — every read reflects the latest committed state
- No projection worker infrastructure to maintain
- Caching can be invalidated precisely when source data changes
- Lower total infrastructure cost compared to three database systems

**Disadvantages**:
- **Graph visualization performance is unacceptable**: Interactive graph exploration requires sub-100ms traversal queries. Materializing graph structures from relational tables on every read introduces latency that kills user experience.
- **Application-layer graph logic is fragile**: Graph algorithms (shortest path, community detection, centrality) must be reimplemented in application code, tested, and maintained. This duplicates Neo4j's built-in capabilities at significant engineering cost.
- **Cache invalidation complexity**: When data changes, the cache must be selectively invalidated for all affected graph paths. This becomes exponentially complex as the graph grows.
- **No graph-native analytics**: Researchers require graph analytics (e.g., "which entities are most connected?", "how does belief X relate to region Y?"). These are impractical to implement at the application layer.
- **Scaling bottleneck**: All graph queries pass through the application layer, which becomes a bottleneck for concurrent graph exploration. Neo4j's native parallel traversal is lost.
- **Immutable versioning adds complexity**: Versioned graph data requires temporal modeling in both PostgreSQL and the cache layer.

**Rejection rationale**: While operationally simpler, this approach sacrifices the entire value proposition of graph-native querying. The platform's product vision — "the largest living knowledge graph of Indonesian mystery culture" — requires graph-native performance and analytics. A dedicated graph projection is not optional; it is core to the product.

# Consequences

## Positive

1. **Single authoritative data source**: All writes go through PostgreSQL, ensuring that every piece of data has one definitive version. Split-brain scenarios are impossible by design.

2. **Provenance integrity**: Every knowledge object, claim, and article is traceable to its source through PostgreSQL's relational model. The provenance chain (Source → Transcript → Segment → Claim → Knowledge Object) is enforced through foreign keys and cannot be bypassed.

3. **Rebuildable projections**: Neo4j and Weaviate can be rebuilt from scratch at any time by replaying domain events. This eliminates data corruption risk in projections and enables disaster recovery without data loss.

4. **Simplified backup and recovery**: Only PostgreSQL requires point-in-time recovery (PITR) for operational continuity. Neo4j and Weaviate can be restored by replaying events, reducing their backup requirements to configuration snapshots.

5. **Clear team ownership boundaries**: Teams own PostgreSQL schemas within their bounded contexts. The projection layer is owned by a platform/infrastructure team. No ambiguity about who is responsible for data correctness.

6. **Human review gate enforced naturally**: AI outputs are written to PostgreSQL in a "review required" state. Only after human approval are projection events emitted. Graph and vector stores never contain unreviewed data, preventing accidental exposure of unverified content.

7. **Independent scaling of reads and writes**: PostgreSQL scales for transactional throughput. Neo4j scales for graph traversal read performance. Weaviate scales for vector search throughput. Each can be scaled independently based on usage patterns.

8. **Event-driven architecture alignment**: The projection pattern aligns with the broader event-driven architecture. Domain events serve double duty — they drive both business workflows (e.g., approval workflows) and infrastructure synchronization (projections).

## Negative

1. **Eventual consistency between stores**: After a write to PostgreSQL, there is a window (typically sub-second to a few seconds, depending on Redpanda latency and projection worker throughput) during which Neo4j and Weaviate are stale. User-facing applications that need graph or vector data immediately must tolerate this delay or be designed to fall back to PostgreSQL.

2. **Projection infrastructure complexity**: Graph and vector projection workers are additional services that must be built, deployed, monitored, and scaled. This increases operational surface area and introduces new failure modes (projection worker crashes, event processing delays, duplicate events).

3. **Increased read latency for graph/vector queries**: Graph and vector data is only available after the projection completes. For time-sensitive operations (e.g., a researcher immediately wants to explore the graph after adding data), the delay can be noticeable.

4. **Duplicate storage cost**: Data exists in PostgreSQL and is duplicated (in different formats) in Neo4j and Weaviate. At the target scale of 100,000,000 graph relationships and 100,000,000 embeddings, storage costs are non-trivial and must be factored into infrastructure budgeting.

5. **Synchronization failure monitoring burden**: Failed projections must be detected, alerted, investigated, and retried. This requires robust monitoring of projection worker health, event processing lag, and data consistency checks across stores.

6. **Migration coordination complexity**: Schema changes in PostgreSQL may require corresponding changes in projection logic. A coordinated rollout is needed: deploy projection worker update → deploy schema change → verify projections. This adds overhead to every database migration.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Consistency** | Strong consistency for writes (PostgreSQL ACID) | Eventual consistency for projections |
| **Recovery** | Full recovery from PostgreSQL snapshots + event replay | Longer RTO for projections (rebuild time) |
| **Performance** | Optimized for each data paradigm (relational, graph, vector) | Write amplification (one write → three stores) |
| **Operational simplicity** | Clear ownership and recovery strategy | Multiple systems to monitor and maintain |
| **Flexibility** | Can add/remove projection targets independently | Must maintain event contracts for each projection |
| **Cost** | Can scale each database independently | Duplicate storage and compute costs |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Projection worker falls behind** | Medium | High — users see stale graph/vector data | Implement lag monitoring with alerting. Auto-scale projection workers based on queue depth. Consider read-through to PostgreSQL for critical paths. |
| **Event loss in Redpanda** | Low | Critical — data never projected | Enable Redpanda retention policies that exceed maximum expected projection time. Implement dead letter queue with manual replay capability. Run periodic reconciliation jobs that compare PostgreSQL to Neo4j/Weaviate counts. |
| **Duplicate events cause data corruption** | Medium | Medium — incorrect graph relationships or duplicate embeddings | All projection handlers must be idempotent. Use upsert semantics. Include version tracking to ignore stale events. |
| **Schema drift between PostgreSQL and projections** | Medium | High — projections fail silently or produce incorrect data | Implement schema validation in projection workers. Run integration tests that verify projection output matches expected format. Maintain a projection schema registry. |
| **Projection rebuild takes too long** | Medium | High — extended downtime for graph/vector stores | Test rebuild times at target scale during performance testing. Implement parallel rebuild strategies (partition by tenant, by entity type). Use bulk import APIs (Neo4j admin import, Weaviate batch). Target: full rebuild < 4 hours at 100M relationships. |
| **Neo4j or Weaviate become unavailable** | Low | Medium — graph/vector queries fail but writes continue | Implement circuit breakers in query services. Display degraded-UI messages to users. Auto-rebuild from events when store recovers. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Developers accidentally write to Neo4j/Weaviate** | Medium | High — data inconsistency, broken provenance | Enforce at code review level: no Neo4j/Weaviate drivers imported in domain service code. Consider network-level isolation (Neo4j/Weaviate only accessible from projection worker subnets). Add pre-commit hooks that scan for unauthorized database imports. |
| **Projection worker deployment breaks existing projections** | Medium | Medium — graph/vector data temporarily inconsistent | Use blue/green deployment for projection workers. Run canary projections before full rollout. Maintain rollback capability. |
| **Insufficient monitoring of projection health** | High | High — silent data inconsistency | Implement projection health dashboards: events processed, events lagging, error rate, projection freshness (last projected timestamp). Alert on lag > 5 minutes or error rate > 0.1%. |
| **Backup strategy confusing due to multiple stores** | Medium | Medium — incorrect recovery procedures | Document clear recovery runbooks. Automate recovery drills. Only PostgreSQL requires PITR; Neo4j/Weaviate recovery = build projection from scratch. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **New database technology required (e.g., time-series, geospatial)** | Projection architecture scales to additional targets. Adding a new projection type follows the established pattern. | Ensure projection worker framework is generic and extensible. The event catalog should be designed to accommodate new consumers. |
| **Target scale exceeds projection rebuild time SLA** | Full rebuild may take > 4 hours. | Implement incremental rebuild strategies. Consider sharding projections by tenant or data type. Explore continuous reconciliation instead of full rebuilds. |
| **Microservices migration requires distributed projections** | New services may own their projection logic. | Keep projection logic in a shared projection service until clear boundaries emerge. Avoid coupling projection logic to domain services prematurely. |
| **Real-time collaboration requirements emerge** | Eventual consistency may conflict with collaborative editing. | PostgreSQL remains strongly consistent. Real-time collaboration can use PostgreSQL directly for operational data. Graph/vector projections remain eventually consistent — acceptable for exploration use cases. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Neo4j or Weaviate gain mature write-serialization capabilities** that approach PostgreSQL's transactional guarantees, making direct writes with two-phase commit feasible.

2. **PostgreSQL adds native graph storage capabilities** that match Neo4j's traversal performance at scale, potentially eliminating the need for a separate graph projection.

3. **Event sourcing becomes the primary data model**, where PostgreSQL serves purely as an event store and all current state is derived from event streams. In this model, projections become the primary read model, and the source-of-truth distinction shifts to the event store.

4. **A new query paradigm emerges** (e.g., knowledge graph embedding, graph neural networks) that requires different storage characteristics not supported by the current projection targets.

5. **The platform reaches a scale where projection rebuild time exceeds 4 hours**, requiring architectural changes such as continuous reconciliation, incremental rebuilds, or region-based sharding.

Each revision should be recorded as a separate ADR that references this document.

# References

- **Backend Platform PRD §3.4** — "PostgreSQL as Source of Truth" — Product-level justification for the decision.
- **Backend Platform PRD §11** — "Database Strategy" — Stores assigned to each database engine.
- **AI Platform PRD §3.2** — "Event Driven Processing" — AI workers triggered by events, not REST.
- **AI Platform PRD §6.7** — "Embedding Service" — Embeddings written to PostgreSQL, projection events emitted.
- **AI Platform PRD §13** — "Queue Architecture" — Redpanda topics for projection events.
- **ADR-004: Event-Driven Architecture** — Transactional outbox pattern and event catalog.
- **ADR-010: Knowledge Graph Strategy** — Neo4j projection schema and update strategy.
- **ADR-011: Vector Search Strategy** — Weaviate projection schema and embedding strategy.
- **Transactional Outbox Pattern** — https://microservices.io/patterns/data/transactional-outbox.html
- **Neo4j Idempotent Writes** — MERGE clause for idempotent upserts.
- **Weaviate Batch Import** — Batch API for efficient vector writes.