# ADR-011: Knowledge Graph Projection — Neo4j Derived from PostgreSQL

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture is built around a knowledge graph of folklore entities, stories, claims, beliefs, rituals, locations, and their relationships. Readers, researchers, and editors explore this graph interactively — finding all entities related to Kuntilanak within 3 degrees of separation, discovering how beliefs about a spirit vary across regions, tracing the provenance of a claim from a story to its source transcript.

The knowledge graph is the platform's primary user-facing data product. It must support:

- **Interactive graph traversal**: Sub-second multi-hop queries (e.g., "find all stories that mention Kuntilanak and are located in Java")
- **Graph analytics**: Centrality, community detection, path finding (e.g., "which entity has the most connections in Balinese folklore?")
- **Temporal queries**: "Show the state of the graph as of June 2025" (using immutable versioning)
- **Tenant isolation**: Users see only their tenant's data plus global knowledge

At the target scale of 100,000,000 graph relationships, these queries require a graph-native database.

## Technical Context

The platform stack includes PostgreSQL 18 (source of truth, per ADR-001), Neo4j 5.26 (graph projection, read-only), and Redpanda (event backbone, per ADR-003). The architecture principle (PRD §3.4) states: "PostgreSQL is source of truth. Neo4j is a Knowledge Graph Projection. Applications must never write directly to Neo4j."

The existing `docs/architecture/knowledge-graph-modeling.md` defines a detailed Neo4j data model covering:

- Node types: Story, Entity (spirit/deity/creature/person/location), Theme, Motif, Claim, Belief, Ritual, Tradition, Location, Source, Transcript, Region, Culture
- Relationship types: MENTIONS, FEATURES, HAS_THEME, HAS_MOTIF, HAS_CLAIM, ASSOCIATED_WITH, APPEARS_IN, DERIVED_FROM, CONTRADICTS, INFLUENCED_BY, LOCATED_IN, RELATED_TO, SAME_AS, VARIANT_OF
- Property model: Each node carries `id`, `name`, `tenant_id`, `version`, `created_at`, `updated_at`, plus type-specific properties

The AI Platform produces Canonical Stories (per ADR-007) with extracted entities, claims, themes, motifs, beliefs, and rituals. These are persisted to PostgreSQL (per ADR-004). The graph projection worker reads from PostgreSQL and writes to Neo4j.

## Constraints

1. **No direct writes to Neo4j**: Domain services must never import Neo4j drivers. All graph writes go through the projection worker.

2. **Read-only Neo4j for query services**: Graph query services read from Neo4j but never write. Neo4j is not a transaction participant.

3. **Rebuildable from PostgreSQL**: The entire Neo4j graph must be rebuildable from PostgreSQL at any time. This is the ultimate recovery mechanism.

4. **Immutable versioning**: When a story or knowledge object is updated, the new version is a new row in PostgreSQL. The graph must reflect the current (latest) version. Historical versions are not projected.

5. **Human review gate**: Only APPROVED or PUBLISHED content (per state machines in PRD §9) is projected to Neo4j. REVIEW_REQUIRED content must never appear in the graph.

6. **Tenant isolation in graph**: Neo4j nodes include `tenant_id` property. Queries filter by tenant. Global knowledge (tenant_id = NULL) is visible to all tenants. Weaviate's native multi-tenancy is used for vector data.

7. **Eventual consistency**: There is a delay (sub-second to seconds) between a PostgreSQL write and the Neo4j projection update. This is acceptable for the platform's use cases.

8. **Scalability target**: 100,000 stories, 1,000,000 knowledge objects, 100,000,000 graph relationships.

## Problem Statement

Neo4j is a read-only projection of data that originates in PostgreSQL. The graph must be kept in sync with PostgreSQL, support full rebuilds, handle schema evolution (new node types, new relationship types), maintain tenant isolation, respect the human review gate, and scale to 100,000,000 relationships. How do we design a graph projection system that reliably syncs data from PostgreSQL to Neo4j, supports event-driven incremental updates and batch rebuilds, handles relationship evolution without data loss, and provides observable, debuggable projection state?

# Decision

