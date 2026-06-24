# Identity-Service Implementation Plan

## Architecture Overview

The identity-service is responsible for **Identity & Access Management (IAM)** across the entire Living Atlas platform. It handles Users, Tenants, Workspaces, Role-Based Access Control (RBAC), and Attribute-Based Access Control (ABAC).

### Guiding Principles

- **Modular Monolith** — DDD bounded contexts within a single Spring Boot application
- **Event-Driven Ready** — Publish domain events for other services (gateway, content, research)
- **PostgreSQL as Source of Truth** — All state originates here; Neo4j/Weaviate are projections
- **Multi-Tenant** — Global knowledge shared, tenant-specific knowledge isolated

---

## Bounded Contexts

The identity-service is divided into 5 bounded contexts:

```
identity-service/

├── user              # auth.users — User accounts, registration, authentication
├── tenant            # tenant.tenants + tenant.workspaces — Multi-tenant management
├── rbac              # iam.roles + iam.permissions + iam.role_permissions + iam.user_roles
├── abac              # iam.policies + iam.policy_rules — Attribute-based policy engine
└── governance        # governance.audit_logs + governance.lineage — Audit & provenance
```

Each context follows the DDD layered structure:

```text
<context>/
├── api/              # REST controllers
├── application/      # Use cases, DTOs, mappers
├── domain/           # Domain models, repository interfaces, domain events
└── infrastructure/   # Repository implementations, JPA mappers
```

> **Current State:** Models have been created in a flat `model/` package. In Phase 2, these will be refactored into their respective bounded contexts.

---

## Phase 1: Foundation (Current)

### 1.1 Database Migration Setup (Flyway)

| File | Description |
|------|-------------|
| `V1__identity_schema.sql` | Create schemas: `auth`, `iam`, `tenant`, `governance` |
| `V2__identity_enums.sql` | Create custom enum types: `tenant_type`, `tenant_status`, `user_status` |
| `V3__identity_tables.sql` | Create all tables for identity contexts |
| `V4__identity_indexes.sql` | Add indexes for performance |
| `V5__identity_seed.sql` | Seed initial roles: `admin`, `researcher`, `creator`, `viewer` |

**Migration Directory:**
```
services/identity-service/src/main/resources/db/migration/
```

### 1.2 Application Configuration

**`application.yaml`** needs:

```yaml
spring:
  application:
    name: identity-service

  datasource:
    url: jdbc:postgresql://localhost:5432/living_atlas
    username: ${DB_USERNAME:livingatlas}
    password: ${DB_PASSWORD:livingatlas}

  jpa:
    hibernate:
      ddl-auto: validate  # Use Flyway for migrations
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        default_schema: auth

  flyway:
    enabled: true
    schemas: auth, iam, tenant, governance
    default-schema: auth

server:
  port: 8081

jwt:
  secret: ${JWT_SECRET}
  expiration: 86400000  # 24 hours
  refresh-expiration: 2592000000  # 30 days
```

### 1.3 Models (✓ Completed)

| File | DDL Schema | Layer |
|------|-----------|-------|
| `TenantType.java` | `tenant.tenant_type` | Enum |
| `TenantStatus.java` | `tenant.tenant_status` | Enum |
| `UserStatus.java` | `auth.user_status` | Enum |
| `User.java` | `auth.users` | Entity |
| `Tenant.java` | `tenant.tenants` | Entity |
| `Workspace.java` | `tenant.workspaces` | Entity |
| `Role.java` | `iam.roles` | Entity |
| `Permission.java` | `iam.permissions` | Entity |
| `RolePermission.java` | `iam.role_permissions` | Entity (composite PK) |
| `RolePermissionId.java` | — | Embeddable PK |
| `UserRole.java` | `iam.user_roles` | Entity (composite PK) |
| `UserRoleId.java` | — | Embeddable PK |
| `Policy.java` | `iam.policies` | Entity |
| `PolicyRule.java` | `iam.policy_rules` | Entity |

---

## Phase 2: Repository Layer

### 2.1 User Context

