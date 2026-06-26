# Gap Analysis: Backend Services vs. PRD & ADR Requirements

**Date:** 2026-06-25  
**Scope:** `services/` directory — Java/Spring Boot backend  
**Reference:** `docs/prd/backend-platform-prd.md`, `docs/adr/ADR-001` through `ADR-015`

---

## 1. Current State Overview

### 1.1 Module Structure (from `services/pom.xml`)

```
services/
├── pom.xml                          # Parent POM (Spring Boot 4.0.7, Java 25)
├── shared-events/                   # Shared event definitions
├── shared-web/                      # Shared web utilities
├── gateway-services/                # API Gateway / Edge routing
├── identity-service/                # Identity, RBAC, ABAC, Audit domains
├── content-service/                 # Source, Story, Article domains
├── knowledge-service/               # Knowledge, Claims, Folklore, Beliefs, Traditions domains
├── research-service/                # Collections, Annotations, Notes, Exports domains
└── workflow-service/                # Approval, Publishing, Moderation domains
```

### 1.2 Technology Stack (from `pom.xml`)

| Technology | Version | Notes |
|-----------|---------|-------|
| Spring Boot | 4.0.7 | Latest |
| Java | 25 | Latest |
| Lombok | 1.18.38 | Code generation |
| SpringDoc OpenAPI | 3.0.2 | API documentation |
| jjwt | 0.13.0 | JWT authentication |
| Spring Cloud | 2025.1.2 | Gateway, service discovery |
| Bucket4j | 8.7.0 | Rate limiting |
| Caffeine | 3.1.8 | Caching |

### 1.3 Key Observations

- **Multiple services deployed independently** (not a modular monolith single JAR as ADR-002 requires)
- **No Redpanda client dependency** in POM — event-driven architecture (ADR-003) not yet implemented in Java backend
- **No Neo4j or Weaviate dependencies** — correct per ADR-001 (projections are Python workers)
- **No AI Platform integration libraries** — correct per ADR-004 (queue-driven, no REST)
- **Basic RBAC entities exist** (Role, Permission) — ABAC extension needed per ADR-006
- **Lineage entity exists** in identity-service — provenance foundation per ADR-014
- **Audit fields present** on entities (created_at, created_by, updated_at, updated_by, version, is_deleted)

---

## 2. Gap Analysis by ADR

### ADR-001: PostgreSQL as Source of Truth

**Status:** ⚠️ PARTIALLY IMPLEMENTED

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| PostgreSQL is the single source of truth | ✅ Services use JPA/Hibernate with PostgreSQL | No gap |
| No direct writes to Neo4j | ✅ No Neo4j dependencies in services | No gap |
| No direct writes to Weaviate | ✅ No Weaviate dependencies in services | No gap |
| Transactional outbox pattern | ❌ Not implemented | **Missing**: No outbox tables, no outbox publisher |
| Projection workers are separate | ✅ (Python workers, outside `services/`) | No gap |
| AI workers write only to PostgreSQL | ✅ (AI Platform is Python, writes to PG) | No gap |

**Actions Required:**
- Implement outbox table per bounded context (`identity_outbox`, `content_outbox`, `knowledge_outbox`, etc.)
- Implement outbox publisher (background process polling unpublished events)
- Add outbox event serialization for Redpanda topics

---

### ADR-002: Modular Monolith First

**Status:** ❌ NOT IMPLEMENTED — CURRENT STATE IS MICROSERVICES

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Single deployment artifact (one JAR) | ❌ 7 separate services, each deployable independently | **Critical gap**: Multiple JARs, multiple deployments |
| Module isolation via package structure | ⚠️ Services have DDD-like structure but process boundaries exist | Modules are in separate services, not packages |
| Shared kernel is minimal and stable | ✅ `shared-events` and `shared-web` exist | No gap conceptually, but extraction not needed since they're shared libraries |
| Database schema is unified but namespaced | ⚠️ Domain-prefixed tables exist but across service databases | Multiple datasources, not a single database |
| In-process events for sync, Redpanda for async | ❌ No in-process event system, no Redpanda | **Missing**: Spring `ApplicationEventPublisher` not used across modules |
| API Gateway remains separate | ✅ `gateway-services/` exists | No gap |
| AI Platform remains separate | ✅ Python AI Platform outside `services/` | No gap |

