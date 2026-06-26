# ADR-002: Modular Monolith First

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture is a greenfield platform with an expected initial user base of 100–5,000 active users. The platform must deliver Phase 1 capabilities (user management, source management, transcript import, story management, knowledge extraction, narrative and knowledge articles) within a constrained timeline and with a small engineering team.

The platform serves multiple user types (Readers, Researchers, Editors, Reviewers, Creators, Tenant Admins, System Admins) across multiple functional domains (Identity, Source, Story, Knowledge, Article, Research, Workflow). Each domain has distinct responsibilities but shares a common database (PostgreSQL), event backbone (Redpanda), and deployment infrastructure.

## Technical Context

The platform stack includes Spring Boot 4, Java 25, PostgreSQL 18, Neo4j 5.26, Weaviate 1.37, Python 3.14, Redpanda, React, and Next.js. The architecture principles mandate event-driven communication, queue-driven AI processing, PostgreSQL as source of truth, multi-tenancy, ABAC, immutable versioning, human review, and provenance-first design.

The current codebase already reflects a service-per-domain structure:

```
services/
├── content-service/      # Source, Story, Article domains
├── identity-service/     # Identity, RBAC, ABAC, Audit domains
├── knowledge-service/    # Knowledge, Claims, Folklore, Beliefs, Traditions domains
├── research-service/     # Collections, Annotations, Notes, Exports domains
├── workflow-service/     # Approval, Publishing, Moderation domains
├── gateway-services/     # API Gateway / Edge routing
├── shared-events/        # Shared event definitions
└── shared-web/           # Shared web utilities
```

Each service is structured using Domain-Driven Design modules:

```
knowledge-service/
├── knowledge/     # api/, application/, domain/, infrastructure/
├── claims/        # api/, application/, domain/, infrastructure/
├── folklore/      # api/, application/, domain/, infrastructure/
├── beliefs/       # api/, application/, domain/, infrastructure/
├── traditions/    # api/, application/, domain/, infrastructure/
├── contradictions/# api/, application/, domain/, infrastructure/
├── motifs/        # api/, application/, domain/, infrastructure/
└── themes/        # api/, application/, domain/, infrastructure/
```

## Constraints

1. **Team size**: The engineering team is small (estimated 3–8 engineers). Maintaining 7+ independent microservices operationally would consume 30–50% of engineering capacity in deployment pipelines, service mesh configuration, distributed tracing, and cross-service debugging.

2. **Delivery timeline**: Phase 1 must deliver 7 functional domains. Microservices would require establishing inter-service communication contracts, API versioning, service discovery, and distributed testing infrastructure before any business logic can be built.

3. **Operational maturity**: The organization does not yet have established DevOps practices for managing a microservices ecosystem. Kubernetes, service meshes, and container orchestration expertise is limited.

4. **Scale**: 100–5,000 active users does not produce the traffic patterns that justify independent service scaling. A single monolith with adequate resources can handle this load comfortably.

5. **AI Platform separation**: The AI Platform (Python-based workers) is already architecturally separated via Redpanda. This is not a microservices decision — it is a technology-driven separation (Java vs. Python, synchronous vs. asynchronous, user-facing vs. internal processing).

6. **Future extraction**: The architecture must not prevent future extraction into microservices. Module boundaries must be clean enough that extraction is a deployment change, not a rewrite.

## Problem Statement

Should the platform be built as a set of independent microservices from the start, or as a modular monolith with well-defined module boundaries that can be extracted into microservices later? How do we balance the long-term benefits of microservices against the short-term delivery and operational costs, given the current team size, expected scale, and delivery timeline?

# Decision

**Use Modular Monolith architecture for all Java/Spring Boot backend services.**

**Do not deploy services as independent microservices initially.**

**All domain services (identity, content, knowledge, research, workflow) are deployed as a single application unit.**

**The API gateway remains a separate deployment for edge routing and cross-cutting concerns.**