| Repository Interface | Method Signatures |
|---------------------|-------------------|
| `UserRepository` | `findByEmail(String email)` |
| | `findByUsername(String username)` |
| | `existsByEmail(String email)` |
| | `existsByUsername(String username)` |
| | `findAllByStatus(UserStatus status, Pageable pageable)` |
| | `findAllByCreatedAtAfter(OffsetDateTime since, Pageable pageable)` |

### 2.2 Tenant Context

| Repository Interface | Method Signatures |
|---------------------|-------------------|
| `TenantRepository` | `findBySlug(String slug)` |
| | `findAllByStatus(TenantStatus status, Pageable pageable)` |
| `WorkspaceRepository` | `findByTenantIdAndSlug(UUID tenantId, String slug)` |
| | `findAllByTenantId(UUID tenantId)` |
| | `findAllByTenantIdAndIsDeletedFalse(UUID tenantId)` |

### 2.3 RBAC Context

| Repository Interface | Method Signatures |
|---------------------|-------------------|
| `RoleRepository` | `findByCode(String code)` |
| `PermissionRepository` | `findByCode(String code)` |
| | `findAllByResourceType(String resourceType)` |
| `RolePermissionRepository` | `findAllByRoleId(UUID roleId)` |
| `UserRoleRepository` | `findAllByUserId(UUID userId)` |
| | `findAllByRoleId(UUID roleId)` |
| | `findAllByTenantId(UUID tenantId)` |
| | `findAllByUserIdAndTenantId(UUID userId, UUID tenantId)` |

### 2.4 ABAC Context

| Repository Interface | Method Signatures |
|---------------------|-------------------|
| `PolicyRepository` | `findByCode(String code)` |
| | `findAllByEnabledTrue()` |
| `PolicyRuleRepository` | `findAllByPolicyIdOrderByRuleOrder(UUID policyId)` |
| | `findAllByPolicyIdIn(List<UUID> policyIds)` |

---

## Phase 3: Service Layer (Application)

### 3.1 User Service

```
UserService
├── register(RegisterRequest) → User
│     - Create user account
│     - Validate unique email/username
│     - Hash password (via Spring Security)
│     - Assign default role
│     - Publish UserCreated event
│
├── authenticate(LoginRequest) → AuthResponse
│     - Validate credentials
│     - Generate JWT access + refresh tokens
│     - Return tokens + user profile
│
├── refreshToken(String refreshToken) → AuthResponse
│     - Validate refresh token
│     - Issue new access token
│
├── getProfile(UUID userId) → UserProfile
│     - Return user details with roles
│
├── updateProfile(UUID userId, UpdateProfileRequest) → User
│     - Update display name, avatar, etc.
│
├── changePassword(UUID userId, ChangePasswordRequest) → void
│     - Validate old password
│     - Hash new password
│     - Publish PasswordChanged event
│
├── verifyEmail(UUID userId) → void
│     - Set email_verified = true
│     - Publish EmailVerified event
│
├── blockUser(UUID userId, UUID adminId) → void
│     - Set status = BLOCKED
│     - Publish UserBlocked event
│
└── deleteUser(UUID userId, UUID adminId) → void
      - Soft delete
      - Publish UserDeleted event
```

### 3.2 Tenant Service

```
TenantService
├── createTenant(CreateTenantRequest) → Tenant
│     - Create tenant with unique slug
│     - Create default workspace
│     - Assign admin role to creator
│     - Publish TenantCreated event
│
├── getTenantBySlug(String slug) → Tenant
├── updateTenant(UUID tenantId, UpdateTenantRequest) → Tenant
├── suspendTenant(UUID tenantId) → void
│     - Publish TenantSuspended event
│
├── createWorkspace(UUID tenantId, CreateWorkspaceRequest) → Workspace
│     - Validate unique slug within tenant
│     - Publish WorkspaceCreated event
│
├── getWorkspace(UUID tenantId, UUID workspaceId) → Workspace
├── updateWorkspace(UUID tenantId, UUID workspaceId, UpdateWorkspaceRequest) → Workspace
└── deleteWorkspace(UUID tenantId, UUID workspaceId) → void
      - Soft delete
      - Publish WorkspaceDeleted event
```