**Actions Required:**
- **Critical**: Consolidate all services into a single Spring Boot application module
- Create a single `living-atlas-backend` module that aggregates all domain packages
- Configure single Flyway migration sequence with domain-prefixed migration names
- Replace inter-service REST calls with in-process Java calls (Spring `ApplicationEventPublisher`)
- Remove separate service entry points (keep only Gateway as separate process)
- Add ArchUnit tests for module boundary enforcement

**Migration Strategy:**
The current multi-service structure was likely intended for future microservices. Per ADR-002, these should be merged into a single deployable unit:

```
Current:                              Target:
services/                             services/
├── identity-service/     ──────────► ├── living-atlas-backend/
├── content-service/      ──────────► │   ├── src/main/java/id/livingatlas/
├── knowledge-service/    ──────────► │   │   ├── identity/ (was identity-service)
├── research-service/     ──────────► │   │   ├── content/  (was content-service)
├── workflow-service/     ──────────► │   │   ├── knowledge/ (was knowledge-service)
├── gateway-services/     ── KEEP ──► │   │   ├── research/ (was research-service)
├── shared-events/        ── KEEP ──► │   │   ├── workflow/ (was workflow-service)
└── shared-web/           ── KEEP ──► │   │   └── shared/   (was shared-events + shared-web)
                                      │   └── ...
                                      └── gateway-services/ (separate process)
```

---

### ADR-003: Event-Driven Architecture

**Status:** ❌ NOT IMPLEMENTED

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Redpanda is the event backbone | ❌ No Redpanda dependency in POM | **Critical missing**: No event infrastructure |
| Transactional outbox pattern | ❌ Not implemented | **Missing**: No outbox tables or publisher |
| Event schema with versioning | ❌ Not implemented | **Missing**: No event classes or versioning |
| Partitioning by aggregate_id | ❌ Not implemented | — |
| Consumer group isolation | ❌ Not implemented | — |
| Event replay mechanism | ❌ Not implemented | — |
| Idempotent event handlers | ❌ Not implemented | — |
| Dead letter queue | ❌ Not implemented | — |
| Monitoring and observability for events | ❌ Not implemented | — |

**Actions Required:**
- Add Redpanda/Kafka client dependency to parent POM
- Implement transactional outbox pattern (outbox table + publisher)
- Create event classes for all required events (14 events from PRD §10)
- Implement event schema versioning
- Configure consumer groups for domain services
- Implement idempotent event handlers (ProcessedEventTracker)
- Implement dead letter queue handling
- Add event monitoring metrics (Prometheus)

---

### ADR-004: Queue-Driven AI Platform

**Status:** ⚠️ PARTIALLY IMPLEMENTED (by omission — backend correctly does not call AI Platform via REST)

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| No REST calls from backend to AI Platform | ✅ Backend services don't import AI Platform SDKs | No gap |
| Backend publishes events to Redpanda for AI | ❌ No Redpanda/event publishing implemented | **Missing**: Event publishing infrastructure |
| AI workers write results to PostgreSQL | ✅ (AI Platform is Python, writes to PG) | No gap |
| Backend reads AI results from PostgreSQL | ⚠️ Not yet implemented (no event-driven consumption) | **Missing**: Backend doesn't consume AI completion events |
| Human review gate in PostgreSQL | ⚠️ Workflow domain exists but review state machine not fully implemented | See ADR-013 |

**Actions Required:**
- Implement event publishing from backend when content is ready for AI processing
- Implement event consumption in backend for AI completion events
- Add status polling/queries for AI processing results

---

### ADR-005: Multi-Tenant Architecture

