# Knowledge Graph Modeling Specification

## Version 1.0
## Status: Draft

---

# Overview

This document defines the knowledge graph model for The Living Atlas. The knowledge graph (Neo4j) is a read-only projection of the PostgreSQL source of truth, optimized for relationship traversal queries: entity connections, story similarity, cultural lineage, and narrative pattern discovery.

---

# Architecture Principles

1. **PostgreSQL is source of truth** — Neo4j is a derived projection
2. **Event-driven sync** — Changes flow via domain events
3. **Idempotent upserts** — Replay-safe sync operations
4. **Read-optimized** — Graph model optimized for traversal, not CRUD
5. **Rebuildable** — Full graph can be rebuilt from PostgreSQL

---

# Node Types

## Core Nodes

### :Entity
Represents a knowledge entity (spirit, ghost, folklore, person, location).

```cypher
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.sourceId IS UNIQUE;

(:Entity {
  sourceId: "uuid",           // PostgreSQL knowledge.objects.id
  type: "spirit",             // entity_type from knowledge.entities
  name: "Kuntilanak",         // canonical_name
  slug: "kuntilanak",
  summary: "A vengeful female spirit...",
  confidence: 0.95,
  status: "active",
  aliases: ["Pontianak", "Kuntilanak"],
  metadata: {},
  createdAt: datetime("2026-06-20T01:00:00Z"),
  updatedAt: datetime("2026-06-20T01:00:00Z")
})
```

### :Story
Represents a narrative story extracted from content.

```cypher
(:Story {
  sourceId: "uuid",           // PostgreSQL content.stories.id
  title: "The Legend of Kuntilanak",
  slug: "the-legend-of-kuntilanak",
  summary: "A traditional folklore about...",
  type: "folklore",           // story_type
  status: "published",
  confidence: 0.88,
  languageCode: "id",
  sourceVideoId: "uuid",
  metadata: {},
  createdAt: datetime("2026-06-20T01:00:00Z"),
  updatedAt: datetime("2026-06-20T02:00:00Z")
})
```

### :Theme
Represents a narrative theme.

```cypher
(:Theme {
  sourceId: "uuid",
  name: "Fear",
  slug: "fear",
  description: "Stories centered on fear and terror",
  storyCount: 120,
  createdAt: datetime("2026-06-20T01:00:00Z")
})
```

### :Motif
Represents a narrative motif.

```cypher
(:Motif {
  sourceId: "uuid",
  name: "Mysterious Voice",
  slug: "mysterious-voice",
  description: "Unexplained sounds or voices",
  storyCount: 45,
  createdAt: datetime("2026-06-20T01:00:00Z")
})
```

### :Culture
Represents a cultural group.

```cypher
(:Culture {
  sourceId: "uuid",
  name: "Dayak",
  slug: "dayak",
  description: "Indigenous people of Borneo",
  region: "Kalimantan",
  createdAt: datetime("2026-06-20T01:00:00Z")
})
```

### :Location
Represents a geographic location.

```cypher
(:Location {
  sourceId: "uuid",
  name: "Pontianak",
  slug: "pontianak",
  type: "city",
  region: "West Kalimantan",
  country: "Indonesia",
  countryCode: "ID",
  latitude: -0.026330,
  longitude: 109.342504,
  isSensitive: false,
  createdAt: datetime("2026-06-20T01:00:00Z")
})
```

### :Belief
Represents a belief system.

```cypher
(:Belief {
  sourceId: "uuid",
  name: "Ancestor Worship",
  slug: "ancestor-worship",
  description: "Veneration of deceased ancestors",
  createdAt: datetime("2026-06-20T01:00:00Z")
})
```

### :Claim
Represents a knowledge claim with evidence.

```cypher
(:Claim {
  sourceId: "uuid",
  text: "Kuntilanak originates from Dayak mythology",
  type: "origin",
  confidence: 0.75,
  status: "unverified",
  createdAt: datetime("2026-06-20T01:00:00Z")
})
```

### :Source
Represents a content source (video, podcast, book).

```cypher
(:Source {
  sourceId: "uuid",
  type: "youtube",
  title: "MISTERI KUNTILANAK DI PONTIANAK",
  platformVideoId: "abc123xyz",
  channelName: "Jurnal Risa Official",
  publishedAt: datetime("2026-06-01T00:00:00Z"),
  durationSeconds: 1800,
  url: "https://youtube.com/watch?v=abc123xyz",
  createdAt: datetime("2026-06-20T01:00:00Z")
})
```

---

# Relationship Types

## Entity Relationships