**The AI Platform (Python workers) remains architecturally separate via Redpanda — this is not a monolith decision, it is a technology boundary.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Single Deployment Unit                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  API Gateway (Separate)                   │    │
│  │  - Routing                                                │    │
│  │  - Rate Limiting                                          │    │
│  │  - Authentication verification                            │    │
│  │  - Request transformation                                 │    │
│  └───────────────────────┬─────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Modular Monolith (Single JAR)               │    │
│  │                                                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │    │
│  │  │ Identity │  │ Content  │  │Knowledge │  │Research│  │    │
│  │  │ Module   │  │ Module   │  │ Module   │  │ Module │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │    │
│  │                                                          │    │
│  │  ┌──────────┐  ┌────────────────────────────────────┐   │    │
│  │  │ Workflow │  │ Shared Kernel                       │   │    │
│  │  │ Module   │  │ - Events                            │   │    │
│  │  └──────────┘  │ - Web filters                       │   │    │
│  │                │ - Security context                   │   │    │
│  │                │ - Base entities                      │   │    │
│  │                └────────────────────────────────────┘   │    │
│  └───────────────────────┬─────────────────────────────────┘    │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    PostgreSQL 18                          │    │
│  │              (Single Database, Shared Schema)             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Redpanda                               │    │
│  │         (Event Backbone — shared in-process producer)     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              AI Platform (Separate Deployment)            │    │
│  │  - Python workers (extraction, normalization,            │    │
│  │    validation, article generation, embedding)            │    │
│  │  - Communicates only via Redpanda                        │    │
│  │  - Writes results to PostgreSQL                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Single Deployment Artifact

All Java domain services are compiled into a single JAR file and deployed as one process. The Maven reactor build produces one deployable artifact:

```
living-atlas-backend.jar
├── id.livingatlas.identityservice.*
├── id.livingatlas.contentservice.*
├── id.livingatlas.knowledgeservice.*
├── id.livingatlas.researchservice.*
├── id.livingatlas.workflowservice.*
├── id.livingatlas.sharedevents.*
└── id.livingatlas.sharedweb.*
```

Each domain module retains its own package structure, Spring context, and database migration files. Module isolation is enforced at the code level, not the process level.

### Rule 2: Module Isolation via Package Structure

Modules communicate only through their Application layers. Direct domain-to-domain or infrastructure-to-domain access across modules is forbidden.

Allowed inter-module communication:
- **Application Service → Application Service**: Via injected service interfaces
- **Application Service → Domain Event**: Via Spring ApplicationEventPublisher (in-process) or Redpanda (async)
- **REST Controller → Application Service**: Standard controller-service pattern within the same module

Forbidden inter-module communication:
- **Domain → Domain**: No direct entity references across modules
- **Infrastructure → Domain**: No cross-module repository access
- **API → Infrastructure**: Controllers must go through Application layer

### Rule 3: Shared Kernel Is Minimal and Stable

The shared kernel contains only:
- Base event types and serialization
- Web security filters and tenant context resolution
- Common exception types
- Base entity audit fields (created_at, created_by, etc.)

The shared kernel must not contain:
- Business logic
- Domain entities
- Service implementations
- Database access

### Rule 4: Database Schema Is Unified but Namespaced

All domain modules share a single PostgreSQL database. Schema organization:

```sql
-- Identity domain tables use identity_ prefix
identity_users
identity_roles
identity_tenants

-- Content domain tables use content_ prefix
content_sources
content_stories
content_transcripts

-- Knowledge domain tables use knowledge_ prefix
knowledge_objects
knowledge_claims
knowledge_folklore

-- Research domain tables use research_ prefix
research_collections
research_annotations

-- Workflow domain tables use workflow_ prefix
workflow_approvals
workflow_publications
```

Flyway migrations are ordered globally (V1, V2, V3...) but each migration file is scoped to a single domain. This prevents migration conflicts while maintaining a single migration sequence.

### Rule 5: In-Process Events for Synchronous Flows, Redpanda for Async