**Status:** ⚠️ PARTIALLY IMPLEMENTED

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Shared database, shared schema | ❌ Multiple services = multiple datasources | Once consolidated into monolith, this is satisfied |
| `tenant_id` and `workspace_id` on all business tables | ⚠️ Some entities have tenant_id, but not consistently enforced | **Gap**: Not all entities have tenant_id + workspace_id |
| Application-layer ABAC enforcement | ❌ Not implemented | See ADR-006 |
| Global knowledge tables (tenant_id IS NULL) | ⚠️ `knowledge_folklore` etc. exist but tenant_id not consistently null | **Gap**: Global vs. tenant-scoped not consistently enforced |
| Row-Level Security (RLS) in PostgreSQL | ❌ Not implemented | **Missing**: No RLS policies |
| Tenant context propagation through events | ❌ Not implemented (events not implemented) | — |
| Tenant onboarding and deletion workflow | ⚠️ `TenantController` has basic CRUD | **Gap**: No soft-delete workflow, no retention policy |
| Workspace-level isolation | ⚠️ Workshop model exists in TenantController | **Gap**: Workspace membership model not fully implemented |

**Actions Required:**
- Add `tenant_id` and `workspace_id` to all business tables that don't have them
- Implement `TenantContext` and `TenantContextHolder` (ThreadLocal)
- Implement automatic tenant filtering in repository base classes
- Add PostgreSQL RLS policies
- Implement tenant context propagation in event metadata
- Implement global knowledge contribution workflow
- Implement workspace membership model

---

### ADR-006: ABAC Authorization Model

**Status:** ⚠️ PARTIALLY IMPLEMENTED — RBAC FOUNDATION EXISTS

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| RBAC defines base permissions | ✅ `Role.java`, `Permission.java`, `RoleController`, `PermissionController` exist | No gap |
| ABAC extends RBAC with attribute conditions | ❌ No ABAC policy engine | **Critical missing**: No `AbacPolicyEngine`, no `identity_abac_policies` table |
| Policy evaluation engine | ❌ Not implemented | **Missing**: No `AuthorizationPolicyEngine` |
| UserContext and ResourceContext | ❌ Not implemented | **Missing**: No context objects for authorization |
| 4-layer enforcement (gateway, filter, service, DB) | ❌ Not implemented | **Missing**: No `AuthorizationFilter`, no `@AuthorizationRequired` annotation |
| Permission caching | ❌ Not implemented | **Missing**: No caching strategy for permissions |
| Audit logging for authorization decisions | ❌ Not implemented | **Missing**: No `audit_authorization` table |
| Role-Permission mapping | ⚠️ Tables exist but no explicit `identity_role_permissions` join table | **Gap**: Role-permission mapping not enforceable |

**Actions Required:**
- Implement `identity_abac_policies` table with JSONB conditions
- Implement `AuthorizationPolicyEngine` with RBAC + ABAC evaluation
- Implement `UserContext` and `ResourceContext` classes
- Implement `@AuthorizationRequired` annotation and AOP aspect
- Implement `AuthorizationFilter` for request-level checks
- Implement permission caching
- Implement `AuthorizationAuditLog` table
- Implement `identity_role_permissions` join table
- Add ArchUnit tests verifying `@AuthorizationRequired` on all `@RequestMapping` methods

---

### ADR-007: Canonical Story Core Contract

**Status:** ⚠️ OUT OF SCOPE FOR BACKEND (handled by AI Platform)

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Canonical Story JSON is the platform contract | ✅ Specification exists in `docs/ai-platform/canonical-story-specification.md` | No backend action needed |
| Schema validation at every stage | ❌ Not implemented (AI Platform responsibility) | No backend action needed |
| Downstream consumers extract, not translate | ⚠️ Backend services consume Canonical Story from PostgreSQL | Backend must validate Canonical Story JSONB before processing |
| Immutable Canonical Story versions | ⚠️ Content-service has `Story.java` with `@Version` for optimistic locking only | Need proper version tables per ADR-008 |
| Direct field mapping to downstream storage | ⚠️ Content-service `Story.java` maps to `content.stories` table | Partially implemented |

**Actions Required:**
- Add JSON Schema validation for Canonical Story JSONB when reading from database
- Add `CHECK` constraint on `ai_output_canonical_stories` for schema validation
- Implement version-aware Canonical Story reading (respect `version` field)

---

### ADR-008: Immutable Versioning