**Neo4j is a read-only projection of data derived from PostgreSQL. The graph projection worker consumes domain events from Redpanda and transforms relational data into Neo4j nodes and relationships. The graph is fully rebuildable from PostgreSQL. Projection state is tracked in PostgreSQL for observability and recovery. Applications must never write directly to Neo4j.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 18 (Source of Truth)                       │
│                                                                          │
│  content_stories      │  knowledge_objects     │  knowledge_claims      │
│  content_story_vers.  │  knowledge_folklore    │  knowledge_beliefs     │
│  content_articles     │  knowledge_themes      │  knowledge_rituals     │
│                       │  knowledge_motifs      │  knowledge_traditions  │
│                       │  knowledge_locations   │  knowledge_contradict. │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Transactional Outbox → Redpanda                                  │   │
│  │  Events: GraphProjectionRequested, StoryCreated,                  │   │
│  │  KnowledgeExtracted, KnowledgeValidated, EntityNormalized,        │   │
│  │  StoryPublished, ReviewApproved, ContradictionDetected            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Redpanda (Event Backbone)                             │
│                                                                          │
│  Topics consumed by graph-projection-worker:                            │
│  - graph.projection.requested   (trigger full/partial rebuild)          │
│  - content.evt: StoryPublished, StoryVersionCreated                     │
│  - knowledge.evt: KnowledgeExtracted, KnowledgeValidated,                │
│    EntityNormalized, ContradictionDetected, BeliefRegistered            │
│  - workflow.evt: ReviewApproved (gate: only approved content)           │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Graph Projection Worker (Python)                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Event Handler                                                    │   │
│  │  ─────────────                                                    │   │
│  │  Consumes events from Redpanda                                   │   │
│  │  Determines action type: insert, update, delete, rebuild         │   │
│  │  Fetches source data from PostgreSQL                              │   │
│  │  Applies transformation logic (relational → graph)               │   │
│  │  Upserts into Neo4j                                              │   │
│  │  Updates projection state in PostgreSQL                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Graph Schema Registry                                            │   │
│  │  ─────────────────────                                            │   │
│  │  Defines: node types, relationship types, property mappings       │   │
│  │  Versioned: graph schema evolves independently of PostgreSQL      │   │
│  │  Migration: handles new node/relationship types gracefully        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Rebuild Coordinator                                             │   │
│  │  ───────────────────                                             │   │
│  │  Triggers: manual (operator), scheduled (nightly),               │   │
│  │  recovery (detected corruption)                                  │   │
│  │  Strategy: batch delete + re-insert from PostgreSQL              │   │
│  │  Batch size: 1,000 entities per transaction                      │   │
│  │  Parallelism: partition by tenant or entity type                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Neo4j 5.26 (Read-Only Graph Projection)               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Node Types                      │  Label Properties              │   │
│  │  ──────────                      │  ─────────────────             │   │
│  │  :Story                          │  id, title, summary,           │   │
│  │                                  │  narrative_type, language,     │   │
│  │                                  │  tenant_id, version,           │   │
│  │                                  │  created_at, updated_at        │   │
│  │                                  │                                │   │
│  │  :Entity                         │  id, name, normalized_name,   │   │
│  │                                  │  entity_type, subtype,        │   │
│  │                                  │  description, tenant_id,       │   │
│  │                                  │  confidence, created_at        │   │
│  │                                  │                                │   │
│  │  :Theme                          │  id, name, category,          │   │
│  │  :Motif                          │  confidence                    │   │
│  │  :Claim                          │                                │   │
│  │  :Belief                         │  id, statement,                │   │
│  │  :Ritual                         │  adherent_community,           │   │
│  │  :Tradition                      │  confidence, tenant_id         │   │
│  │                                  │                                │   │
│  │  :Location                       │  id, name, location_type,     │   │
│  │                                  │  latitude, longitude           │   │
│  │                                  │                                │   │
│  │  :Region                         │  id, name, ethnic_group       │   │
│  │  :Culture                        │                                │   │
│  │  :Source                         │  id, title, source_type,      │   │
│  │  :Transcript                     │  language                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Relationship Types             │  Properties                     │   │
│  │  ──────────────────             │  ──────────                     │   │
│  │  (:Story)-[:MENTIONS]->(:Entity)  │  confidence, evidence_segment, │   │
│  │  (:Story)-[:HAS_THEME]->(:Theme) │  source_id                     │   │
│  │  (:Story)-[:HAS_MOTIF]->(:Motif) │                                │   │
│  │  (:Story)-[:HAS_CLAIM]->(:Claim) │                                │   │
│  │  (:Story)-[:LOCATED_IN]->(:Loc.) │                                │   │
│  │  (:Story)-[:DERIVED_FROM]->(:Tr.)│                                │   │
│  │  (:Entity)-[:APPEARS_IN]->(:Loc.)│                                │   │
│  │  (:Entity)-[:ASSOCIATED_WITH]->(.)│                                │   │
│  │  (:Entity)-[:RELATED_TO]->(:Ent.)│                                │   │
│  │  (:Entity)-[:SAME_AS]->(:Entity) │                                │   │
│  │  (:Entity)-[:VARIANT_OF]->(:Ent.)│                                │   │
│  │  (:Entity)-[:CONTRADICTS]->(:Ent)│                                │   │
│  │  (:Belief)-[:HELD_BY]->(:Cult.)  │                                │   │
│  │  (:Ritual)-[:PRACTICED_IN]->(Reg)│                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Event-Driven Incremental Updates

The graph projection worker consumes domain events from Redpanda and applies incremental updates. Each event type maps to a specific graph operation.

```python
class GraphProjectionWorker:
    """Consumes domain events and updates Neo4j projection."""
    
    EVENT_HANDLERS = {
        "StoryPublished": handle_story_published,
        "StoryVersionCreated": handle_story_version_created,
        "KnowledgeExtracted": handle_knowledge_extracted,
        "KnowledgeValidated": handle_knowledge_validated,
        "EntityNormalized": handle_entity_normalized,
        "ContradictionDetected": handle_contradiction_detected,
        "BeliefRegistered": handle_belief_registered,
        "ReviewApproved": handle_review_approved,
        "GraphProjectionRequested": handle_rebuild_request,
    }
    
    async def handle_event(self, event):
        handler = self.EVENT_HANDLERS.get(event.event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event.event_type}")
            return
        
        try:
            await handler(event)
            self._update_projection_state(event)
        except Exception as e:
            logger.error(f"Projection failed for event {event.event_id}: {e}")
            self._publish_to_dlq(event, str(e))
    
    async def handle_story_published(self, event):
        """Project a published story and its entities into Neo4j."""
        story = await self._fetch_story(event.data['storyId'])
        
        async with self.neo4j_session() as session:
            await session.run("""
                MERGE (s:Story {id: $story_id})
                SET s.title = $title,
                    s.summary = $summary,
                    s.narrative_type = $narrative_type,
                    s.language = $language,
                    s.tenant_id = $tenant_id,
                    s.status = 'PUBLISHED',
                    s.version = $version,
                    s.updated_at = timestamp()
                
                WITH s
                UNWIND $entities AS entity
                MERGE (e:Entity {id: entity.id})
                SET e.name = entity.name,
                    e.normalized_name = entity.normalized_name,
                    e.entity_type = entity.entity_type,
                    e.subtype = entity.subtype,
                    e.tenant_id = entity.tenant_id,
                    e.confidence = entity.confidence
                MERGE (s)-[r:MENTIONS]->(e)
                SET r.confidence = entity.confidence,
                    r.evidence_segment = entity.evidence_segment,
                    r.updated_at = timestamp()
            """, story_id=story['id'],
                 title=story['title'],
                 summary=story['summary'],
                 narrative_type=story['narrative_type'],
                 language=story['language'],
                 tenant_id=str(story['tenant_id']),
                 version=story['version'],
                 entities=self._extract_entities(story))
    
    async def handle_knowledge_extracted(self, event):
        """Project extracted knowledge objects (themes, motifs, beliefs, rituals)."""
        knowledge = await self._fetch_knowledge(event.data['knowledgeId'])
        
        async with self.neo4j_session() as session:
            # Themes
            for theme in knowledge['themes']:
                await session.run("""
                    MERGE (t:Theme {id: $id})
                    SET t.name = $name,
                        t.category = $category,
                        t.confidence = $confidence,
                        t.tenant_id = $tenant_id
                    WITH t
                    MATCH (s:Story {id: $story_id})
                    MERGE (s)-[r:HAS_THEME]->(t)
                    SET r.confidence = $confidence
                """, id=theme['id'], name=theme['name'],
                     category=theme.get('category'),
                     confidence=theme['confidence'],
                     tenant_id=str(event.metadata['tenantId']),
                     story_id=event.data['storyId'])
            
            # Beliefs
            for belief in knowledge['beliefs']:
                await session.run("""
                    MERGE (b:Belief {id: $id})
                    SET b.statement = $statement,
                        b.adherent_community = $community,
                        b.confidence = $confidence,
                        b.tenant_id = $tenant_id
                    WITH b
                    MATCH (s:Story {id: $story_id})
                    MERGE (s)-[r:HAS_BELIEF]->(b)
                    SET r.confidence = $confidence
                """, id=belief['id'], statement=belief['statement'],
                     community=belief.get('adherentCommunity'),
                     confidence=belief['confidence'],
                     tenant_id=str(event.metadata['tenantId']),
                     story_id=event.data['storyId'])
```

