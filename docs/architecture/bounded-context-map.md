# Bounded Context Map

## Version 1.0
## Status: Draft

---

# Overview

This document defines the bounded contexts of The Living Atlas platform, their relationships, and the communication patterns between them. Each bounded context represents a distinct domain boundary with its own ubiquitous language, data ownership, and business logic.

---

# Context Map Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        IDENTITY CONTEXT                          │
│  Users · Tenants · Workspaces · Roles · ABAC Policies · API Keys │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ JWT + Claims                      │ JWT + Claims
               ▼                                   ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│       GATEWAY CONTEXT        │    │     WORKFLOW CONTEXT         │
│  Routing · Auth · Rate Limit │    │  Review · Approval · Publish │
│  Aggregation · CORS          │    │  Moderation · State Machine  │
└──────┬───────────────┬───────┘    └──────────────┬───────────────┘
       │               │                            │
       ▼               ▼                            ▼
┌──────────────┐ ┌──────────────┐    ┌──────────────────────────────┐
│    CONTENT   │ │  KNOWLEDGE   │    │        RESEARCH CONTEXT      │
│    CONTEXT   │ │   CONTEXT    │    │  Collections · Annotations   │
│              │ │              │    │  Notes · Saved Queries       │
│ Stories      │ │ Knowledge    │    │  Exports · Story DNA         │
│ Articles     │ │ Objects      │    └──────────────────────────────┘
│ Sources      │ │ Themes       │
│ Transcripts  │ │ Motifs       │    ┌──────────────────────────────┐
│ Evidence     │ │ Claims       │    │        AI CONTEXT            │
│ Versions     │ │ Contradict.  │    │  Ingestion · Extraction      │
└──────┬───────┘ │ Folklore     │    │  Enrichment · Embedding      │
       │         │ Culture      │    │  Article Gen · Orchestration │
       │         └──────┬───────┘    └──────────────────────────────┘
       │                │
       ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA PLATFORM CONTEXT                     │