**Status:** ❌ NOT IMPLEMENTED

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Aggregate root + version rows pattern | ❌ Current `@Version` is optimistic locking, not versioning | **Critical missing**: No version tables |
| Creating a new version is INSERT only | ❌ Current approach UPDATEs the same row | **Critical gap**: Content is overwritten, not appended |
| Reading the latest version via `current_version_id` | ❌ Not implemented | **Missing**: No root → version pointer pattern |
| Rollback creates a new version | ❌ Not implemented | **Missing**: No rollback mechanism |
| References point to aggregate root, not version ID | ⚠️ Foreign keys reference entity ID (correct for root) | Partially correct — root IDs exist but root table doesn't have `current_version_id` |
| Status on aggregate root, not on versions | ❌ Status field exists on single entity table | Will work once root/version split is done |
| Version change types | ❌ Not implemented | **Missing**: No `change_type` field |
| Storage management (archiving) | ❌ Not implemented | **Missing**: No archiving strategy |

**Actions Required:**
- Split each versioned entity into two tables:
  - `content_stories` (root) + `content_story_versions` (versions)
  - `knowledge_objects` (root) + `knowledge_object_versions` (versions)
  - `knowledge_claims` (root) + `knowledge_claim_versions` (versions)
  - `content_articles` (root) + `content_article_versions` (versions)
- Add `current_version_id` to root tables
- Add `version_number`, `previous_version_id`, `change_type`, `change_reason` to version tables
- Update all foreign key references to point to aggregate root
- Implement `createNewVersion()` service methods
- Implement `rollbackToVersion()` service methods
- Implement archiving stored procedure for old versions
- Update API to return latest version by default with `?version=X` parameter

---

### ADR-009: AI Provider Abstraction

**Status:** ✅ OUT OF SCOPE FOR BACKEND (handled by AI Platform/Python)

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Business logic never directly calls providers | ✅ Backend doesn't call AI providers | No backend action needed |
| Provider interface and adapters | ✅ Implemented in Python AI Platform | No backend action needed |
| Provider factory with failover | ✅ Implemented in Python AI Platform | No backend action needed |

---

### ADR-010: Prompt Registry Governance

**Status:** ✅ OUT OF SCOPE FOR BACKEND (handled by AI Platform/Python)

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Prompt registry with versioning | ✅ Specification exists | No backend action needed |
| Golden dataset testing | ✅ Specification exists | No backend action needed |
| Phased rollout strategy | ✅ Specification exists | No backend action needed |

---

### ADR-011: Knowledge Graph Projection

**Status:** ✅ OUT OF SCOPE FOR BACKEND (handled by Python projection workers)

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Neo4j is a read-only projection | ✅ No Neo4j dependencies in services | No backend action needed |
| Graph projection worker | ✅ Python worker (outside `services/`) | No backend action needed |
| Event-driven incremental updates | ⚠️ Backend must publish events for projection | See ADR-003 (events not implemented) |

**Actions Required:**
- Once events are implemented (ADR-003), ensure backend publishes `StoryPublished`, `ReviewApproved` events

---

### ADR-012: Vector Search Architecture

**Status:** ✅ OUT OF SCOPE FOR BACKEND (handled by Python embedding service)

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Weaviate is a read-only vector projection | ✅ No Weaviate dependencies in services | No backend action needed |
| Embedding service generates vectors | ✅ Python service (outside `services/`) | No backend action needed |
| Event-driven embedding generation | ⚠️ Backend must publish events for embedding | See ADR-003 (events not implemented) |

---

### ADR-013: Human Review Required

**Status:** ⚠️ PARTIALLY IMPLEMENTED

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| AI outputs start in `REVIEW_REQUIRED` state | ⚠️ Workflow service exists but review state machine not fully implemented | **Gap**: No review state machine in Java services |
| Review state machine | ⚠️ `ApprovalState.java` exists, but full state machine not implemented | **Gap**: States exist but transitions are not enforced |
| Dual review tracks (Editor + Reviewer) | ✅ RBAC has EDITOR and REVIEWER roles | No gap |
| Review queue management | ❌ `workflow_review_tasks` table not present in codebase | **Missing**: No review queue |
| Review UI renders structured content | ❌ Frontend apps exist (`apps/web-admin/`) but content is placeholder (`a.txt` only) | **Gap**: No review UI implemented |
| Rejection and reprocessing flow | ❌ Not implemented | **Missing**: No `handle_review_rejected` logic |
| Projection gate (unreviewed never projected) | ✅ Enforced in Python projection workers (ADR-011, ADR-012) | No backend action needed |
| Reviewer assignment and workload management | ❌ Not implemented | **Missing**: No assignment strategy |
| Review SLA and escalation | ❌ Not implemented | **Missing**: No SLA monitoring |
| Audit trail for review decisions | ⚠️ `workflow-service` has `Approval.java`, `Moderation.java` | **Gap**: Audit trail exists but not comprehensive |