### Rule 2: Idempotent Upserts with MERGE

All Neo4j writes use MERGE (not CREATE) to ensure idempotency. If the same event is processed twice (due to at-least-once delivery from Redpanda), the MERGE operation ensures the graph state is identical.

```cypher
// Idempotent node creation
MERGE (e:Entity {id: $entity_id})
SET e.name = $name,
    e.entity_type = $entity_type,
    e.tenant_id = $tenant_id,
    e.updated_at = timestamp()

// Idempotent relationship creation
MATCH (s:Story {id: $story_id})
MATCH (e:Entity {id: $entity_id})
MERGE (s)-[r:MENTIONS]->(e)
SET r.confidence = $confidence,
    r.evidence_segment = $evidence,
    r.updated_at = timestamp()
```

### Rule 3: Projection State Tracking

The projection worker maintains a state table in PostgreSQL that tracks which version of each entity has been projected to Neo4j. This enables observability, recovery, and rebuild verification.

```sql
CREATE TABLE projection_state (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source entity identification
    source_type         VARCHAR(50) NOT NULL,   -- 'story', 'entity', 'theme', 'belief', etc.
    source_id           UUID NOT NULL,           -- ID in PostgreSQL
    
    -- Projection tracking
    projected_version   BIGINT NOT NULL,         -- Version of source data that was projected
    projected_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Event that triggered this projection
    last_event_id       UUID NOT NULL,
    last_event_type     VARCHAR(100) NOT NULL,
    
    -- Status
    status              VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    -- 'PENDING' → 'PROJECTED' → 'FAILED'
    
    error_message       TEXT,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    
    -- Uniqueness
    UNIQUE(source_type, source_id),
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for finding entities that need projection
CREATE INDEX idx_projection_pending 
    ON projection_state(source_type, source_id) 
    WHERE status = 'PENDING';

-- Index for rebuild queries
CREATE INDEX idx_projection_source 
    ON projection_state(source_type, source_id);
```

**Projection state query**:
```sql
-- Find entities that are behind (source version > projected version)
SELECT ps.source_type, ps.source_id, ps.projected_version, 
       v.version_number AS current_version
FROM projection_state ps
JOIN content_story_versions v ON v.story_id = ps.source_id
WHERE ps.source_type = 'story'
  AND ps.projected_version < v.version_number;

-- Projection lag (time since last projection)
SELECT source_type, 
       COUNT(*) AS total,
       AVG(EXTRACT(EPOCH FROM (NOW() - projected_at))) AS avg_lag_seconds
FROM projection_state
WHERE status = 'PROJECTED'
GROUP BY source_type;
```

### Rule 4: Rebuild Strategy

The graph can be fully rebuilt from PostgreSQL at any time. The rebuild process:

1. Truncates all Neo4j data (or drops and recreates constraints/indexes)
2. Reads all APPROVED/PUBLISHED data from PostgreSQL in batches
3. Transforms and inserts into Neo4j
4. Resets projection_state to reflect the rebuild