### 3.3 RBAC Service

```
RbacService
├── createRole(CreateRoleRequest) → Role
├── updateRole(UUID roleId, UpdateRoleRequest) → Role
├── assignPermissionToRole(UUID roleId, UUID permissionId) → void
├── removePermissionFromRole(UUID roleId, UUID permissionId) → void
├── assignRoleToUser(UUID userId, UUID roleId, UUID tenantId, UUID workspaceId) → void
│     - Publish RoleAssigned event
│
├── removeRoleFromUser(UUID userId, UUID roleId, UUID tenantId, UUID workspaceId) → void
│     - Publish RoleRemoved event
│
├── getPermissionsForUser(UUID userId) → List<Permission>
│     - Aggregate permissions from all assigned roles
│
├── getPermissionsForUserInTenant(UUID userId, UUID tenantId) → List<Permission>
├── hasPermission(UUID userId, String permissionCode) → boolean
└── hasPermissionInTenant(UUID userId, UUID tenantId, String permissionCode) → boolean
```

### 3.4 ABAC Service

```
AbacService
├── createPolicy(CreatePolicyRequest) → Policy
├── updatePolicy(UUID policyId, UpdatePolicyRequest) → Policy
├── togglePolicy(UUID policyId, boolean enabled) → void
├── addRuleToPolicy(UUID policyId, AddRuleRequest) → PolicyRule
├── evaluateAccess(EvaluateAccessRequest) → boolean
│     - Evaluate all enabled policies against subject/resource attributes
│     - Return ALLOW if any policy with effect=allow matches
│     - Return DENY if any policy with effect=deny matches
│     - Default: DENY
│
├── getEffectivePolicies(UUID userId, String resourceType) → List<Policy>
└── canAccess(
        UUID userId,
        String resourceType,
        String resourceId,
        String action,
        Map<String, Object> attributes
    ) → AccessDecision
```

### 3.5 Governance Service

```
GovernanceService
├── recordAuditLog(AuditLogRequest) → void
│     - Record all state changes for audit trail
│     - Partitioned by month for performance
│
├── queryAuditLogs(AuditQuery query) → Page<AuditLogResponse>
│     - Filter by actor_id, resource_type, time range
│
├── recordLineage(LineageRequest) → void
│     - Record provenance relationships
│
├── getLineage(UUID targetId, String targetType) → List<LineageResponse>
└── getLineageGraph(UUID targetId, String targetType) → GraphResponse
      - Return full provenance chain
```

---

## Phase 4: Security Layer

### 4.1 JWT Authentication

| Component | Purpose |
|-----------|---------|
| `JwtTokenProvider` | Generate and validate JWT access + refresh tokens |
| `JwtAuthenticationFilter` | OncePerRequestFilter — extract JWT from Authorization header |
| `JwtAuthenticationEntryPoint` | Return 401 for unauthenticated requests |
| `CustomUserDetailsService` | Load User by email/username for Spring Security |

### 4.2 Token Structure

**Access Token Claims:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "roles": ["admin", "researcher"],
  "tenant_id": "tenant-uuid",
  "iat": 1718000000,
  "exp": 1718086400
}
```

### 4.3 Security Configuration

```java
SecurityConfig
├── SecurityFilterChain
│     - Permit: /api/v1/auth/register, /api/v1/auth/login, /api/v1/auth/refresh
│     - Authenticate: everything else
│     - Stateless session
│     - CORS configuration for apps (web-atlas, web-admin, web-research)
│
├── PasswordEncoder
│     - BCryptPasswordEncoder
│
└── AuthenticationManager
      - DaoAuthenticationProvider with CustomUserDetailsService