**Actions Required:**
- Implement `workflow_review_tasks` table
- Implement review state machine with proper transition enforcement
- Implement `ReviewQueueManager`
- Implement reviewer assignment strategy
- Implement SLA monitoring and escalation
- Implement `workflow_review_audit_log` table
- Build review UI in web-admin app

---

### ADR-014: Provenance First Architecture

**Status:** ⚠️ PARTIALLY IMPLEMENTED

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Five-level provenance chain | ⚠️ Lineage entity exists (`Lineage.java`) but only tracks cross-entity relationships | **Gap**: No structured five-level chain |
| Provenance is structural, not optional | ⚠️ Canonical Story has provenance (AI Platform) but backend doesn't enforce | **Gap**: Backend doesn't validate provenance |
| Generation method declaration | ❌ `generation_method` enum/column not on Java entities | **Missing**: No AI vs human distinction |
| Lineage table for cross-entity relationships | ⚠️ `lineage` table exists in identity schema | **Gap**: Limited relationship types, not integrated with content tables |
| AI extraction metadata at every level | ❌ `ai_generation_metadata` table not in Java services | **Missing**: No AI metadata tracking in backend |
| Contradiction preservation with dual provenance | ⚠️ `knowledge_contradictions` referenced but not in Java entities | **Gap**: Contradiction model not implemented in services |
| Immutable source material | ❌ `content_sources` table may not have immutability enforcement | **Gap**: No DELETE prevention triggers |
| Research citation support | ❌ Not implemented | **Missing**: No citation API |
| Provenance in projections | ✅ Neo4j/Weaviate carry provenance (Python workers) | No backend action needed |
| Provenance Query API | ❌ Not implemented | **Missing**: No provenance API endpoint |

**Actions Required:**
- Add `generation_method` ENUM column to all content entities
- Implement `ai_generation_metadata` table
- Enhance `provenance_lineage` table with comprehensive relationship types
- Add PostgreSQL triggers to prevent DELETE on `content_sources`
- Implement provenance API endpoints (`GET /api/v1/provenance/...`)
- Implement citation generator
- Add provenance validation in content services

---

### ADR-015: AI Cost Governance

**Status:** ⚠️ OUT OF SCOPE FOR BACKEND (handled by Python AI Platform, but backend should report costs)

| Requirement | Current State | Gap |
|-------------|--------------|-----|
| Every AI call is tracked | ✅ `ai_cost_log` table exists (created by AI Platform) | No backend action needed |
| Cost attribution per tenant/workspace | ✅ Cost logs include tenant_id/workspace_id | No backend action needed |
| Cost per story | ✅ pipeline_run_id links costs | No backend action needed |
| Provider comparison | ✅ ai_cost_log records provider/model | No backend action needed |
| Budget limits | ❌ `cost_budgets` table not present in Java services | **Missing**: Budget table and enforcement in backend |
| Real-time cost visibility | ❌ No cost dashboard endpoints | **Gap**: Backend should expose cost metrics API |
| Cost anomaly detection | ❌ Not implemented in backend | **Gap**: Backend should expose cost data for monitoring |

**Actions Required:**
- Implement `cost_budgets` table (if not already in database migrations)
- Add cost analytics API endpoints for dashboard consumption
- Add cost-related health check endpoints

---

## 3. Consolidated Action Plan

### Phase 1: Immediate (Critical Path)

| Priority | ADR | Action | Effort |
|----------|-----|--------|--------|
| 🔴 Critical | 002 | Consolidate 7 services into modular monolith (single JAR) | 2–3 weeks |
| 🔴 Critical | 003 | Implement Redpanda/event infrastructure (outbox + publisher) | 2–3 weeks |
| 🔴 Critical | 008 | Implement immutable versioning (root + version tables) | 2–3 weeks |
| 🔴 Critical | 006 | Implement ABAC policy engine and authorization | 2–3 weeks |