Synchronous cross-module flows (e.g., "create user → assign default role") use Spring's `ApplicationEventPublisher` for in-process event propagation. This avoids the latency and complexity of Redpanda for operations that must complete within the same HTTP request.

Asynchronous flows (e.g., "story created → trigger AI extraction") use Redpanda. The transactional outbox pattern ensures reliable publication.

When a module is extracted to a microservice later, in-process events are replaced with Redpanda events. The event contract remains the same — only the transport changes.

### Rule 6: API Gateway Remains Separate

The gateway service (`gateway-services/`) is deployed as a separate process. Rationale:
- Edge routing, rate limiting, and authentication verification are cross-cutting concerns that benefit from isolation
- A gateway failure should not crash the backend
- The gateway can be scaled independently if traffic patterns require it
- The gateway provides a clean API boundary for frontend applications

### Rule 7: AI Platform Remains Separate

The AI Platform (Python workers) is deployed independently. This is not a microservices decision — it is a technology boundary:
- Java backend and Python AI workers have different runtime requirements
- AI workers are not user-facing and have different scaling characteristics
- Communication is exclusively through Redpanda (no REST)
- AI workers can be deployed, scaled, and updated independently

# Alternatives Considered

## Alternative 1: Full Microservices from Day One

**Description**: Deploy each domain service (identity, content, knowledge, research, workflow) as an independent microservice with its own deployment pipeline, database schema (or database instance), and API versioning. Services communicate via REST/gRPC and Redpanda events.

**Advantages**:
- Independent scaling per service (e.g., knowledge-service may need more resources than research-service)
- Independent deployment cycles — a bug in content-service does not block identity-service releases
- Technology flexibility — each service could theoretically use a different stack
- Team ownership boundaries are physically enforced — no accidental cross-module coupling
- Aligns with industry trend toward microservices

**Disadvantages**:
- **Operational overhead is prohibitive for a small team**: 7 services × (CI/CD pipeline, Docker image, health checks, logging configuration, monitoring dashboards, secret management) = 7× operational surface area. A team of 3–8 engineers would spend 30–50% of capacity on infrastructure.
- **Distributed development complexity**: Every local development environment requires running 7 services plus PostgreSQL, Redpanda, Neo4j, and Weaviate. Docker Compose orchestration becomes a significant maintenance burden.
- **Cross-service transactions are impossible**: A "create story with initial knowledge extraction" flow spans content-service and knowledge-service. Without distributed transactions, this requires saga patterns, compensating transactions, and eventual consistency handling — all before any business logic is built.
- **API contract churn**: In early development, domain boundaries are not fully understood. Microservices force API versioning and contract negotiation for every change, slowing iteration velocity.
- **Debugging complexity**: A single user request may traverse gateway → identity → content → knowledge → workflow. Distributed tracing must be in place from day one, adding OpenTelemetry configuration overhead before any feature ships.
- **Network latency**: Every cross-service call adds network round-trip time. At 100–5,000 users, this latency is pure overhead with no benefit.
- **Database-per-service increases complexity**: Each service would need its own Flyway migration sequence, connection pool, and backup strategy. Cross-service queries require federation or application-level joins.

**Rejection rationale**: Microservices solve organizational and scaling problems that do not yet exist. The operational cost of 7 microservices for a small team at 100–5,000 users is unjustified. The modular monolith provides the same architectural benefits (module isolation, clear boundaries) without the operational tax.

## Alternative 2: Monolith Without Modular Boundaries

**Description**: Build a traditional monolithic application where all code lives in a single package structure without enforced module boundaries. No DDD modules, no package-level isolation, no inter-module communication rules.

**Advantages**:
- Fastest initial development velocity — no architectural ceremony
- Simplest possible code navigation — everything is accessible
- No module boundary enforcement overhead
- Easiest onboarding for new developers