```

### 4.4 Method Security

```java
@PreAuthorize("hasPermission(#resourceId, 'user', 'read')")
@PreAuthorize("@abacService.canAccess(authentication.principal.id, 'story', #storyId, 'edit', T(java.util.Map).of())")
```

---

## Phase 5: API Layer (REST Controllers)

### 5.1 Auth Controller

```
POST /api/v1/auth/register       → Register new user
POST /api/v1/auth/login          → Login with email/username + password
POST /api/v1/auth/refresh        → Refresh access token
POST /api/v1/auth/logout         → Invalidate refresh token
POST /api/v1/auth/verify-email   → Verify email address
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
```

### 5.2 User Controller

```
GET    /api/v1/users/me                  → Get current user profile
PUT    /api/v1/users/me                  → Update current user profile
PUT    /api/v1/users/me/password         → Change password
GET    /api/v1/users/{userId}            → Get user by ID (admin)
GET    /api/v1/users                     → List users (admin, paginated)
PATCH  /api/v1/users/{userId}/block      → Block user (admin)
DELETE /api/v1/users/{userId}            → Soft delete user (admin)
```

### 5.3 Tenant Controller

```
POST   /api/v1/tenants                  → Create tenant
GET    /api/v1/tenants/{slug}            → Get tenant by slug
PUT    /api/v1/tenants/{tenantId}        → Update tenant
PATCH  /api/v1/tenants/{tenantId}/suspend → Suspend tenant
GET    /api/v1/tenants                   → List tenants (admin)

POST   /api/v1/tenants/{tenantId}/workspaces     → Create workspace
GET    /api/v1/tenants/{tenantId}/workspaces      → List workspaces
GET    /api/v1/tenants/{tenantId}/workspaces/{id} → Get workspace
PUT    /api/v1/tenants/{tenantId}/workspaces/{id} → Update workspace
DELETE /api/v1/tenants/{tenantId}/workspaces/{id} → Delete workspace
```

### 5.4 RBAC Controller

```
POST   /api/v1/roles                   → Create role
GET    /api/v1/roles                   → List roles
GET    /api/v1/roles/{roleId}          → Get role
PUT    /api/v1/roles/{roleId}          → Update role

POST   /api/v1/permissions              → Create permission
GET    /api/v1/permissions              → List permissions

POST   /api/v1/roles/{roleId}/permissions/{permissionId}    → Assign permission to role
DELETE /api/v1/roles/{roleId}/permissions/{permissionId}    → Remove permission from role

POST   /api/v1/users/{userId}/roles     → Assign role to user (with tenant/workspace scope)
DELETE /api/v1/users/{userId}/roles     → Remove role from user
GET    /api/v1/users/{userId}/permissions → Get permissions for user
```

### 5.5 ABAC Controller

```
POST   /api/v1/policies                 → Create policy
GET    /api/v1/policies                 → List policies
GET    /api/v1/policies/{policyId}      → Get policy
PUT    /api/v1/policies/{policyId}      → Update policy
PATCH  /api/v1/policies/{policyId}/toggle → Enable/disable policy

POST   /api/v1/policies/{policyId}/rules  → Add rule to policy
DELETE /api/v1/policies/{policyId}/rules/{ruleId} → Remove rule

POST   /api/v1/access/evaluate          → Evaluate access (for gateway aggregation)
```

### 5.6 Governance Controller

```
GET    /api/v1/audit-logs               → Query audit logs (admin)
GET    /api/v1/lineage/{targetType}/{targetId} → Get provenance lineage
```

---

## Phase 6: Event Publishing

### 6.1 Domain Events

All events are published to Redpanda/Kafka topics for other services to consume.

| Event | Payload | Consumers |
|-------|---------|-----------|
| `UserCreated` | userId, email, username, createdAt | gateway-service (cache warmup), knowledge-service (default workspace) |
| `UserVerified` | userId, email | gateway-service |
| `UserBlocked` | userId, reason | gateway-service |
| `UserDeleted` | userId | all services (cleanup) |
| `TenantCreated` | tenantId, slug, name, ownerId | content-service, knowledge-service |
| `TenantSuspended` | tenantId, reason | all services |
| `WorkspaceCreated` | workspaceId, tenantId, slug | research-service |
| `WorkspaceDeleted` | workspaceId, tenantId | research-service |
| `RoleAssigned` | userId, roleId, tenantId, workspaceId | gateway-service (permission cache) |
| `RoleRemoved` | userId, roleId, tenantId, workspaceId | gateway-service (permission cache) |

### 6.2 Event Publisher Interface

```java
public interface DomainEventPublisher {
    void publish(DomainEvent event);
}