### Phase 2: Important (Core Functionality)

| Priority | ADR | Action | Effort |
|----------|-----|--------|--------|
| 🟡 High | 005 | Add tenant_id/workspace_id to all entities + TenantContext | 1–2 weeks |
| 🟡 High | 013 | Implement review state machine + review queue | 1–2 weeks |
| 🟡 High | 014 | Add generation_method + provenance lineage enhancements | 1–2 weeks |
| 🟡 High | 001 | Implement transactional outbox (covered by ADR-003) | — |

### Phase 3: Enhancement (Quality of Life)

| Priority | ADR | Action | Effort |
|----------|-----|--------|--------|
| 🟢 Medium | 005 | Implement RLS policies in PostgreSQL | 3–5 days |
| 🟢 Medium | 005 | Implement workspace membership model | 3–5 days |
| 🟢 Medium | 013 | Build review UI in web-admin | 2–3 weeks |
| 🟢 Medium | 014 | Implement provenance API + citation generator | 1–2 weeks |
| 🟢 Medium | 015 | Implement cost budget API + dashboard endpoints | 3–5 days |

### Phase 4: Future (Post-MVP)

| Priority | ADR | Action | Effort |
|----------|-----|--------|--------|
| ⚪ Low | 005 | Implement global knowledge contribution workflow | 1 week |
| ⚪ Low | 013 | Implement reviewer assignment optimization | 1 week |
| ⚪ Low | 014 | Implement PROV-O alignment for interoperability | 1 week |
| ⚪ Low | 008 | Implement version archiving and compaction | 3–5 days |

---

## 4. Summary

| ADR | Title | Status | Backend Gaps |
|-----|-------|--------|-------------|
| 001 | PostgreSQL as Source of Truth | ⚠️ Partial | Transactional outbox missing |
| 002 | Modular Monolith First | ❌ Not implemented | **7 separate services → merge into 1** |
| 003 | Event-Driven Architecture | ❌ Not implemented | No Redpanda, no outbox, no events |
| 004 | Queue-Driven AI Platform | ⚠️ Partial | Event publishing/consuming missing |
| 005 | Multi-Tenant Architecture | ⚠️ Partial | tenant_id gaps, no RLS, no TenantContext |
| 006 | ABAC Authorization Model | ⚠️ Partial | RBAC exists, ABAC engine missing |
| 007 | Canonical Story Core Contract | ⚠️ N/A (AI Platform) | Backend should validate JSONB |
| 008 | Immutable Versioning | ❌ Not implemented | Root + version tables missing |
| 009 | AI Provider Abstraction | ✅ N/A (AI Platform) | No backend action |
| 010 | Prompt Registry Governance | ✅ N/A (AI Platform) | No backend action |
| 011 | Knowledge Graph Projection | ✅ N/A (Python workers) | Must publish events once implemented |
| 012 | Vector Search Architecture | ✅ N/A (Python workers) | Must publish events once implemented |
| 013 | Human Review Required | ⚠️ Partial | Review queue, state machine, SLA missing |
| 014 | Provenance First Architecture | ⚠️ Partial | generation_method, provenance API missing |
| 015 | AI Cost Governance | ⚠️ Partial | Budget API, cost metrics missing |

### Key Metrics

- **ADRs fully implemented:** 0 (0%)
- **ADRs partially implemented:** 8 (53%)
- **ADRs not implemented (backend critical):** 3 (20%) — ADR-002, ADR-003, ADR-008
- **ADRs not applicable to backend:** 4 (27%) — ADR-007, ADR-009, ADR-010, ADR-011, ADR-012

### Biggest Risks

1. **Modular monolith not implemented (ADR-002)**: The current microservices architecture creates 7× operational overhead for a small team. Deployment complexity, debugging difficulty, and infrastructure cost are all higher than necessary at the current scale.

2. **No event infrastructure (ADR-003)**: Without Redpanda and the transactional outbox, the platform cannot implement event-driven AI processing, event replay, consumer isolation, or reliable projection synchronization.

3. **No immutable versioning (ADR-008)**: Content is currently overwritten on update. This breaks the PRD requirement ("Updates create new versions. Never overwrite."), eliminates audit trail for content changes, and makes rollback impossible.