```python
async def rebuild_graph(tenant_id: Optional[str] = None):
    """Full rebuild of Neo4j from PostgreSQL.
    
    Args:
        tenant_id: If provided, rebuild only for this tenant.
                   If None, rebuild entire graph.
    """
    logger.info(f"Starting graph rebuild for tenant: {tenant_id or 'ALL'}")
    start_time = time.monotonic()
    
    # Step 1: Clear existing data
    async with neo4j_session() as session:
        if tenant_id:
            # Tenant-scoped delete (for partial rebuild)
            await session.run(
                "MATCH (n {tenant_id: $tenant_id}) DETACH DELETE n",
                tenant_id=tenant_id
            )
        else:
            # Full delete
            await session.run("MATCH (n) DETACH DELETE n")
    
    # Step 2: Rebuild in order (sources → stories → entities → relationships)
    stats = {
        'stories': 0, 'entities': 0, 'themes': 0, 'motifs': 0,
        'beliefs': 0, 'rituals': 0, 'traditions': 0, 'locations': 0,
        'relationships': 0
    }
    
    # Batch 1: Stories (with tenant filter if specified)
    async for batch in fetch_batched(
        "SELECT s.id, sv.title, sv.summary, sv.narrative_type, "
        "sv.language, s.tenant_id, sv.version_number "
        "FROM content_stories s "
        "JOIN content_story_versions sv ON s.current_version_id = sv.id "
        "WHERE s.status = 'PUBLISHED' "
        + ("AND s.tenant_id = $1" if tenant_id else ""),
        batch_size=1000, tenant_id=tenant_id
    ):
        async with neo4j_session() as session:
            for row in batch:
                await session.run("""
                    MERGE (s:Story {id: $id})
                    SET s.title = $title,
                        s.summary = $summary,
                        s.narrative_type = $narrative_type,
                        s.language = $language,
                        s.tenant_id = $tenant_id,
                        s.version = $version,
                        s.status = 'PUBLISHED',
                        s.created_at = timestamp()
                """, id=str(row['id']), title=row['title'],
                     summary=row['summary'],
                     narrative_type=row['narrative_type'],
                     language=row['language'],
                     tenant_id=str(row['tenant_id']),
                     version=row['version_number'])
                stats['stories'] += 1
    
    # Batch 2: Entities from knowledge_objects
    async for batch in fetch_batched(
        "SELECT ko.id, ko.canonical_name, ko.object_type, "
        "ko.summary, ko.confidence_score, ko.tenant_id, "
        "ko.metadata->>'subtype' AS subtype "
        "FROM knowledge_objects ko "
        "WHERE ko.status = 'PUBLISHED'"
        + (" AND ko.tenant_id = $1" if tenant_id else ""),
        batch_size=1000, tenant_id=tenant_id
    ):
        async with neo4j_session() as session:
            for row in batch:
                await session.run("""
                    MERGE (e:Entity {id: $id})
                    SET e.name = $name,
                        e.normalized_name = $name,
                        e.entity_type = $type,
                        e.subtype = $subtype,
                        e.summary = $summary,
                        e.confidence = $confidence,
                        e.tenant_id = $tenant_id
                """, id=str(row['id']), name=row['canonical_name'],
                     type=row['object_type'],
                     subtype=row.get('subtype'),
                     summary=row['summary'],
                     confidence=row['confidence_score'],
                     tenant_id=str(row['tenant_id']))
                stats['entities'] += 1
    
    # ... (similar batches for themes, motifs, beliefs, rituals, locations)
    
    # Step 3: Create relationships
    async for batch in fetch_batched(
        "SELECT cr.story_id, cr.entity_id, cr.relationship_type, "
        "cr.confidence, cr.evidence "
        "FROM content_story_entities cr "
        "JOIN content_stories s ON cr.story_id = s.id "
        "WHERE s.status = 'PUBLISHED'"
        + (" AND s.tenant_id = $1" if tenant_id else ""),
        batch_size=1000, tenant_id=tenant_id
    ):
        async with neo4j_session() as session:
            for row in batch:
                await session.run("""
                    MATCH (s:Story {id: $story_id})
                    MATCH (e:Entity {id: $entity_id})
                    MERGE (s)-[r:MENTIONS]->(e)
                    SET r.confidence = $confidence,
                        r.evidence = $evidence
                """, story_id=str(row['story_id']),
                     entity_id=str(row['entity_id']),
                     confidence=row['confidence'],
                     evidence=row['evidence'])
                stats['relationships'] += 1
    
    # Step 4: Reset projection state
    await db.execute("DELETE FROM projection_state")
    await db.execute("""
        INSERT INTO projection_state 
            (source_type, source_id, projected_version, status, projected_at)
        SELECT 'story', id, version, 'PROJECTED', NOW()
        FROM content_stories WHERE status = 'PUBLISHED'
    """)
    
    duration = time.monotonic() - start_time
    logger.info(f"Rebuild complete: {stats} in {duration:.1f}s")
    return stats
```

**Rebuild time estimates** (at target scale):

| Scale | Stories | Entities | Relationships | Estimated Time |
|-------|---------|----------|---------------|----------------|
| Small (Phase 1) | 1,000 | 10,000 | 100,000 | ~2 minutes |
| Medium (Phase 2) | 10,000 | 100,000 | 10,000,000 | ~20 minutes |
| Target (Phase 3) | 100,000 | 1,000,000 | 100,000,000 | ~3 hours |

### Rule 5: Relationship Evolution

Relationships in the graph evolve as new knowledge is extracted and existing knowledge is refined. The projection worker handles three types of relationship changes:

**New relationships**: When a story is published with newly extracted entities, new `MENTIONS` relationships are created. When contradictions are detected, new `CONTRADICTS` relationships are created between entities.

**Updated relationships**: When entity normalization resolves an alias (e.g., "Pontianak" → "Kuntilanak"), the `SAME_AS` relationship is created. When confidence scores change, relationship properties are updated.

**Deleted relationships**: When content is archived, relationships are removed. The projection worker consumes the archive event and DETACH DELETEs the affected nodes.

```python
async def handle_entity_normalized(self, event):
    """Handle entity alias resolution — create SAME_AS relationships."""
    alias = event.data['aliasEntityId']
    canonical = event.data['canonicalEntityId']
    confidence = event.data.get('confidence', 90)
    
    async with self.neo4j_session() as session:
        await session.run("""
            MATCH (alias:Entity {id: $alias_id})
            MATCH (canonical:Entity {id: $canonical_id})
            MERGE (alias)-[r:SAME_AS]->(canonical)
            SET r.confidence = $confidence,
                r.resolved_at = timestamp(),
                r.normalization_job_id = $job_id
        """, alias_id=alias, canonical_id=canonical,
             confidence=confidence, job_id=event.data['normalizationJobId'])

async def handle_content_archived(self, event):
    """Handle content archival — remove from graph."""
    entity_type = event.data['entityType']  # 'story', 'entity', 'article'
    entity_id = event.data['entityId']
    
    async with self.neo4j_session() as session:
        # Remove the node and all its relationships
        await session.run(
            "MATCH (n {id: $id}) DETACH DELETE n",
            id=entity_id
        )
    
    # Update projection state
    await db.execute("""
        UPDATE projection_state 
        SET status = 'ARCHIVED', updated_at = NOW()
        WHERE source_type = $1 AND source_id = $2
    """, entity_type, entity_id)
```

### Rule 6: Human Review Gate Enforcement

The projection worker must only project APPROVED or PUBLISHED content. REVIEW_REQUIRED content is never projected.