// Implementation using RedpandaTemplate or KafkaTemplate
public class RedpandaEventPublisher implements DomainEventPublisher {
    // publish to topic based on event type
}
```

---

## Phase 7: Implementation Order (Phases)

### Phase 1 — Foundation (Week 1)
- [x] Create all model entities (14 files)
- [ ] Create Flyway migration scripts (V1–V5)
- [ ] Configure `application.yaml` with datasource, JPA, Flyway
- [ ] Add `@EnableJpaAuditing` support in main Application class
- [ ] Add `@EnableMethodSecurity` for pre/post authorization
- [ ] Create base `Repository` interfaces

### Phase 2 — User & Authentication (Week 2)
- [ ] Implement `UserRepository`
- [ ] Implement `UserService` (register, authenticate, refresh)
- [ ] Implement `CustomUserDetailsService`
- [ ] Implement `JwtTokenProvider`
- [ ] Implement `JwtAuthenticationFilter`
- [ ] Implement `SecurityConfig`
- [ ] Implement `AuthController` (register, login, refresh)
- [ ] Implement `UserController` (profile, update)
- [ ] Write unit tests for UserService

### Phase 3 — Tenant Multi-Tenancy (Week 2)
- [ ] Create Flyway seed for default tenant
- [ ] Implement `TenantRepository` + `WorkspaceRepository`
- [ ] Implement `TenantService` + `WorkspaceService`
- [ ] Implement `TenantController` + `WorkspaceController`
- [ ] Add multi-tenant identifier to JWT claims
- [ ] Write unit tests for TenantService

### Phase 4 — RBAC (Week 3)
- [ ] Implement `RoleRepository`, `PermissionRepository`, `UserRoleRepository`
- [ ] Implement `RbacService`
- [ ] Implement `RoleController`, `PermissionController`
- [ ] Seed default roles (admin, researcher, creator, viewer)
- [ ] Implement `@PreAuthorize` checks in controllers
- [ ] Write unit tests for RbacService

### Phase 5 — ABAC (Week 3-4)
- [ ] Implement `PolicyRepository` + `PolicyRuleRepository`
- [ ] Implement `AbacService` with policy evaluation engine
- [ ] Implement `PolicyController`
- [ ] Implement `canAccess()` permission evaluator for Spring Security
- [ ] Write unit tests for ABAC evaluation engine

### Phase 6 — Governance (Week 4)
- [ ] Implement `GovernanceService`
- [ ] Implement audit logging filter/interceptor
- [ ] Implement `AuditLogController`
- [ ] Implement lineage tracking
- [ ] Implement `GovernanceController`

### Phase 7 — Events & Integration (Week 4-5)
- [ ] Integrate Redpanda/Kafka dependency
- [ ] Implement `DomainEventPublisher`
- [ ] Implement event publishing for all domain events
- [ ] Implement OpenAPI documentation (springdoc)
- [ ] Integration tests for full auth flow
- [ ] Performance tests for token generation

---

## Package Structure (Final)

```
services/identity-service/src/main/java/id/livingatlas/identityservice/