**Disadvantages**:
- **Extraction becomes a rewrite**: Without clear module boundaries, extracting a domain into a microservice requires untangling dependencies, extracting entities, and rearchitecting the code. This is significantly more expensive than extracting from a modular monolith.
- **No architectural guardrails**: As the codebase grows, cross-domain dependencies proliferate. The knowledge module directly accesses story entities. The workflow module directly modifies knowledge state. Over 2–3 years, the codebase becomes a "big ball of mud" where no single person understands the full dependency graph.
- **Team coordination overhead**: Without module boundaries, multiple developers working on different domains frequently conflict on the same files. Merge conflicts become a daily occurrence.
- **Testing becomes harder**: Without module boundaries, unit tests cannot easily mock cross-domain dependencies. Tests become integration tests by default, slowing the test suite.
- **No clear ownership**: When a bug occurs in a cross-domain interaction, there is no clear owner. The identity team and content team both touch the same code paths.

**Rejection rationale**: This approach optimizes for the first 3 months at the expense of the next 3 years. The platform has clearly defined bounded contexts (Identity, Source, Story, Knowledge, Article, Research, Workflow). Not enforcing these boundaries in code would create technical debt that makes future extraction prohibitively expensive. The modular monolith provides the same development speed with the added benefit of extraction-ready boundaries.

## Alternative 3: Microservices with Shared Library

**Description**: Deploy microservices but extract all shared logic (entities, events, base classes) into a shared library published as a Maven artifact. Services communicate via Redpanda events only — no synchronous REST/gRPC calls between services.

**Advantages**:
- Event-driven communication eliminates synchronous coupling
- Shared library ensures consistent event schemas and base types
- Services can be developed and deployed independently
- No distributed transaction problem (all communication is async)
- Aligns with the existing event-driven architecture principle

**Disadvantages**:
- **Shared library creates hidden coupling**: Changes to shared entities require coordinated releases across all services. A new field on `BaseEntity` forces recompilation and redeployment of all services.
- **Event-only communication is insufficient for many flows**: User authentication, authorization checks, and tenant resolution are synchronous by nature. Making these asynchronous would require significant architectural gymnastics (e.g., caching auth tokens locally, accepting stale authorization data).
- **Operational overhead remains high**: 7 services still means 7 deployment pipelines, 7 sets of monitoring, 7 health check endpoints, 7 log streams. The shared library does not reduce operational complexity.
- **Local development still requires multi-service orchestration**: Even with event-only communication, developers must run all services to test cross-domain flows.
- **Event schema evolution is complex**: Adding a field to an event requires updating the shared library, publishing a new version, updating all consumers, and coordinating deployment. In a monolith, this is a single code change.
- **Debugging async flows is harder**: Event-driven debugging requires tracing messages through Redpanda, checking consumer offsets, and inspecting dead letter queues. This is significantly more complex than debugging a synchronous call chain in a monolith.

**Rejection rationale**: While event-only communication reduces coupling compared to REST/gRPC microservices, it does not reduce operational complexity. The shared library introduces its own coupling and coordination problems. The modular monolith provides the same event-driven architecture benefits without the operational overhead.

## Alternative 4: Strangler Fig with Initial Monolith

**Description**: Start with a modular monolith but immediately build a strangler fig layer that routes requests to either the monolith or future microservices. Deploy the monolith behind a routing layer that can redirect specific API paths to extracted services as they are built.

**Advantages**:
- Extraction path is prepared from day one — no routing infrastructure changes needed later
- Individual endpoints can be extracted incrementally without affecting the rest of the system
- Provides a clear migration strategy that is visible to the entire team
- Forces early thinking about API contracts and service boundaries

**Disadvantages**:
- **Premature infrastructure complexity**: Building a strangler fig layer before any extraction is needed adds routing configuration, service discovery integration, and request forwarding logic that provides no value until the first extraction.
- **Routing layer becomes a maintenance burden**: The strangler fig must be kept in sync with the monolith's API surface. Every new endpoint requires routing configuration. This overhead is incurred for every feature, not just extracted ones.
- **False sense of extraction readiness**: Having a strangler fig does not mean the code is extraction-ready. Module boundaries may still be leaky. The routing layer only handles HTTP traffic — it does not address database coupling, event coupling, or shared code dependencies.
- **Increased deployment complexity**: The monolith and strangler fig must be deployed and configured together. This adds another moving part to every deployment.