| Relationship | From | To | Description |
|-------------|------|----|-------------|
| `APPEARS_IN` | :Entity | :Location | Entity is associated with location |
| `ORIGINATES_FROM` | :Entity | :Culture | Entity originates from culture |
| `ASSOCIATED_WITH` | :Entity | :Belief | Entity linked to belief system |
| `RELATED_TO` | :Entity | :Entity | General entity relationship |
| `VARIANT_OF` | :Entity | :Entity | Regional/cultural variant |
| `CONTRADICTS` | :Entity | :Entity | Conflicting descriptions |

## Story Relationships

| Relationship | From | To | Description |
|-------------|------|----|-------------|
| `FEATURES` | :Story | :Entity | Story mentions entity |
| `HAS_THEME` | :Story | :Theme | Story embodies theme |
| `HAS_MOTIF` | :Story | :Motif | Story contains motif |
| `HAS_CLAIM` | :Story | :Claim | Story contains claim |
| `DERIVED_FROM` | :Story | :Source | Story extracted from source |
| `SIMILAR_TO` | :Story | :Story | Narrative similarity |
| `REFERENCES` | :Story | :Story | Story references another story |

## Knowledge Relationships

| Relationship | From | To | Description |
|-------------|------|----|-------------|
| `HAS_CULTURE` | :Entity | :Culture | Entity belongs to culture |
| `HAS_BELIEF` | :Entity | :Belief | Entity associated with belief |
| `LOCATED_IN` | :Entity | :Location | Entity located in place |
| `EVIDENCED_BY` | :Claim | :Story | Claim supported by story |
| `CONTRADICTS` | :Claim | :Claim | Conflicting claims |

## Cultural Relationships

| Relationship | From | To | Description |
|-------------|------|----|-------------|
| `PART_OF` | :Culture | :Culture | Sub-culture relationship |
| `INFLUENCED_BY` | :Culture | :Culture | Cultural influence |
| `PRACTICES` | :Culture | :Belief | Culture practices belief |
| `LOCATED_IN` | :Culture | :Location | Culture geographic area |

---

# Graph Model Diagram

```
                    ┌──────────┐
                    │  Source  │
                    └────┬─────┘
                         │ DERIVED_FROM
                         ▼
                    ┌──────────┐
     ┌─────────────│  Story   │─────────────┐
     │             └────┬─────┘             │
     │                  │                   │
     │ FEATURES    HAS_THEME  HAS_MOTIF     │
     ▼                  ▼         ▼         │
┌──────────┐     ┌──────────┐ ┌──────────┐  │
│ Entity   │     │  Theme   │ │  Motif   │  │
└────┬─────┘     └──────────┘ └──────────┘  │
     │                                       │
     ├── APPEARS_IN ──► Location             │
     ├── ORIGINATES_FROM ──► Culture         │
     ├── ASSOCIATED_WITH ──► Belief          │
     └── RELATED_TO ──► Entity              │
                                            │
                    ┌──────────┐            │
                    │  Claim   │◄───────────┘
                    └────┬─────┘   HAS_CLAIM
                         │
                    EVIDENCED_BY
                         │
                    ┌──────────┐
                    │  Story   │
                    └──────────┘
```

---

# Query Patterns

## 1. Entity Detail with Relationships
```cypher
MATCH (e:Entity {slug: "kuntilanak"})
OPTIONAL MATCH (e)-[r]->(related)
RETURN e, collect({type: type(r), node: related}) AS relationships
```

## 2. Story Network (2-hop traversal)
```cypher
MATCH (s:Story {slug: "the-legend-of-kuntilanak"})
OPTIONAL MATCH (s)-[:FEATURES]->(e:Entity)
OPTIONAL MATCH (e)<-[:FEATURES]-(relatedStory:Story)
WHERE relatedStory <> s
RETURN s, e, relatedStory
LIMIT 50
```

## 3. Cultural Entity Map
```cypher
MATCH (c:Culture {name: "Dayak"})
OPTIONAL MATCH (c)<-[:ORIGINATES_FROM]-(e:Entity)
OPTIONAL MATCH (e)-[:APPEARS_IN]->(l:Location)
OPTIONAL MATCH (e)-[:ASSOCIATED_WITH]->(b:Belief)
RETURN c, collect(DISTINCT e) AS entities, 
       collect(DISTINCT l) AS locations,
       collect(DISTINCT b) AS beliefs
```

## 4. Theme-Based Story Discovery
```cypher
MATCH (t:Theme {slug: "fear"})
MATCH (s:Story)-[:HAS_THEME]->(t)
MATCH (s)-[:FEATURES]->(e:Entity)
WHERE s.status = "published"
RETURN t, s, collect(e) AS entities
ORDER BY s.updatedAt DESC
LIMIT 20
```