├── IdentityServiceApplication.java
├── config/
│   ├── SecurityConfig.java
│   ├── JpaConfig.java
│   ├── RedpandaConfig.java
│   └── OpenApiConfig.java
│
├── user/
│   ├── api/
│   │   ├── AuthController.java
│   │   └── UserController.java
│   ├── application/
│   │   ├── UserService.java
│   │   ├── dto/
│   │   │   ├── RegisterRequest.java
│   │   │   ├── LoginRequest.java
│   │   │   ├── AuthResponse.java
│   │   │   └── UserProfile.java
│   │   └── mapper/
│   │       └── UserMapper.java
│   ├── domain/
│   │   ├── User.java              (refactored from model/)
│   │   ├── UserStatus.java        (refactored from model/)
│   │   ├── UserRepository.java
│   │   └── event/
│   │       ├── UserCreatedEvent.java
│   │       ├── UserVerifiedEvent.java
│   │       ├── UserBlockedEvent.java
│   │       └── UserDeletedEvent.java
│   └── infrastructure/
│       └── JpaUserRepository.java
│
├── tenant/
│   ├── api/
│   │   ├── TenantController.java
│   │   └── WorkspaceController.java
│   ├── application/
│   │   ├── TenantService.java
│   │   ├── WorkspaceService.java
│   │   └── dto/
│   ├── domain/
│   │   ├── Tenant.java
│   │   ├── Workspace.java
│   │   ├── TenantType.java
│   │   ├── TenantStatus.java
│   │   ├── TenantRepository.java
│   │   ├── WorkspaceRepository.java
│   │   └── event/
│   └── infrastructure/
│
├── rbac/
│   ├── api/
│   │   ├── RoleController.java
│   │   └── PermissionController.java
│   ├── application/
│   │   ├── RbacService.java
│   │   └── dto/
│   ├── domain/
│   │   ├── Role.java
│   │   ├── Permission.java
│   │   ├── RolePermission.java
│   │   ├── RolePermissionId.java
│   │   ├── UserRole.java
│   │   ├── UserRoleId.java
│   │   ├── RoleRepository.java
│   │   ├── PermissionRepository.java
│   │   ├── UserRoleRepository.java
│   │   └── event/
│   └── infrastructure/
│
├── abac/
│   ├── api/
│   │   └── PolicyController.java
│   ├── application/
│   │   ├── AbacService.java
│   │   ├── PolicyEvaluator.java
│   │   └── dto/
│   ├── domain/
│   │   ├── Policy.java
│   │   ├── PolicyRule.java
│   │   ├── PolicyRepository.java
│   │   ├── PolicyRuleRepository.java
│   │   └── model/
│   │       ├── AccessDecision.java
│   │       └── PolicyEffect.java
│   └── infrastructure/
│
├── governance/
│   ├── api/
│   │   ├── AuditLogController.java
│   │   └── LineageController.java
│   ├── application/
│   │   └── GovernanceService.java
│   ├── domain/
│   │   ├── AuditLog.java
│   │   ├── Lineage.java
│   │   ├── AuditLogRepository.java
│   │   └── LineageRepository.java
│   └── infrastructure/
│
├── security/
│   ├── JwtTokenProvider.java
│   ├── JwtAuthenticationFilter.java
│   ├── JwtAuthenticationEntryPoint.java
│   ├── CustomUserDetailsService.java
│   └── AbacPermissionEvaluator.java
│
└── shared/
    ├── event/
    │   ├── DomainEvent.java
    │   ├── DomainEventPublisher.java
    │   └── RedpandaEventPublisher.java
    └── dto/
        ├── PageResponse.java
        └── ErrorResponse.java
```

---

## OpenAPI Documentation

All REST endpoints will be documented using springdoc-openapi:

```yaml
springdoc:
  api-docs:
    path: /api-docs
  swagger-ui:
    path: /swagger-ui.html
  packages-to-scan: id.livingatlas.identityservice