**Rejection rationale**: The strangler fig pattern is valuable when extracting from an existing monolith that cannot be rewritten. For a greenfield platform, it is premature optimization. The modular monolith's clean module boundaries provide a better extraction path without the operational overhead of a strangler fig layer. The strangler fig can be introduced at extraction time, not before.

# Consequences

## Positive

1. **Rapid development velocity**: A single JAR means compile → test → package → deploy in minutes. No cross-service contract negotiation, no API versioning ceremony, no distributed deployment coordination. Features can be delivered in days instead of weeks.

2. **Simplified local development**: Developers run one Spring Boot application (plus PostgreSQL, Redpanda, Neo4j, Weaviate via Docker Compose). No need to start 7 services, configure service discovery, or manage inter-service authentication. Onboarding a new developer takes hours, not days.

3. **Atomic database migrations**: Flyway migrations run in a single sequence. There is no risk of migration ordering conflicts across services. A migration that adds a column to `stories` and a related column to `knowledge_objects` can be in the same migration file, ensuring consistency.

4. **In-process transactions**: Cross-domain operations (e.g., "create story → assign to workspace → emit event") execute within a single Spring transaction. No distributed transaction coordination, no saga patterns, no compensating events. This dramatically simplifies the initial implementation of complex workflows.

5. **Simplified debugging and observability**: A single application produces one log stream, one set of metrics, one trace. Distributed tracing is unnecessary — a single thread trace covers the entire request. Debugging a cross-domain flow means stepping through code in one IDE session, not correlating logs across 7 services.

6. **Lower infrastructure cost**: One JVM, one connection pool to PostgreSQL, one set of health check endpoints. At 100–5,000 users, the infrastructure cost is a fraction of what 7 microservices would require.

7. **Clear module boundaries established early**: DDD module structure is enforced from day one. When extraction becomes necessary, the boundaries are already defined, tested, and proven. Extraction becomes a deployment change, not a rewrite.

8. **Simplified deployment pipeline**: One CI/CD pipeline builds, tests, and deploys the monolith. No need for coordinated multi-service releases, canary deployments across services, or rollback coordination.

## Negative

1. **Single point of deployment risk**: A bug in any module can take down the entire application. There is no fault isolation between domains. A memory leak in the knowledge module affects identity module availability.

2. **No independent scaling**: All modules share the same JVM resources. If the knowledge module requires more memory for graph processing, the entire monolith must be scaled up. Modules with different resource profiles (CPU-intensive vs. memory-intensive vs. I/O-bound) cannot be scaled independently.

3. **Build time grows with codebase size**: As the codebase grows, compilation and test execution times increase. At the target scale of 100,000 stories, the monolith may take 15–30 minutes to build, impacting developer iteration speed.

4. **Module boundary discipline is required**: Without physical process boundaries, developers must exercise discipline to maintain module isolation. Code reviews must enforce boundary rules. Over time, entropy can erode module boundaries if not actively maintained.

5. **Single technology constraint**: All modules must use the same Java version, Spring Boot version, and library versions. A module that needs a newer library version must wait for the entire monolith to upgrade. This can slow down innovation in specific domains.

6. **Deployment coupling**: All modules are deployed together. A critical fix in one module requires deploying all modules, even if the other modules have no changes. This increases the blast radius of every deployment.

