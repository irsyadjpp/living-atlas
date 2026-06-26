# Implementation Plan: Backend Critical Items

Based on gap analysis and 4 ADRs (002, 003, 006, 008)

## Implementation Status

### ✅ Completed Files

#### ADR-003: Event-Driven Architecture (shared-events)

| File | Purpose |
|------|---------|
| `DomainEvent.java` | Base interface for all domain events |
| `AbstractDomainEvent.java` | Abstract base with JSON serialization |
| `EventMetadata.java` | Standard metadata (tenant, correlation, causation) |
| `OutboxEvent.java` | JPA entity for transactional outbox table |
| `OutboxEventRepository.java` | JPA repository with polling queries |
| `OutboxEventPublisher.java` | Writes events to outbox within @Transactional |
| `OutboxPollerScheduler.java` | Background scheduler (100ms interval) |
| `RedpandaEventPublisher.java` | Publishes to Redpanda (log-based for dev) |
| `ProcessedEventTracker.java` | Idempotency tracking for event handlers |
| `StoryCreatedEvent.java` | Example domain event |
| `ReviewApprovedEvent.java` | Example domain event |
| `EventTopics.java` | Central topic registry (already existed) |

#### ADR-008: Immutable Versioning (content-service)

| File | Purpose |
|------|---------|
| `StoryVersion.java` | Immutable version entity with version chain |
| `StoryVersionRepository.java` | Repository for version queries |
| `StoryNarrativeType.java` | Enum for narrative types |

#### ADR-006: ABAC Authorization (identity-service + shared-web)

| File | Purpose |
|------|---------|
| `AbacPolicyEngine.java` | Central RBAC + ABAC evaluation engine |
| `UserContext.java` | Authenticated user context object |
| `ResourceContext.java` | Resource attributes for ABAC evaluation |
| `TenantContextHolder.java` | ThreadLocal holder for request context |
| `AuthorizationRequired.java` | `@AuthorizationRequired` annotation |
| `AuthorizationAspect.java` | AOP aspect enforcing authorization |

### 🔄 Pending (Next Steps)

#### ADR-002: Modular Monolith

| Task | Status |
|------|--------|
| Create `living-atlas-backend` module | ⏳ Pending |
| Consolidate 7 services into single JAR | ⏳ Pending |
| Single Flyway migration sequence | ⏳ Pending |
| ArchUnit tests for module boundaries | ⏳ Pending |

#### ADR-003: Event-Driven (Remaining)

| Task | Status |
|------|--------|
| Flyway migration for outbox tables | ⏳ Pending |
| Spring Kafka/Redpanda producer dependency | ⏳ Pending |
| Event handler examples with idempotency | ⏳ Pending |

#### ADR-008: Immutable Versioning (Remaining)

| Task | Status |
|------|--------|
| Modify `Story.java` to be aggregate root only | ⏳ Pending |
| Add `currentVersionId` to Story entity | ⏳ Pending |
| Implement `createNewVersion()` in StoryService | ⏳ Pending |
| Implement `rollbackToVersion()` in StoryService | ⏳ Pending |
| KnowledgeObject + Claim + Article versioning | ⏳ Pending |

#### ADR-006: ABAC (Remaining)

| Task | Status |
|------|--------|
| Add `identity_abac_policies` table migration | ⏳ Pending |
| Add `identity_role_permissions` join table | ⏳ Pending |
| Add `audit_authorization` table | ⏳ Pending |
| Wire AuthorizationFilter into SecurityConfig | ⏳ Pending |
| Add ArchUnit tests for @AuthorizationRequired | ⏳ Pending |

## File Structure

```
services/
├── shared-events/src/main/java/.../sharedevents/
│   ├── DomainEvent.java                          ← NEW
│   ├── AbstractDomainEvent.java                  ← NEW
│   ├── EventMetadata.java                        ← NEW
│   ├── EventTopics.java                          ← EXISTING
│   ├── events/
│   │   ├── StoryCreatedEvent.java                ← NEW
│   │   └── ReviewApprovedEvent.java              ← NEW
│   └── outbox/
│       ├── OutboxEvent.java                      ← NEW
│       ├── OutboxEventRepository.java            ← NEW
│       ├── OutboxEventPublisher.java             ← NEW
│       ├── OutboxPollerScheduler.java            ← NEW
│       ├── RedpandaEventPublisher.java           ← NEW
│       └── ProcessedEventTracker.java            ← NEW
│
├── shared-web/src/main/java/.../sharedweb/
│   ├── annotation/
│   │   └── AuthorizationRequired.java            ← NEW
│   ├── aspect/
│   │   └── AuthorizationAspect.java              ← NEW
│   └── security/
│       ├── UserContext.java                      ← NEW
│       ├── ResourceContext.java                  ← NEW
│       └── TenantContextHolder.java              ← NEW
│
├── identity-service/.../identityservice/abac/
│   └── domain/
│       ├── AbacPolicyEngine.java                 ← NEW
│       ├── PolicyRepository.java                 ← EXISTING
│       └── model/
│           ├── Policy.java                       ← EXISTING
│           ├── PolicyRule.java                   ← EXISTING
│           └── AccessDecision.java               ← EXISTING
│
└── content-service/.../contentservice/story/domain/
    ├── Story.java                                ← MODIFY (add currentVersionId)
    ├── StoryVersion.java                         ← NEW
    ├── StoryVersionRepository.java               ← NEW
    └── StoryNarrativeType.java                   ← NEW