```python
async def handle_review_approved(self, event):
    """When review is approved, project the content to Neo4j."""
    entity_type = event.data['entityType']  # 'canonical_story', 'knowledge'
    entity_id = event.data['entityId']
    
    # Verify the entity is in APPROVED or PUBLISHED state
    entity = await self._fetch_entity(entity_type, entity_id)
    if entity['status'] not in ('APPROVED', 'PUBLISHED'):
        logger.warning(
            f"Review approved but entity {entity_id} has status {entity['status']}. "
            f"Skipping projection."
        )
        return
    
    # Project to Neo4j
    await self._project_entity(entity_type, entity)
```

**Enforcement at the event level**: The projection worker only subscribes to events that indicate approved/published content:
- `StoryPublished` (not `StoryCreated`)
- `ReviewApproved` (not `ReviewRequested`)
- `KnowledgeValidated` (not `KnowledgeExtracted`)

Events for unapproved content (`StoryCreated`, `ReviewRequested`, `KnowledgeExtracted`) are not consumed by the projection worker. They are consumed by workflow and orchestration services.

### Rule 7: Tenant Isolation in Graph

Every Neo4j node carries a `tenant_id` property. Graph queries filter by tenant. Global knowledge (tenant_id = NULL) is visible to all tenants.

```cypher
// Tenant-scoped query: find all stories visible to tenant T1
MATCH (s:Story)
WHERE s.tenant_id = 'T1' OR s.tenant_id IS NULL
RETURN s

// Find entities related to Kuntilanak within 3 hops (tenant-scoped)
MATCH (e:Entity {name: 'Kuntilanak', tenant_id: $tenant_id})
CALL apoc.path.subgraphAll(e, {
    maxLevel: 3,
    whitelistNodes: ['Entity', 'Story', 'Location'],
    labelFilter: '+Entity|+Story|+Location'
})
YIELD nodes, relationships
RETURN nodes, relationships

// Cross-tenant global knowledge (visible to all)
MATCH (e:Entity)
WHERE e.tenant_id IS NULL  -- Global folklore entities
  AND e.name = 'Kuntilanak'
RETURN e
```

**Weaviate multi-tenancy note**: Weaviate has native multi-tenancy built into its API. Vector data for different tenants is automatically isolated. Neo4j does not have native multi-tenancy — it is handled through application-level filtering on `tenant_id`.

```python
# Graph query service — always includes tenant filter
class GraphQueryService:
    async def find_related_entities(self, entity_id: str, tenant_id: str, max_hops: int = 3):
        async with self.neo4j_session() as session:
            result = await session.run("""
                MATCH (e:Entity {id: $entity_id})
                WHERE e.tenant_id = $tenant_id OR e.tenant_id IS NULL
                CALL apoc.path.subgraphAll(e, {
                    maxLevel: $max_hops,
                    whitelistNodes: ['Entity', 'Story', 'Theme', 'Belief', 'Location']
                })
                YIELD nodes, relationships
                RETURN nodes, relationships
            """, entity_id=entity_id, tenant_id=tenant_id, max_hops=max_hops)
            
            record = await result.single()
            return {
                'nodes': [self._node_to_dict(n) for n in record['nodes']]
                    if record else [],
                'relationships': [self._rel_to_dict(r) for r in record['relationships']]
                    if record else []
            }
```

### Rule 8: Projection Lag Monitoring

Projection lag — the time between a PostgreSQL write and its appearance in Neo4j — must be observable.

```python
# Prometheus metrics
projection_lag_seconds = Gauge(
    'graph_projection_lag_seconds',
    'Time since last projection update',
    ['source_type']
)

projection_events_processed = Counter(
    'graph_projection_events_processed_total',
    'Total events processed by graph projection worker',
    ['event_type', 'status']
)

projection_rebuild_duration = Histogram(
    'graph_projection_rebuild_duration_seconds',
    'Duration of graph rebuild operations',
    ['scope']  # 'full', 'tenant'
)

# Alerting rules (Prometheus)
# - graph_projection_lag_seconds > 300  → Warning (5 min lag)
# - graph_projection_lag_seconds > 1800 → Critical (30 min lag)
# - graph_projection_events_processed_total{status="failed"} > 10 in 5m → Warning
```

**Dashboard metrics** (Grafana):

| Panel | Query | Alert |
|-------|-------|-------|
| Projection Lag (seconds) | `avg(graph_projection_lag_seconds) by (source_type)` | > 300s → Warning, > 1800s → Critical |
| Events Processed | `rate(graph_projection_events_processed_total[5m])` | — |
| Event Failure Rate | `rate(graph_projection_events_processed_total{status="failed"}[5m])` | > 0.01 → Warning |
| Rebuild Duration | `graph_projection_rebuild_duration_seconds` | > 4 hours → Warning |
| Neo4j Node Count | Neo4j `MATCH (n) RETURN count(n)` | — |
| Neo4j Relationship Count | Neo4j `MATCH ()-->() RETURN count(*))` | — |
| Pending Projections | `SELECT count(*) FROM projection_state WHERE status = 'PENDING'` | > 1000 → Warning |

### Rule 9: Graph Schema Versioning

The graph model (node types, relationship types, property names) evolves over time. The graph projection worker maintains a schema version and handles migrations.

```sql
CREATE TABLE graph_schema_versions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version             VARCHAR(50) NOT NULL UNIQUE,  -- '1.0.0', '1.1.0', '2.0.0'
    description         TEXT NOT NULL,
    
    -- Schema definition (JSONB — source of truth for graph model)
    schema_definition   JSONB NOT NULL,
    -- {
    --   "nodeTypes": ["Story", "Entity", "Theme", ...],
    --   "relationshipTypes": ["MENTIONS", "HAS_THEME", ...],
    --   "indexes": ["Entity(name)", "Story(tenant_id)"],
    --   "constraints": ["Entity(id)", "Story(id)"]
    -- }
    
    -- Migration script (Cypher)
    migration_cypher    TEXT,  -- null for initial schema
    
    -- Status
    is_active           BOOLEAN NOT NULL DEFAULT false,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    applied_at          TIMESTAMPTZ
);
```

