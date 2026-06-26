# Database Ownership Matrix

## Version 1.0
## Status: Draft

---

# Overview

This document defines which service owns which database schemas and tables. Ownership means the service has exclusive write access; other services must read via APIs or events.

**Rule**: PostgreSQL is the single source of truth. Neo4j and Weaviate are read-only projections.

---

# Ownership Principles

1. **Each schema has exactly ONE owner service**
2. **No cross-service direct database writes**
3. **Read access** for other services is permitted via REST APIs
4. **Projection databases** (Neo4j, Weaviate) are owned by data-platform services
5. **Global schemas** (system, governance) are owned by shared infrastructure

---

# Schema Ownership Matrix

## identity-service

| Schema | Tables | Access Pattern | Notes |
|--------|--------|---------------|-------|
| `auth` | `users` | CRUD via API | User authentication & profiles |
| `iam` | `roles`, `permissions`, `role_permissions`, `user_roles`, `policies`, `policy_rules` | CRUD via API | Authorization & ABAC |
| `tenant` | `tenants`, `workspaces` | CRUD via API | Multi-tenancy |

**Read by**: All services (user context via JWT claims)
**Written by**: identity-service only

## content-service

| Schema | Tables | Access Pattern | Notes |
|--------|--------|---------------|-------|
| `source` | `channels`, `channel_snapshots`, `playlists`, `playlist_snapshots`, `videos`, `video_payload_versions`, `video_formats`, `video_chapters`, `video_tags`, `video_thumbnails`, `assets`, `subtitle_tracks`, `transcripts`, `speakers`, `transcript_segments`, `video_comments`, `ingestion_jobs`, `extraction_jobs` | CRUD via API | Content acquisition & processing |
| `content` | `stories`, `story_versions`, `story_evidence`, `articles` | CRUD via API | Stories & articles |

**Read by**: knowledge-service (via events + API), research-service (via API)
**Written by**: content-service only

## knowledge-service

| Schema | Tables | Access Pattern | Notes |
|--------|--------|---------------|-------|
| `knowledge` | `objects`, `object_aliases`, `entities`, `folklore_entities`, `characters`, `locations`, `themes`, `motifs`, `archetypes`, `narrative_patterns`, `claims`, `claim_sources`, `assertions`, `contradictions`, `contradiction_claims`, `sources`, `citations`, `entity_versions`, `entity_change_log`, `story_entities`, `story_themes`, `story_motifs`, `story_patterns` | CRUD via API | Knowledge graph data |
| `culture` | `cultures`, `ethnic_groups`, `regions`, `beliefs`, `traditions`, `rituals` | CRUD via API | Cultural domain data |

**Read by**: research-service (via API), data-platform (via events)
**Written by**: knowledge-service only

## research-service

| Schema | Tables | Access Pattern | Notes |
|--------|--------|---------------|-------|
| `research` | `story_genomes`, `story_similarity`, `narrative_dna`, `adaptation_scores`, `adaptation_reasons`, `knowledge_gaps`, `collections`, `annotations`, `notes` | CRUD via API | Research workspaces |

**Read by**: None (leaf context)
**Written by**: research-service only
**Reads from**: content-service, knowledge-service (via API)

## workflow-service

| Schema | Tables | Access Pattern | Notes |
|--------|--------|---------------|-------|
| `workflow` | `reviews`, `approvals`, `workflow_states`, `workflow_transitions` | CRUD via API | Review & approval workflows |
| `governance` | `audit_logs`, `lineage`, `knowledge_reviews`, `knowledge_quality_scores` | Write via events | Audit & quality |

**Read by**: content-service, knowledge-service (via API)
**Written by**: workflow-service only

## system (shared)

| Schema | Tables | Access Pattern | Notes |
|--------|--------|---------------|-------|
| `system` | `outbox_events`, `countries`, `configurations` | All services write to outbox | Infrastructure |

**Owned by**: Platform Engineering (shared infrastructure)
**Written by**: All services (outbox events)

## analytics

| Schema | Tables | Access Pattern | Notes |
|--------|--------|---------------|-------|
| `analytics` | `cultural_trends`, `theme_trends` | Write via events | Analytics projections |

**Owned by**: data-platform / analytics service
**Written by**: analytics service only

---

# Cross-Service Data Access

| Consumer Service | Reads From | Method | Caching |
|-----------------|-----------|--------|---------|
| gateway-service | All services | REST proxy | None |
| content-service | identity-service | JWT claims | In-memory |
| knowledge-service | content-service | Events + REST | Event-driven |
| research-service | content-service | REST | Local cache |
| research-service | knowledge-service | REST | Local cache |
| workflow-service | content-service | Events | Event-driven |
| workflow-service | knowledge-service | Events | Event-driven |
| neo4j-sync | knowledge-service | Events | None |
| weaviate-sync | knowledge-service | Events | None |

---

# Projection Database Ownership

## Neo4j (Knowledge Graph)

| Owner | Service | Sync Method |
|-------|---------|------------|
| neo4j-sync | data-platform/neo4j-sync | Event-driven from PostgreSQL |

**Write access**: neo4j-sync only
**Read access**: knowledge-service (via REST API), graph visualization tools

## Weaviate (Vector Search)

| Owner | Service | Sync Method |
|-------|---------|------------|
| weaviate-sync | data-platform/weaviate-sync | Event-driven from PostgreSQL |

**Write access**: weaviate-sync only
**Read access**: knowledge-service (via REST API), search functionality

---

# Forbidden Patterns

1. **Direct SQL** from one service to another service's database
2. **Shared JPA entities** across services
3. **Writing to Neo4j or Weaviate** outside data-platform services
4. **Cross-schema foreign keys** between different service schemas
5. **Database-level joins** across service boundaries

---

# References

- ADR-003: PostgreSQL as Source of Truth
- ADR-006: Service Boundaries and Ownership
- ddl.md - Complete Schema Design
- BACKEND-PRD.md §2.4 PostgreSQL Is Source of Truth