7. **Team coordination overhead grows**: As the team grows beyond 5–8 engineers, coordinating changes across modules in a single codebase becomes challenging. Merge conflicts, shared code changes, and release coordination become bottlenecks.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Development velocity** | Fast initial delivery, no contract negotiation | Slower builds as codebase grows |
| **Operational simplicity** | One JVM, one pipeline, one log stream | No fault isolation between modules |
| **Scaling** | Simple vertical scaling | No independent horizontal scaling |
| **Module boundaries** | Enforced in code, extraction-ready | Requires ongoing discipline to maintain |
| **Deployment risk** | Single deployment, simple rollback | Single point of failure, full deployment for any change |
| **Team scalability** | Works well for 3–8 engineers | Becomes bottleneck beyond 8–10 engineers |
| **Technology flexibility** | Unified dependency management | Cannot upgrade modules independently |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Module boundary erosion over time** | High | High — extraction becomes impossible without rewrite | Enforce boundary rules in CI (ArchUnit tests). Conduct quarterly architecture reviews. Use package dependency analysis tools (e.g., JDepend, ArchUnit) to detect violations automatically. |
| **Build time becomes prohibitive** | Medium | Medium — developer productivity degrades | Implement incremental compilation. Split test execution into unit (fast) and integration (slow) suites. Consider Gradle module parallelism. If build exceeds 15 minutes, evaluate extraction of the largest module. |
| **Single JVM resource contention** | Medium | Medium — one module's memory leak affects all | Set per-module resource limits via thread pool isolation, connection pool separation, and circuit breakers. Monitor per-module resource consumption. Use Spring's `@Async` with separate thread pools per domain. |
| **Database connection pool exhaustion** | Medium | High — one module's slow queries starve others | Use separate HikariCP connection pools per domain module. Set query timeout limits. Implement database statement-level monitoring. |
| **Classpath conflicts from shared dependencies** | Low | Medium — library version conflicts | Use Maven dependency management to enforce consistent versions. Run `mvn dependency:tree` in CI to detect conflicts. Keep shared kernel dependencies minimal. |
| **Flyway migration conflicts** | Low | Medium — two modules add migrations with same version | Use domain-prefixed migration names (e.g., `V1_1__identity_users.sql`, `V1_2__content_sources.sql`). Enforce migration review process. Run migration validation in CI. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Full deployment for every change** | High | Medium — increased blast radius | Implement canary deployment for the monolith. Use feature flags to gate new functionality. Maintain rollback scripts for database migrations. |
| **No fault isolation between modules** | Medium | High — one module crash takes down all | Implement health check endpoints per module. Use Spring's `@CircuitBreaker` for external calls. Set per-module thread pool limits. Monitor JVM heap and thread dumps per module package. |
| **Team coordination overhead as team grows** | Medium | Medium — merge conflicts, release coordination | Establish clear module ownership. Use CODEOWNERS file for automatic review assignment. Implement branch policies per module if needed. |
| **Onboarding complexity for new engineers** | Low | Medium — understanding the full codebase is harder | Maintain architecture documentation (bounded context map, module dependency diagram). Use ADRs to document key decisions. Provide onboarding guide with module walkthrough. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Extraction is more expensive than expected** | High — delayed migration to microservices | Invest in module boundary quality from day one. Run extraction drills (simulate extracting a module) in Phase 2 to validate the approach. Document extraction patterns early. |
| **Team grows to 10+ engineers before extraction triggers are met** | Medium — coordination overhead becomes painful | Extraction triggers are not just team size. Evaluate extraction when deployment conflicts, scaling divergence, or team coordination costs exceed the operational cost of microservices. |
| **A module requires a different database technology** | Medium — monolith constraint becomes limiting | The module can be extracted to a microservice with its own database. The modular monolith structure makes this a clean extraction rather than a rewrite. |
| **Performance requirements demand independent scaling** | Low — 100–5,000 users does not require this | If a module's traffic profile diverges significantly (e.g., knowledge graph queries become 100× more frequent than identity operations), extract that module for independent scaling. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Team grows beyond 8–10 engineers**: At this point, coordination overhead in a single codebase may justify extracting one or more modules into independent microservices. Extraction should be incremental, starting with the module that has the highest change frequency or most distinct resource profile.