```

---

## Dependencies Already in pom.xml

| Dependency | Purpose | Status |
|-----------|---------|--------|
| `spring-boot-starter-data-jpa` | JPA + Hibernate | ✓ |
| `spring-boot-starter-security` | Spring Security | ✓ |
| `spring-boot-starter-validation` | Bean Validation | ✓ |
| `spring-boot-starter-webmvc` | Spring MVC | ✓ |
| `springdoc-openapi-starter-webmvc-ui` | OpenAPI docs | ✓ |
| `jjwt-api / jjwt-impl / jjwt-jackson` | JWT tokens | ✓ |
| `lombok` | Boilerplate reduction | ✓ |

### Dependencies to Add

| Dependency | Purpose | Phase |
|-----------|---------|-------|
| `spring-boot-starter-mail` | Email verification, password reset | Phase 2 |
| `flyway-core + flyway-database-postgresql` | Database migrations | Phase 1 |
| `spring-kafka` or `redpanda-spring-boot-starter` | Event publishing | Phase 7 |
| `spring-boot-starter-cache` | Permission caching | Phase 4 |
| `caffeine` | Local cache for permissions | Phase 4 |
| `spring-boot-starter-data-redis` | Token blacklist, refresh tokens | Phase 2 |
| `testcontainers + testcontainers-postgresql` | Integration testing | Phase 2 |

---

## Testing Strategy

| Layer | Test Type | Framework |
|-------|-----------|-----------|
| Domain | Unit tests | JUnit 5 + Mockito |
| Application | Unit + Integration | JUnit 5 + Mockito |
| API | Web MVC tests | `@WebMvcTest` + MockMvc |
| Repository | Data JPA tests | `@DataJpaTest` + Testcontainers |
| Security | Security tests | `@WebMvcTest` + SecurityMockMvc |
| Integration | Full context | `@SpringBootTest` + Testcontainers |

---

## ADR Decisions for Identity-Service

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | Flat `model/` package initially, refactor to DDD later | Start simple, evolve structure as complexity grows |
| ADR-002 | Soft delete for auth/tenant, never delete for governance | Audit domain must be immutable |
| ADR-003 | JWT over session-based auth | Stateless, microservice-ready, self-contained claims |
| ADR-004 | UUID primary keys | Distributed-friendly, no sequential ID leaks |
| ADR-005 | JSONB for metadata columns | Schema flexibility for polymorphic attributes |
| ADR-006 | Flyway for migrations | Version-controlled, repeatable, CI/CD compatible |
| ADR-007 | RBAC + ABAC layered | RBAC for 80% of access decisions, ABAC for complex policies |
| ADR-008 | Attribute-based policy evaluation in code | Avoids custom DSL complexity; JSON expression stored in DB |

---

## File Inventory

### Created (Phase 1 Complete)

```
services/identity-service/src/main/java/id/livingatlas/identityservice/
├── IdentityServiceApplication.java
├── model/
│   ├── TenantType.java
│   ├── TenantStatus.java
│   ├── UserStatus.java
│   ├── User.java
│   ├── Tenant.java
│   ├── Workspace.java
│   ├── Role.java
│   ├── Permission.java
│   ├── RolePermission.java
│   ├── RolePermissionId.java
│   ├── UserRole.java
│   ├── UserRoleId.java
│   ├── Policy.java
│   └── PolicyRule.java
```

### To Be Created (Phases 1-7)

```
services/identity-service/src/main/resources/
├── application.yaml                        (update)
├── db/migration/
│   ├── V1__identity_schema.sql
│   ├── V2__identity_enums.sql
│   ├── V3__identity_tables.sql
│   ├── V4__identity_indexes.sql
│   └── V5__identity_seed.sql

services/identity-service/src/main/java/id/livingatlas/identityservice/
├── config/
│   ├── SecurityConfig.java
│   ├── JpaConfig.java
│   └── OpenApiConfig.java
├── user/api/ (AuthController, UserController)
├── user/application/ (UserService, DTOs, Mappers)
├── user/domain/ (UserRepository interface, events)
├── user/infrastructure/ (JpaUserRepository)
├── tenant/api/ (TenantController, WorkspaceController)
├── tenant/application/ (TenantService, WorkspaceService)
├── tenant/domain/ (Repository interfaces, events)
├── rbac/api/ (RoleController, PermissionController)
├── rbac/application/ (RbacService)
├── rbac/domain/ (Repository interfaces)
├── abac/api/ (PolicyController)
├── abac/application/ (AbacService, PolicyEvaluator)
├── abac/domain/ (Repository interfaces)
├── governance/api/ (AuditLogController, LineageController)
├── governance/application/ (GovernanceService)
├── governance/domain/ (Repository interfaces)
├── security/ (JwtTokenProvider, JwtAuthenticationFilter, etc.)
└── shared/ (DomainEvent, DomainEventPublisher, DTOs)