│  Neo4j Sync · Weaviate Sync · Analytics · Lineage · Trends      │
└─────────────────────────────────────────────────────────────────┘
```

---

# Context Descriptions

## 1. Identity Context
**Service**: identity-service
**Schema**: `auth`, `iam`, `tenant`
**Ubiquitous Language**: User, Tenant, Workspace, Role, Permission, Policy, API Key
**Owner**: Platform Engineering

### Core Entities
- User (email, username, status)
- Tenant (slug, type, subscription)
- Workspace (slug, visibility, tenant-scoped)
- Role (code, name, permissions)
- Permission (resource_type, action)
- Policy (code, effect, rules)
- API Key (key_hash, scopes, tenant)

### Relationships
- **Upstream**: None (root context)
- **Downstream**: Gateway (JWT), Content (user context), Knowledge (user context)
- **Shared Kernel**: User identity claims in JWT

---

## 2. Gateway Context
**Service**: gateway-service
**Schema**: None (routing only)
**Ubiquitous Language**: Route, Rate Limit, CORS, Auth Token, API Version
**Owner**: Platform Engineering

### Core Responsibilities
- Request routing to appropriate services
- JWT validation and claim extraction
- Rate limiting per client/endpoint
- API versioning (URL path)
- Request/response transformation
- CORS management

### Relationships
- **Upstream**: Identity (JWT validation)
- **Downstream**: Content, Knowledge, Research, Workflow
- **Conformist**: Follows API contracts defined by downstream services

---

## 3. Content Context
**Service**: content-service
**Schema**: `source`, `content`
**Ubiquitous Language**: Story, Article, Source, Channel, Video, Transcript, Evidence, Version
**Owner**: Content Team

### Core Entities
- Channel (platform, name, metadata)
- Video (title, description, duration)
- Transcript (type, language, content)
- TranscriptSegment (timestamp, content, speaker)
- Story (title, type, status)
- StoryVersion (immutable content snapshot)
- Article (type, content, status)
- Evidence (story_id, segment_id, confidence)

### Relationships
- **Upstream**: Identity (user context), Gateway (API)
- **Downstream**: Knowledge (events), Workflow (events), Research (read)
- **Published Language**: StoryCreated, ArticlePublished events

---

## 4. Knowledge Context
**Service**: knowledge-service
**Schema**: `knowledge`, `culture`
**Ubiquitous Language**: Knowledge Object, Entity, Theme, Motif, Claim, Contradiction, Folklore, Culture
**Owner**: Knowledge Team

### Core Entities
- KnowledgeObject (type, canonical_name, confidence)
- Entity (type: spirit, ghost, folklore, location)
- Theme (name, description)
- Motif (name, description)
- Claim (text, type, confidence, status)
- Contradiction (entity, conflicting claims)
- Assertion (subject, predicate, object)
- Citation (source, target)

### Relationships
- **Upstream**: Content (events), AI Enrichment (events)
- **Downstream**: Data Platform (events for Neo4j/Weaviate sync)
- **Published Language**: KnowledgeObjectCreated, ClaimCreated events

---

## 5. Research Context
**Service**: research-service
**Schema**: `research`
**Ubiquitous Language**: Collection, Annotation, Note, Saved Query, Export, Story DNA
**Owner**: Research Team

### Core Entities
- Collection (name, description, items)
- Annotation (target, content, type)
- ResearchNote (content, references)
- SavedQuery (query, filters, metadata)
- StoryGenome (theme/motif/archetype vectors)
- StorySimilarity (story pair, score)

### Relationships
- **Upstream**: Content (read stories), Knowledge (read objects)
- **Downstream**: None (leaf context)
- **Conformist**: Reads from Content and Knowledge contexts

---

## 6. Workflow Context
**Service**: workflow-service
**Schema**: `workflow`, `governance`
**Ubiquitous Language**: Review, Approval, Rejection, State Machine, Transition, Moderation
**Owner**: Editorial Team

### Core Entities
- Review (target_type, target_id, reviewer, status)
- Approval (review_id, decision, notes)
- WorkflowState (entity_type, entity_id, current_state)
- WorkflowTransition (from_state, to_state, trigger)

### Relationships
- **Upstream**: Content (events), Knowledge (events)
- **Downstream**: Content (events), Knowledge (events)
- **Published Language**: ReviewApproved, ReviewRejected events

---

## 7. AI Context
**Services**: ingestion-service, extraction-service, enrichment-service, embedding-service, article-service, orchestration-service
**Schema**: `ai`
**Ubiquitous Language**: Pipeline, Job, Model, Extraction, Embedding, Generation
**Owner**: AI Team

### Core Entities
- PipelineJob (type, status, progress)
- ExtractionResult (entities, themes, claims)
- EmbeddingVector (object_id, vector, model)
- GeneratedArticle (type, content, sources)

### Relationships
- **Upstream**: Content (events trigger pipeline)
- **Downstream**: Content (results), Knowledge (extracted knowledge)
- **Published Language**: PipelineCompleted, EnrichmentJobCompleted events

---

## 8. Data Platform Context
**Services**: neo4j-sync, weaviate-sync, analytics
**Schema**: None (projection only)
**Ubiquitous Language**: Graph Node, Graph Relationship, Vector Index, Embedding, Trend
**Owner**: Data Engineering

### Core Responsibilities
- Sync PostgreSQL data to Neo4j (graph projection)
- Sync embeddings to Weaviate (vector projection)
- Compute analytics and trends
- Track data lineage

### Relationships
- **Upstream**: Knowledge (events), Content (events)
- **Downstream**: None (read-only projections)
- **Conformist**: Consumes events from Knowledge and Content contexts

---

# Context Interaction Matrix

| From \ To | Identity | Gateway | Content | Knowledge | Research | Workflow | AI | Data Platform |
|-----------|----------|---------|---------|-----------|----------|----------|-----|---------------|
| Identity | - | JWT | Claims | Claims | Claims | Claims | - | - |
| Gateway | Validate | - | Route | Route | Route | Route | Route | - |
| Content | - | API | - | Events | Read | Events | Events | - |
| Knowledge | - | API | Events | - | Read | Events | - | Events |
| Research | - | API | Read | Read | - | - | - | - |
| Workflow | - | API | Events | Events | - | - | - | - |
| AI | - | API | Events | Events | - | - | - | - |
| Data Platform | - | API | - | - | - | - | - | - |

**Legend**: 
- **JWT**: Token-based authentication
- **Route**: HTTP request routing
- **Events**: Asynchronous domain events
- **Read**: Read-only data access
- **API**: REST API calls
- **Claims**: User/tenant context propagation

---

# Context Boundary Rules

1. **No direct database access** across context boundaries
2. **No shared JPA entities** between contexts
3. **Contexts communicate via**:
   - REST APIs (synchronous queries)
   - Domain Events (asynchronous state changes)
4. **Each context owns its schema(s)** exclusively
5. **Contexts may read** from other contexts via REST APIs
6. **Contexts must not write** to another context's database

---

# References

- ADR-005: DDD Modular Structure
- ADR-006: Service Boundaries and Ownership
- ADR-007: Multi-Tenancy Strategy
- BACKEND-PRD.md §3 Functional Domains