2. **A module requires independent scaling**: If monitoring reveals that one module has significantly different resource requirements (e.g., knowledge graph queries require 16 GB RAM while identity operations need 2 GB), extraction enables independent resource allocation.

3. **Deployment conflicts become frequent**: If the team regularly experiences deployment conflicts where changes in one module block releases for another, extraction of the conflicting module should be evaluated.

4. **Build time exceeds 20 minutes**: At this threshold, developer productivity is significantly impacted. Extraction of the largest or most frequently changed module can reduce build time.

5. **A module requires a different technology stack**: If a domain would benefit from a different runtime (e.g., a real-time collaboration module using WebSockets and a different framework), extraction enables technology flexibility.

6. **The platform reaches Phase 3 scale with 100,000+ stories and 10+ engineers**: At this scale, the operational benefits of microservices (fault isolation, independent scaling, team autonomy) may outweigh the operational costs.

## Extraction Strategy

When extraction is triggered, the following process should be followed:

### Phase 1: Preparation (2–4 weeks)

1. **Audit module boundaries**: Run ArchUnit tests to verify no illegal cross-module dependencies exist. Fix any violations.
2. **Extract database schema**: Move the module's tables to a separate database schema (or database instance). Update Flyway migrations.
3. **Replace in-process events with Redpanda events**: Identify all `ApplicationEventPublisher` usages that cross the module boundary. Replace with Redpanda events using the same event schema.
4. **Create API contract**: Define the module's public API (REST endpoints or event contracts). Document request/response schemas.
5. **Extract shared kernel dependencies**: Identify shared kernel classes used by the module. Copy or extract to a shared library.

### Phase 2: Extraction (1–2 weeks)

1. **Create new service project**: Use the existing module structure as a template. Copy the module code to a new service project.
2. **Set up CI/CD pipeline**: Create build, test, and deployment pipeline for the new service.
3. **Configure service discovery**: Register the new service in the gateway routing configuration.
4. **Deploy in parallel**: Run the monolith and the new service in parallel. Route a percentage of traffic to the new service.
5. **Validate**: Compare results between monolith and extracted service. Verify data consistency.

### Phase 3: Cutover (1 week)

1. **Route all traffic to extracted service**: Update gateway routing to send all relevant traffic to the new service.
2. **Remove module from monolith**: Delete the module code from the monolith. Update the monolith build configuration.
3. **Monitor**: Watch for errors, latency changes, and data consistency issues.
4. **Document**: Update architecture documentation and ADRs to reflect the new service boundary.

### Extraction Priority

If multiple modules need extraction, prioritize by:

1. **Resource profile divergence**: Extract modules with the most different CPU/memory/IO requirements first.
2. **Change frequency**: Extract modules with the highest change frequency to reduce deployment coupling.
3. **Team ownership**: Extract modules owned by different teams to enable independent release cycles.
4. **External dependency**: Extract modules that depend on external systems (e.g., AI Platform integration) to isolate failure domains.

# References

- **Backend Platform PRD §3.1** — "Modular Monolith First" — Product-level justification for the decision.
- **Backend Platform PRD §15** — "Internal Service Structure" — DDD module structure requirements.
- **Backend Platform PRD §18** — "Out of Scope (Current Phase)" — Microservices explicitly excluded from MVP.
- **ADR-001: PostgreSQL as Source of Truth** — Shared database with namespace-prefixed tables.
- **ADR-005: DDD Modular Structure** — Module organization and dependency rules.
- **ADR-006: Service Boundaries** — Bounded context definitions and inter-module communication contracts.
- **Simon Brown's Modular Monolith** — https://www.youtube.com/watch?v=5OjqD-ow8GE — Principles of modular monolith architecture.
- **ArchUnit** — https://www.archunit.org/ — Java library for enforcing architecture rules in tests.
- **Domain-Driven Design (Eric Evans)** — Strategic design, bounded contexts, and module boundaries.
- **Extraction Patterns** — Strangler Fig pattern for incremental migration from monolith to microservices.