**Schema migration example** (adding a new `Contradiction` node type):
```cypher
// Migration from v1.0.0 to v1.1.0
// Adding Contradiction node type

CREATE CONSTRAINT contradiction_id IF NOT EXISTS
FOR (c:Contradiction) REQUIRE c.id IS UNIQUE;

CREATE INDEX contradiction_type IF NOT EXISTS
FOR (c:Contradiction) ON (c.type);
```

### Rule 10: Recovery from Projection Failures

When the projection worker fails to process an event (e.g., Neo4j is unavailable, data inconsistency), it implements retry logic and dead letter handling.

```python
async def process_with_retry(self, event, max_retries=3):
    """Process an event with retry logic."""
    for attempt in range(max_retries):
        try:
            await self.handle_event(event)
            return
        except Neo4jConnectionError as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Neo4j unavailable (attempt {attempt + 1}), retrying in {wait}s")
                await asyncio.sleep(wait)
            else:
                raise
        except DataIntegrityError as e:
            # Data issue — won't be fixed by retry, go to DLQ
            await self._publish_to_dlq(event, str(e))
            return
```

# Alternatives Considered

## Alternative 1: Graph-Queries-in-PostgreSQL (No Neo4j)

**Description**: Use PostgreSQL for all graph queries. Recursive CTEs, adjacency lists stored in JSONB, and the Apache AGE extension provide graph capabilities within PostgreSQL. No Neo4j is deployed.

**Advantages**:
- Zero additional infrastructure — PostgreSQL is already in the stack
- Strong consistency — no projection lag, no sync mechanism
- Simplified backup and recovery — one database to manage
- Lower operational cost — no Neo4j cluster to maintain
- ACID transactions across relational and graph data

**Disadvantages**:
- **Recursive CTEs do not scale to 100M relationships**: PostgreSQL's recursive query performance degrades significantly at graph scale. A 3-hop traversal of 100M relationships that takes 10ms in Neo4j can take 10–60 seconds in PostgreSQL.
- **No graph-native query language**: Cypher enables expressive pattern matching that is verbose and slow in SQL. Graph analytics (centrality, community detection, path finding) are impractical in PostgreSQL.
- **Apache AGE is immature**: The AGE extension is still in early stages. It introduces its own operational complexity and may not be production-ready for the platform's scale.
- **No graph visualization tooling**: Neo4j's ecosystem (Bloom, Browser, GraphQL integration) provides immediate value for researchers exploring the knowledge graph.
- **No indexed adjacency**: Neo4j's native graph storage stores adjacency lists as direct pointers, enabling O(1) traversal to neighbors. PostgreSQL must use index lookups for each hop, which is O(log n) per hop.
- **Team expertise**: The team would need to build and maintain graph algorithms that Neo4j provides natively.

**Rejection rationale**: For the platform's core value proposition — interactive graph exploration at 100M relationships — PostgreSQL's recursive CTEs are not performant enough. Neo4j's native graph storage and query optimization provide a 100–1000x performance improvement for multi-hop traversals. The additional infrastructure cost is justified by the graph query performance requirements.

## Alternative 2: Neo4j as Source of Truth (Reverse the Projection)

**Description**: Make Neo4j the primary database for knowledge graph data. PostgreSQL stores operational data (users, workspaces, workflows, audit logs) while Neo4j is the authoritative store for all knowledge-related data (stories, entities, claims, relationships). The AI Platform writes directly to Neo4j.

**Advantages**:
- No projection lag — data is immediately available as a graph
- Simpler architecture — no sync layer, no projection worker
- AI Platform writes directly to the graph database
- Eliminates duplicate storage (data exists once, in Neo4j)
- Graph queries are always consistent with the latest data

**Disadvantages**:
- **Violates the PostgreSQL Source of Truth principle**: The PRD explicitly states PostgreSQL is the source of truth (PRD §3.4). This decision would require changing a core architecture principle.
- **No immutable versioning in Neo4j**: Neo4j does not have native support for immutable versioning. Implementing version chains, version history, and rollback in Neo4j would require significant custom development.
- **No mature audit/lineage capabilities**: PostgreSQL's audit logging, temporal tables, and lineage tracking are more mature than Neo4j's.
- **No JSONB for flexible metadata**: Neo4j properties are typed and indexed. Flexible metadata (cultural context, extraction metadata) is harder to query and index compared to PostgreSQL JSONB.
- **Graph database as system of record is risky**: Graph databases are optimized for relationship traversal, not for transactional integrity, complex queries, or reporting. Using Neo4j as the system of record for all knowledge data would force operational patterns that the database is not optimized for.
- **Higher operational maturity required**: Running Neo4j at scale as the primary database requires specialized expertise that is harder to staff than PostgreSQL.
- **AI Platform would need to write directly to Neo4j**: This violates the queue-driven AI architecture (ADR-004) and would require the AI Platform to have Neo4j credentials and drivers, increasing security surface area.

**Rejection rationale**: Making Neo4j the source of truth violates the established architecture principle and would lose the benefits of PostgreSQL's mature versioning, audit, and JSONB capabilities. The projection model provides the best combination: PostgreSQL for transactional integrity, versioning, and provenance; Neo4j for graph query performance.

## Alternative 3: Dual-Write (Write to Both PostgreSQL and Neo4j)

**Description**: Domain services write to both PostgreSQL and Neo4j in the same transaction. The service calls PostgreSQL first, then Neo4j. If Neo4j fails, the transaction is rolled back. Both databases are always consistent.

**Advantages**:
- Strong consistency between PostgreSQL and Neo4j — no projection lag
- No sync worker to build and maintain
- Simpler mental model — one write operation updates both stores
- Immediate graph availability after write

