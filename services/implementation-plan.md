# Implementation Plan: Backend Critical Items

Based on gap analysis and 4 ADRs (002, 003, 006, 008)

## Phase 1: Modular Monolith (ADR-002)

### Step 1: Create living-atlas-backend module
```
services/
├── living-atlas-backend/          ← NEW: Single deployable module
│   ├── pom.xml                    ← Aggregates all domain modules
│   ├── src/main/java/
│   │   └── id/livingatlas/backend/
│   │       ├── LivingAtlasApplication.java  ← Main Spring Boot app
│   │       └── config/
│   │           ├── ModuleConfig.java        ← Scans all domain packages
│   │           └── FlywayConfig.java        ← Single migration sequence
│   └── src/main/resources/
│       ├── application.yaml                ← Unified config
│       └── db/migration/                    ← Single migration dir
├── pom.xml                     ← Maven reactor with single JAR packaging
└── ...existing services...
```

## Phase 2: Event-Driven Architecture (ADR-003)

### Files to create:
```
shared-events/src/main/java/id/livingatlas/sharedevents/
├── DomainEvent.java                  ← Base event interface
├── EventMetadata.java                ← Metadata (tenant, correlationId)
├── EventPublisher.java               ← Interface for publishing
├── impl/
│   ├── OutboxEventPublisher.java     ← Transactional outbox impl
│   └── OutboxPollerScheduler.java    ← Polls and publishes to Redpanda
└── events/
    ├── StoryCreatedEvent.java
    ├── StoryVersionCreatedEvent.java
    ├── ReviewApprovedEvent.java
    ├── ReviewRejectedEvent.java
    └── ...other events

Flyway migration:
    V001__create_outbox_tables.sql
```

## Phase 3: Immutable Versioning (ADR-008)

### Files to create:
```
content-service/src/main/java/.../contentservice/story/domain/
├── Story.java                    ← MODIFY: Aggregate root only
├── StoryVersion.java            ← NEW: Version entity
├── StoryRepository.java         ← MODIFY: Root repository
└── StoryVersionRepository.java  ← NEW: Version repository

content-service/src/main/java/.../contentservice/story/application/
├── CreateStoryCommand.java
├── CreateVersionCommand.java
└── StoryService.java            ← MODIFY: createNewVersion(), rollback()

knowledge-service/.../knowledge/* аналогично
```

## Phase 4: ABAC Authorization (ADR-006)

### Files to create:
```
shared-web/src/main/java/.../sharedweb/
├── security/
│   ├── UserContext.java              ← NEW: User context object
│   ├── ResourceContext.java          ← NEW: Resource context object
│   └── TenantContextHolder.java      ← EXIST: TenantContextHolder

identity-service/.../identityservice/abac/
├── api/AbacPolicyController.java     ← NEW: CRUD for ABAC policies
├── domain/
│   ├── AbacPolicyEngine.java         ← NEW: Policy evaluation logic
│   ├── AuthorizationResult.java      ← NEW: Result object
│   ├── model/
│   │   └── AbacPolicy.java           ← NEW: Policy entity
│   └── AbacPolicyRepository.java     ← NEW: JPA Repository

shared-web/src/main/java/.../sharedweb/
├── annotation/
│   └── AuthorizationRequired.java    ← NEW: @AuthorizationRequired
├── aspect/
│   └── AuthorizationAspect.java      ← NEW: AOP enforcement
└── filter/
    └── AuthorizationFilter.java       ← NEW: Request-level filter
```

## Priority Files to Create Now:

1. `OutboxEventPublisher.java` — Core of event-driven architecture
2. `DomainEvent.java` — Base event interface
3. `Story.java` (modified) + `StoryVersion.java` — Immutable versioning
4. `AbacPolicyEngine.java` — ABAC evaluation
5. `AuthorizationRequired.java` — Annotation for authorization
6. `UserContext.java` + `ResourceContext.java` — Context objects