## 5. Contradiction Detection
```cypher
MATCH (c1:Claim)-[:CONTRADICTS]-(c2:Claim)
OPTIONAL MATCH (c1)<-[:HAS_CLAIM]-(s1:Story)
OPTIONAL MATCH (c2)<-[:HAS_CLAIM]-(s2:Story)
RETURN c1.text AS claim1, c2.text AS claim2,
       s1.title AS story1, s2.title AS story2
```

## 6. Story Similarity (based on shared entities/themes)
```cypher
MATCH (s1:Story {slug: "the-legend-of-kuntilanak"})
MATCH (s1)-[:FEATURES|HAS_THEME|HAS_MOTIF]->(shared)<-[:FEATURES|HAS_THEME|HAS_MOTIF]-(s2:Story)
WHERE s2 <> s1
RETURN s2.title, count(shared) AS similarityScore
ORDER BY similarityScore DESC
LIMIT 10
```

---

# Index Strategy

```cypher
// Unique constraints (for idempotent upserts)
CREATE CONSTRAINT entity_source_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.sourceId IS UNIQUE;
CREATE CONSTRAINT story_source_id IF NOT EXISTS FOR (s:Story) REQUIRE s.sourceId IS UNIQUE;
CREATE CONSTRAINT theme_source_id IF NOT EXISTS FOR (t:Theme) REQUIRE t.sourceId IS UNIQUE;
CREATE CONSTRAINT motif_source_id IF NOT EXISTS FOR (m:Motif) REQUIRE m.sourceId IS UNIQUE;
CREATE CONSTRAINT culture_source_id IF NOT EXISTS FOR (c:Culture) REQUIRE c.sourceId IS UNIQUE;
CREATE CONSTRAINT location_source_id IF NOT EXISTS FOR (l:Location) REQUIRE l.sourceId IS UNIQUE;
CREATE CONSTRAINT belief_source_id IF NOT EXISTS FOR (b:Belief) REQUIRE b.sourceId IS UNIQUE;
CREATE CONSTRAINT claim_source_id IF NOT EXISTS FOR (c:Claim) REQUIRE c.sourceId IS UNIQUE;
CREATE CONSTRAINT source_source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.sourceId IS UNIQUE;

// Indexes for common queries
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_slug IF NOT EXISTS FOR (e:Entity) ON (e.slug);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX story_status IF NOT EXISTS FOR (s:Story) ON (s.status);
CREATE INDEX story_type IF NOT EXISTS FOR (s:Story) ON (s.type);
CREATE INDEX story_slug IF NOT EXISTS FOR (s:Story) ON (s.slug);
CREATE INDEX theme_slug IF NOT EXISTS FOR (t:Theme) ON (t.slug);
CREATE INDEX motif_slug IF NOT EXISTS FOR (m:Motif) ON (m.slug);
CREATE INDEX culture_name IF NOT EXISTS FOR (c:Culture) ON (c.name);
CREATE INDEX location_name IF NOT EXISTS FOR (l:Location) ON (l.name);
```

---

# Sync Strategy

## Event-Driven Sync
```
PostgreSQL Change → Domain Event → neo4j-sync → Neo4j Upsert
```

## Sync Operations
| Event | Graph Operation |
|-------|----------------|
| KnowledgeObjectCreated | MERGE (:Entity {sourceId}) SET ... |
| KnowledgeObjectUpdated | MATCH (:Entity {sourceId}) SET ... |
| KnowledgeObjectMerged | MERGE target, DELETE source |
| StoryCreated | MERGE (:Story {sourceId}) SET ... |
| StoryPublished | MATCH (:Story {sourceId}) SET status: "published" |
| EntityLinkedToStory | MATCH (e:Entity), (s:Story) MERGE (s)-[:FEATURES]->(e) |
| ThemeExtracted | MERGE (:Theme {sourceId}) SET ... |
| MotifExtracted | MERGE (:Motif {sourceId}) SET ... |
| ClaimCreated | MERGE (:Claim {sourceId}) SET ... |

## Full Rebuild
```bash
# Batch job to rebuild entire graph from PostgreSQL
neo4j-sync rebuild --batch-size=1000 --parallel=4
```

---

# Performance Targets

| Query Type | Target | Index Used |
|-----------|--------|------------|
| Single entity lookup | < 10ms | sourceId unique constraint |
| Entity with 1-hop relationships | < 50ms | sourceId + relationship index |
| Story with 2-hop network | < 200ms | Relationship traversal |
| Theme-based story list | < 100ms | Theme index + relationship |
| Contradiction detection | < 500ms | Claim relationship index |
| Full-text search (entity name) | < 50ms | Entity name index |

---

# References

- ADR-010: Knowledge Graph Strategy
- ddl.md - Knowledge & Culture Domain
- plan.md - data-platform/neo4j-sync
- BACKEND-PRD.md §3 Knowledge Domain