**Disadvantages**:
- **Neo4j availability affects write availability**: If Neo4j is down, writes to PostgreSQL are also blocked (or the transaction must be rolled back). This couples the availability of two systems.
- **Transaction coordination across heterogeneous systems**: PostgreSQL and Neo4j do not support distributed transactions. The application must implement a two-phase commit or compensate for failures manually.
- **Domain services need Neo4j drivers**: Every service that writes knowledge data must import Neo4j drivers, create sessions, and manage connections. This violates the "no direct writes to Neo4j" principle.
- **Write amplification**: Every write operation hits two databases, doubling write latency and increasing the chance of failure.
- **No human review gate enforcement**: If a service writes unapproved data to both PostgreSQL and Neo4j, the human review gate is bypassed. With the projection model, the projection worker can enforce the gate by only projecting approved content.
- **No rebuild capability**: If Neo4j data becomes corrupted, there is no clean way to rebuild it from PostgreSQL without replaying all writes. The projection model's rebuild is a batch operation that reads from PostgreSQL — it requires no write history.
- **Schema evolution complexity**: Changing the graph schema requires coordinated changes across all domain services that write to Neo4j.

**Rejection rationale**: Dual-write couples the availability of PostgreSQL and Neo4j, requires domain services to import Neo4j drivers, and makes rebuilds difficult. The event-driven projection model provides better decoupling, availability, and recoverability. The eventual consistency of the projection model is acceptable for the platform's use cases.

## Alternative 4: Materialized Views in PostgreSQL for Graph Queries

**Description**: Instead of Neo4j, use PostgreSQL materialized views that are pre-computed to represent graph relationships. Queries read from materialized views instead of running recursive CTEs. Refresh the views periodically or on-demand.

**Advantages**:
- Single database — no Neo4j infrastructure
- Materialized views provide better query performance than recursive CTEs
- REFRESH MATERIALIZED VIEW CONCURRENTLY allows non-blocking updates
- Views can be indexed for common graph traversal patterns
- Strong consistency for view refresh (within a single database)

**Disadvantages**:
- **Pre-computed views do not handle arbitrary graph traversals**: A materialized view can optimize specific query patterns (e.g., "entity + all neighbors"), but cannot support arbitrary multi-hop traversals. Every query pattern must be anticipated and pre-computed.
- **View refresh time grows with data volume**: REFRESH MATERIALIZED VIEW on a 100M relationship table takes hours. CONCURRENTLY refresh is slower and requires a unique index.
- **No transitive closure**: Materialized views cannot efficiently represent "find all paths between two entities" or "shortest path" queries. These require recursive processing regardless of pre-computation.
- **No graph analytics**: Centrality, community detection, and path finding algorithms would need to be implemented in application code using the materialized views.
- **No graph visualization ecosystem**: Neo4j's Bloom, Browser, and GraphQL integrations provide immediate value that would need to be built from scratch.
- **Storage duplication**: Materialized views duplicate data already in PostgreSQL, consuming additional storage without providing the graph-native performance of Neo4j.

**Rejection rationale**: Materialized views improve performance for known, limited query patterns but cannot support the arbitrary graph exploration that is core to the platform's value proposition. The cost of pre-computing all possible graph traversals at 100M relationships is prohibitive. Neo4j's native graph storage provides graph-native performance for arbitrary queries without pre-computation.

# Consequences

## Positive

1. **Performance for graph queries**: Neo4j's native graph storage provides sub-100ms traversal for 3–5 hop queries at 100M relationships. This makes interactive graph exploration possible for researchers and readers.

2. **Full rebuild capability**: The graph can be rebuilt from PostgreSQL at any time. Estimated rebuild time is ~3 hours at target scale. This eliminates the risk of Neo4j data corruption — recovery is always possible.

3. **Human review gate enforced by architecture**: The projection worker only consumes events for APPROVED/PUBLISHED content. REVIEW_REQUIRED content is never projected. It is architecturally impossible for unverified AI outputs to appear in the knowledge graph.

4. **Eventual consistency is acceptable**: The sub-second to second projection lag is acceptable for the platform's use cases. Interactive graph exploration is primarily a research and reading activity, not a real-time operation.

5. **Projection state observability**: The `projection_state` table provides complete observability into what has been projected, what is pending, and what has failed. Dashboards and alerts provide operational visibility.

6. **Idempotent processing**: MERGE operations ensure that duplicate events (from at-least-once delivery) do not corrupt the graph. The projection worker can safely reprocess events.

7. **Independent scaling**: PostgreSQL scales for transactional throughput. Neo4j scales for graph query performance. Each can be scaled independently based on usage patterns.

8. **Graph schema versioning**: Schema changes are managed through versioned migrations. Adding new node types or relationship types is a controlled process with rollback capability.

## Negative

1. **Projection lag**: There is a window (sub-second to seconds) between a PostgreSQL write and its appearance in Neo4j. Users who create content will not see it in the graph immediately.

2. **Eventual consistency complexity**: Application code must handle the case where data exists in PostgreSQL but not yet in Neo4j. For content that the user just created, the application should read from PostgreSQL directly rather than from Neo4j.

3. **Operational overhead of Neo4j**: Neo4j requires its own infrastructure (servers, storage, backup, monitoring). For a small team, this is a significant operational burden.

4. **Rebuild time at scale**: A full rebuild at 100M relationships takes ~3 hours. During this time, the graph is unavailable for queries. Partial rebuilds (per tenant) are faster but still significant.

5. **Storage duplication**: Data exists in PostgreSQL and is duplicated (in different format) in Neo4j. At 100M relationships, Neo4j storage is estimated at 10–20GB plus indexes.

6. **No cross-tenant graph queries**: Tenant isolation prevents queries that span tenants. A researcher cannot discover related entities owned by another tenant. This is by design for security but limits cross-tenant knowledge discovery.

7. **No native Neo4j multi-tenancy**: Unlike Weaviate (which has native multi-tenancy), Neo4j tenant isolation is handled through application-level `tenant_id` filtering. This adds query complexity and a small performance overhead.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Query performance** | < 100ms multi-hop traversals at 100M relationships | Neo4j infrastructure to operate |
| **Consistency** | Strong consistency in PostgreSQL | Eventual consistency (sub-second to seconds) in Neo4j |
| **Recoverability** | Full rebuild from PostgreSQL in ~3 hours | Graph unavailable during rebuild |
| **Data volume** | Optimized for graph storage | Storage duplication (~10–20GB extra at scale) |
| **Tenant isolation** | Application-level filtering works | No native Neo4j multi-tenancy |
| **Schema evolution** | Versioned graph schema migrations | Must keep graph schema in sync with PostgreSQL schema |
| **Operational simplicity** | Clear separation: PostgreSQL for writes, Neo4j for reads | Two database systems to manage |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Neo4j becomes unavailable** | Low | High — graph queries fail but writes continue | Circuit breaker in query services. Return degraded response (no graph visualization). Auto-rebuild from events when Neo4j recovers. |
| **Projection worker falls behind** | Medium | Medium — stale graph data | Monitor lag. Auto-scale worker based on queue depth. Prioritize events by tenant activity. |
| **Projection worker crashes mid-event** | Low | Medium — event not processed | Consumer group offset management ensures events are re-processed after restart. Idempotent MERGE prevents duplicates. |
| **Neo4j runs out of disk space** | Low | Critical — Neo4j crashes | Monitor disk usage. Set alerts at 70%, 85%, 95%. Implement data retention policies for archived content. |
| **MERGE creates duplicate nodes due to missing constraint** | Low | Medium — duplicate graph data | Enforce uniqueness constraints in Neo4j (`CREATE CONSTRAINT FOR (n:Entity) REQUIRE n.id IS UNIQUE`). |
| **Graph schema migration fails** | Low | Medium — broken graph queries | Test migrations in staging. Maintain rollback scripts. Keep previous schema version documentation. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Developer accidentally writes directly to Neo4j** | Medium | High — data inconsistency, broken provenance | Network-level isolation: Neo4j only accessible from projection worker subnets. Code review enforces no Neo4j drivers in domain services. |
| **Rebuild takes longer than expected** | Medium | Medium — extended graph downtime | Test rebuild times during performance testing. Implement parallel rebuild strategies. Use Neo4j admin import for bulk data. |
| **Projection state diverges from actual Neo4j state** | Medium | Medium — silent data inconsistency | Run periodic reconciliation: compare Neo4j node count vs PostgreSQL row count per entity type. Alert on divergence > 1%. |
| **Neo4j backup strategy confusing** | Medium | Medium — incorrect recovery procedures | Document clear recovery runbooks. Only PostgreSQL requires PITR; Neo4j recovery = rebuild from PostgreSQL. |
| **Cypher query performance regression** | Medium | Medium — slow graph exploration | PROFILE queries in staging before deploying. Use query logging in production. Implement query timeout. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Graph scale exceeds 1B relationships** | Rebuild time exceeds 12 hours | Implement incremental rebuild (continuous reconciliation). Partition graph by tenant or region. Consider Neo4j Fabric (sharding). |
| **New relationship types require schema migration** | Migration must be applied without downtime | Neo4j schema changes are typically additive (new labels, new relationship types). Test migration performance at scale. |
| **Real-time graph updates required** | Eventual consistency may not be sufficient | Reduce projection lag by moving from event-driven to CDC-based (Change Data Capture) synchronization using Debezium. |
| **Multi-region Neo4j deployment required** | Graph data must be synchronized across regions | Neo4j does not support multi-region clusters natively. Consider read replicas per region with async replication from a primary. |
| **Graph neural network training requires graph snapshots** | Need consistent point-in-time graph exports | Implement snapshot export: read all nodes and relationships at a given timestamp. Export to standard graph format (GraphML, CSV). |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Graph scale exceeds 1B relationships**: At this scale, full rebuild time exceeds 12 hours. Implement incremental rebuild strategies, continuous reconciliation, or Neo4j Fabric for sharding.

2. **Real-time graph updates required**: If the platform needs sub-100ms projection lag for real-time features, replace event-driven synchronization with CDC-based (Change Data Capture) using Debezium to stream PostgreSQL changes directly to Neo4j.

3. **Neo4j adds native multi-tenancy**: If Neo4j introduces native multi-tenant support (similar to Weaviate's tenant-per-class model), migrate from application-level `tenant_id` filtering to native isolation. This would improve query performance and simplify tenant management.

4. **New graph database technology emerges**: If a new graph database provides significantly better performance, simpler operations, or native multi-tenancy, evaluate migration. The event-driven projection model makes migration easier — rebuild the new graph from PostgreSQL.

5. **Graph neural network pipeline requires training data**: If the platform trains GNN models on the knowledge graph, implement snapshot export capabilities for consistent point-in-time graph exports.

# References

- **Backend Platform PRD §3.4** — "PostgreSQL as Source of Truth" — Neo4j is a projection, not a source of truth.
- **Backend Platform PRD §11** — "Database Strategy" — Neo4j stores nodes, relationships, graph projections. Read only.
- **AI Platform PRD §6.7** — "Embedding Service" — Projection events for graph synchronization.
- **AI Platform PRD §12** — "Queue Architecture" — `graph.projection.requested` and `graph.projected` topics.
- **ADR-001: PostgreSQL as Source of Truth** — Neo4j as read-only graph projection.
- **ADR-003: Event-Driven Architecture** — Event replay for projection rebuilding.
- **ADR-004: Queue-Driven AI Platform** — Projection workers consume events, write to Neo4j.
- **ADR-005: Multi-Tenant Architecture** — Tenant isolation through `tenant_id` property on all nodes.
- **ADR-007: Canonical Story Core Contract** — Entities, claims, themes, motifs extracted from Canonical Story.
- **ADR-008: Immutable Versioning** — Graph reflects current (latest) version, not historical versions.
- **Knowledge Graph Modeling** — `docs/architecture/knowledge-graph-modeling.md` — Detailed Neo4j data model.
- **Neo4j Documentation** — https://neo4j.com/docs/ — Cypher query language, constraints, indexes, and administration.
- **Neo4j MERGE** — https://neo4j.com/docs/cypher-manual/current/clauses/merge/ — Idempotent create-or-update pattern.
- **APOC Path Expansion** — https://neo4j.com/docs/apoc/current/overview/ — Graph traversal utilities for multi-hop queries.