# ADR-006: RBAC + ABAC Authorization Model — ABAC Extends RBAC

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture serves 7 distinct user types across multiple tenants, workspaces, and content states:

| User Type | Description | Key Permissions Required |
|-----------|-------------|------------------------|
| **Reader** | General public, horror communities | Read published stories/articles, explore graph, search |
| **Researcher** | Anthropologists, academics | Reader + create collections, annotate stories, save graph views, export datasets |
| **Editor** | Content team, publishers | Review AI output, approve publication, merge knowledge |
| **Reviewer** | Subject matter experts | Validate claims, validate evidence, approve knowledge |
| **Creator** | Writers, storytellers | Create stories, manage sources, submit content |
| **Tenant Admin** | Organization administrators | Workspace management, user management, policy management |
| **System Admin** | Platform operators | Global administration, tenant governance, system configuration |

Beyond role-based access, the platform requires attribute-based decisions that depend on:

- **Tenant membership**: A user from Tenant A must not access Tenant B's private data
- **Workspace membership**: Within a tenant, a user may only access specific workspaces
- **Content ownership**: A user may edit their own drafts but not another user's drafts
- **Content status**: Draft content is restricted to workspace members; published content is tenant-wide
- **Content classification**: PUBLIC content is visible to all; RESTRICTED content requires special roles
- **Action type**: Reading has different permissions than writing, deleting, or administering

A pure RBAC model (role → permissions) cannot express these multi-dimensional access rules without creating an explosion of roles. For example, "Editor who can review drafts in Workspace A but not Workspace B" would require separate roles per workspace in pure RBAC.

## Technical Context

The codebase already implements basic RBAC:

```java
// Role.java — existing RBAC entity
@Entity
@Table(name = "roles", schema = "iam")
public class Role {
    private String code;        // e.g., "EDITOR", "RESEARCHER"
    private String name;
}

// Permission.java — existing permission entity
@Entity
@Table(name = "permissions", schema = "iam")
public class Permission {
    private String code;         // e.g., "story:read", "story:write"
    private String resourceType; // e.g., "story", "collection", "article"
    private String action;       // e.g., "read", "write", "delete", "admin"
}
```

The PRD specifies:
- **Authorization Model**: RBAC + ABAC
- **RBAC Roles**: Reader, Researcher, Editor, Reviewer, Creator, Admin
- **ABAC Dimensions**: Tenant, Workspace, Ownership, Status, Classification

The multi-tenant architecture (ADR-005) establishes tenant isolation at the application layer. The authorization model must integrate with this isolation layer and extend it with fine-grained access control.

## Constraints

1. **Role explosion prevention**: Pure RBAC would require workspace-specific roles (e.g., "EDITOR_WORKSPACE_A", "EDITOR_WORKSPACE_B"). This does not scale. ABAC must eliminate the need for workspace-specific roles.

2. **Performance**: ABAC policy evaluation must not degrade API response times below p95 < 300ms. Policy evaluation is on the critical path for every API request.

3. **Auditability**: Every access decision must be auditable. When a user is denied access, there must be a clear record of which policy (RBAC role, ABAC attribute, or both) caused the denial.

4. **Policy configuration**: Authorization policies must be configurable without code changes. Adding a new permission or modifying an ABAC rule should not require a deployment.

5. **Consistency across layers**: Authorization must be enforced consistently across REST APIs, GraphQL (future), event consumers, and database queries (RLS).

6. **Backward compatibility**: The existing RBAC implementation (Role, Permission entities) must be preserved and extended, not replaced. The ABAC layer must integrate with the existing role-permission mapping.

7. **Human review gate**: AI-generated content in REVIEW_REQUIRED state must only be accessible to editors and reviewers, not to readers or creators.

## Problem Statement

How do we implement an authorization model that combines RBAC (roles and permissions) with ABAC (attribute-based conditions) to provide fine-grained access control across tenants, workspaces, content states, and classifications — without creating role explosion, degrading API performance, or requiring code changes for policy updates?

# Decision

**RBAC + ABAC hybrid model. RBAC defines what roles and base permissions a user has. ABAC extends RBAC by adding attribute-based conditions (tenant, workspace, ownership, status, classification) that are evaluated at runtime for each access request. ABAC conditions are not roles — they are runtime checks that refine RBAC permissions. The policy engine evaluates both layers for every authorization decision.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Authorization Decision Flow                           │
│                                                                          │
│  ┌──────────────┐                                                        │
│  │  API Request  │                                                        │
│  │  + JWT Token  │                                                        │
│  └──────┬───────┘                                                        │
│         │                                                                 │
│         ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Layer 1: Authentication (JWT Verification)            │   │
│  │  - Verify JWT signature and expiry                                │   │
│  │  - Extract user_id, tenant_id, roles                              │   │
│  │  - Reject if invalid or expired                                   │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                             │                                           │
│                             ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Layer 2: RBAC Check (Role → Permission)              │   │
│  │                                                                   │   │
│  │  Does the user's role have the required base permission?          │   │
│  │                                                                   │   │
│  │  User has role: EDITOR                                            │   │
│  │  EDITOR has permission: story:write                               │   │
│  │  → PASS (RBAC check succeeded)                                    │   │
│  │                                                                   │   │
│  │  If FAIL → DENY (user's role does not grant this permission)      │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                             │                                           │
│                             ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Layer 3: ABAC Evaluation (Attribute Checks)          │   │
│  │                                                                   │   │
│  │  Even though RBAC allows story:write, ABAC checks:                │   │
│  │                                                                   │   │
│  │  ┌───────────────────────────────────────────────────────────┐    │   │
│  │  │ 1. Tenant: Is the user a member of the story's tenant?    │    │   │
│  │  │ 2. Workspace: Is the user a member of the workspace       │    │   │
│  │  │    (if the story is a draft)?                              │    │   │
│  │  │ 3. Ownership: Can the user edit another user's story?     │    │   │
│  │  │ 4. Status: Can the user edit a PUBLISHED story?            │    │   │
│  │  │ 5. Classification: Does the user have the required         │    │   │
│  │  │    clearance for RESTRICTED content?                       │    │   │
│  │  └───────────────────────────────────────────────────────────┘    │   │
│  │                                                                   │   │
│  │  If ALL conditions PASS → ALLOW                                   │   │
│  │  If ANY condition FAILS → DENY                                    │   │
│  └──────────────────────────┬───────────────────────────────────────┘   │
│                             │                                           │
│                             ▼                                           │
│                      ┌──────────────┐                                   │
│                      │  ALLOW / DENY │                                   │
│                      └──────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: RBAC Defines Base Permissions

RBAC is the first gate. A user must have a role that grants the required base permission before ABAC conditions are evaluated.

**Role-Permission Mapping**:

```sql
CREATE TABLE identity_role_permissions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_code           VARCHAR(50) NOT NULL REFERENCES identity_roles(code),
    permission_code     VARCHAR(100) NOT NULL REFERENCES identity_permissions(code),
    
    UNIQUE(role_code, permission_code),
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Base Permission Catalog**:

| Resource | Action | Description | Roles Granted |
|----------|--------|-------------|---------------|
| `story` | `read` | Read published stories | READER, RESEARCHER, EDITOR, REVIEWER, CREATOR, ADMIN |
| `story` | `write` | Create and edit stories | CREATOR, EDITOR, ADMIN |
| `story` | `delete` | Soft-delete stories | ADMIN |
| `story` | `publish` | Change story status to PUBLISHED | EDITOR, ADMIN |
| `story` | `review` | Review story AI output | EDITOR, REVIEWER |
| `article` | `read` | Read published articles | READER, RESEARCHER, EDITOR, REVIEWER, CREATOR, ADMIN |
| `article` | `write` | Create and edit articles | EDITOR, CREATOR, ADMIN |
| `article` | `publish` | Change article status to PUBLISHED | EDITOR, ADMIN |
| `knowledge` | `read` | Read knowledge objects | READER, RESEARCHER, EDITOR, REVIEWER, CREATOR, ADMIN |
| `knowledge` | `write` | Create and edit knowledge objects | EDITOR, ADMIN |
| `knowledge` | `validate` | Validate claims and evidence | REVIEWER, ADMIN |
| `knowledge` | `merge` | Merge knowledge objects | EDITOR, ADMIN |
| `collection` | `read` | Read research collections | RESEARCHER, ADMIN |
| `collection` | `write` | Create and edit collections | RESEARCHER, ADMIN |
| `collection` | `delete` | Delete collections | RESEARCHER (own only), ADMIN |
| `annotation` | `write` | Annotate stories | RESEARCHER, ADMIN |
| `source` | `write` | Register and manage sources | CREATOR, EDITOR, ADMIN |
| `transcript` | `read` | Read transcript content | CREATOR, EDITOR, RESEARCHER, ADMIN |
| `workspace` | `admin` | Manage workspace settings | TENANT_ADMIN, SYSTEM_ADMIN |
| `workspace` | `member` | Manage workspace members | TENANT_ADMIN, WORKSPACE_ADMIN |
| `tenant` | `admin` | Manage tenant settings | TENANT_ADMIN, SYSTEM_ADMIN |
| `system` | `admin` | Global system administration | SYSTEM_ADMIN |
| `ai_output` | `review` | Review AI-generated output | EDITOR, REVIEWER, ADMIN |
| `export` | `read` | Export datasets | RESEARCHER, ADMIN |
| `graph` | `read` | Explore knowledge graph | READER, RESEARCHER, EDITOR, REVIEWER, CREATOR, ADMIN |

**User-Role Assignment** (tenant-scoped):

```sql
CREATE TABLE identity_user_roles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES identity_users(id),
    role_code           VARCHAR(50) NOT NULL REFERENCES identity_roles(code),
    tenant_id           UUID NOT NULL,
    workspace_id        UUID,          -- NULL if tenant-wide role
    
    UNIQUE(user_id, role_code, tenant_id, workspace_id),
    
    assigned_by         UUID NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ     -- NULL = no expiry (temporary roles possible)
);
```

### Rule 2: ABAC Extends RBAC with Attribute Conditions

ABAC conditions are evaluated after the RBAC check passes. They refine the base permission based on the resource's attributes and the user's context.

**ABAC Dimension Reference**:

| Dimension | Values | Purpose | Example Check |
|-----------|--------|---------|---------------|
| **Tenant** | `MATCH`, `GLOBAL`, `ANY` | Which tenants can access this resource | User must belong to the same tenant as the resource, or resource is global |
| **Workspace** | `MEMBER`, `PUBLISHED`, `ANY` | Which workspaces can access this resource | Draft content requires workspace membership; published content is tenant-wide |
| **Ownership** | `OWNER`, `WORKSPACE`, `ANY` | Who can modify this resource | Only the creator can edit a draft; workspace editors can edit any workspace content |
| **Status** | `DRAFT`, `REVIEW`, `APPROVED`, `PUBLISHED`, `ARCHIVED`, `ANY` | What states are accessible | Draft content is restricted; published content is open |
| **Classification** | `PUBLIC`, `TENANT`, `WORKSPACE`, `RESTRICTED` | Sensitivity level | RESTRICTED content requires ADMIN role regardless of other permissions |

**ABAC Policy Definition**:

```sql
CREATE TABLE identity_abac_policies (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name         VARCHAR(200) NOT NULL UNIQUE,
    effect              VARCHAR(10) NOT NULL DEFAULT 'ALLOW',  -- ALLOW, DENY (DENY overrides ALLOW)
    
    -- Which resource and action this policy applies to
    resource_pattern    VARCHAR(500) NOT NULL,  -- e.g., 'story:*', 'collection:write', 'knowledge:validate'
                                                -- Supports wildcards: 'story:*' matches all story actions
    
    -- ABAC conditions (JSONB)
    conditions          JSONB NOT NULL DEFAULT '{}',
    -- Supported condition keys:
    -- {
    --   "tenants": ["MATCH"],                    -- Allowed tenant relationships
    --   "workspaces": ["MEMBER", "PUBLISHED"],   -- Allowed workspace relationships
    --   "ownership": ["WORKSPACE"],              -- Allowed ownership relationships
    --   "statuses": ["DRAFT", "REVIEW"],          -- Allowed resource statuses
    --   "classifications": ["PUBLIC", "TENANT"], -- Allowed classifications
    --   "roles": ["EDITOR", "REVIEWER"],         -- Additional role requirements
    --   "attributes": {                           -- Custom attribute matchers
    --     "ai_generated": true                    -- Only applies to AI-generated content
    --   }
    -- }
    
    -- Priority (lower number = higher priority)
    priority            INTEGER NOT NULL DEFAULT 100,
    
    -- Description for audit
    description         TEXT,
    
    -- Active flag for gradual rollout
    is_active           BOOLEAN NOT NULL DEFAULT true,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Default ABAC Policies**:

```sql
-- 1. Tenant isolation: user must match resource tenant (or resource is global)
INSERT INTO identity_abac_policies 
    (policy_name, resource_pattern, conditions, priority, description)
VALUES 
    ('tenant-isolation', '*:*', 
     '{"tenants": ["MATCH", "GLOBAL"]}'::jsonb, 
     1, 'All requests must match tenant or access global resources');

-- 2. Draft content: workspace members only
INSERT INTO identity_abac_policies
    (policy_name, resource_pattern, conditions, priority, description)
VALUES
    ('draft-workspace-isolation', 'story:write,story:read,article:write,article:read',
     '{"statuses": ["DRAFT"], "workspaces": ["MEMBER"]}'::jsonb,
     10, 'Draft content requires workspace membership');

-- 3. Published content: tenant-wide access
INSERT INTO identity_abac_policies
    (policy_name, resource_pattern, conditions, priority, description)
VALUES
    ('published-tenant-wide', 'story:read,article:read,knowledge:read',
     '{"statuses": ["PUBLISHED"], "workspaces": ["PUBLISHED"]}'::jsonb,
     10, 'Published content is visible to all tenant members');

-- 4. Ownership: only creator can delete their own content
INSERT INTO identity_abac_policies
    (policy_name, resource_pattern, conditions, priority, description)
VALUES
    ('owner-delete-only', 'story:delete,collection:delete,annotation:delete',
     '{"ownership": ["OWNER"]}'::jsonb,
     20, 'Only the content creator can delete their own content');

-- 5. Restricted classification: admin only
INSERT INTO identity_abac_policies
    (policy_name, resource_pattern, conditions, priority, description)
VALUES
    ('restricted-admin-only', '*:*',
     '{"classifications": ["RESTRICTED"], "roles": ["ADMIN", "SYSTEM_ADMIN"]}'::jsonb,
     5, 'RESTRICTED content requires ADMIN or SYSTEM_ADMIN role');

-- 6. AI output review: editors and reviewers only
INSERT INTO identity_abac_policies
    (policy_name, resource_pattern, conditions, priority, description)
VALUES
    ('ai-review-restricted', 'ai_output:*',
     '{"statuses": ["REVIEW_REQUIRED"], "roles": ["EDITOR", "REVIEWER"]}'::jsonb,
     5, 'AI output in REVIEW_REQUIRED state requires EDITOR or REVIEWER role');

-- 7. Workspace admin: workspace members with admin role
INSERT INTO identity_abac_policies
    (policy_name, resource_pattern, conditions, priority, description)
VALUES
    ('workspace-admin', 'workspace:admin',
     '{"workspaces": ["MEMBER"], "roles": ["WORKSPACE_ADMIN", "TENANT_ADMIN"]}'::jsonb,
     5, 'Workspace administration requires workspace membership and admin role');
```

### Rule 3: Policy Evaluation Engine

The policy engine evaluates RBAC first, then ABAC. Both must pass for access to be granted.

```java
@Component
public class AuthorizationPolicyEngine {
    
    private final RolePermissionRepository rolePermissionRepo;
    private final AbacPolicyRepository abacPolicyRepo;
    private final AuditLogger auditLogger;
    
    /**
     * Authorize a user action on a resource.
     * 
     * @param user the authenticated user with their roles and attributes
     * @param action the requested action (e.g., "story:write")
     * @param resource the target resource with its attributes
     * @return AuthorizationResult with decision and reason
     */
    public AuthorizationResult authorize(UserContext user, String action, ResourceContext resource) {
        
        // STEP 1: Resolve user's effective permissions from RBAC roles
        Set<String> userPermissions = resolveUserPermissions(user);
        
        // STEP 2: RBAC check — does the user have the base permission?
        if (!userPermissions.contains(action)) {
            // Check for wildcard permission (e.g., "story:*" covers "story:write")
            String resourceType = action.split(":")[0];
            if (!userPermissions.contains(resourceType + ":*") 
                && !userPermissions.contains("*:*")) {
                auditLogger.logDenial(user, action, resource, "RBAC_DENIED", 
                    "User role does not grant permission: " + action);
                return AuthorizationResult.denied("Insufficient permissions");
            }
        }
        
        // STEP 3: Resolve applicable ABAC policies
        // Policies are matched by resource pattern (most specific match wins)
        List<AbacPolicy> policies = resolveAbacPolicies(action, resource);
        
        // STEP 4: Evaluate ABAC policies in priority order
        // Default is ALLOW if no policy explicitly DENIES
        boolean abacResult = true;
        String denialReason = null;
        
        for (AbacPolicy policy : policies) {
            if (!policy.isActive()) continue;
            
            boolean policyResult = evaluatePolicy(policy, user, resource);
            
            if (policy.getEffect() == PolicyEffect.DENY && !policyResult) {
                // DENY policy matched and conditions failed → deny
                abacResult = false;
                denialReason = policy.getDescription();
                break;
            }
            // ALLOW policies are implicitly evaluated — if they pass, continue
            // If they fail, the default is still ALLOW unless a DENY policy catches it
        }
        
        if (!abacResult) {
            auditLogger.logDenial(user, action, resource, "ABAC_DENIED", denialReason);
            return AuthorizationResult.denied(denialReason);
        }
        
        // STEP 5: ALLOW
        auditLogger.logAccess(user, action, resource, "ALLOWED");
        return AuthorizationResult.allowed();
    }
    
    private boolean evaluatePolicy(AbacPolicy policy, UserContext user, ResourceContext resource) {
        JsonNode conditions = policy.getConditions();
        
        // Evaluate tenant dimension
        if (conditions.has("tenants")) {
            if (!evaluateTenantCondition(conditions.get("tenants"), user, resource)) {
                return false;
            }
        }
        
        // Evaluate workspace dimension
        if (conditions.has("workspaces")) {
            if (!evaluateWorkspaceCondition(conditions.get("workspaces"), user, resource)) {
                return false;
            }
        }
        
        // Evaluate ownership dimension
        if (conditions.has("ownership")) {
            if (!evaluateOwnershipCondition(conditions.get("ownership"), user, resource)) {
                return false;
            }
        }
        
        // Evaluate status dimension
        if (conditions.has("statuses")) {
            if (!evaluateStatusCondition(conditions.get("statuses"), resource)) {
                return false;
            }
        }
        
        // Evaluate classification dimension
        if (conditions.has("classifications")) {
            if (!evaluateClassificationCondition(conditions.get("classifications"), user, resource)) {
                return false;
            }
        }
        
        // Evaluate role dimension (additional role requirements beyond RBAC)
        if (conditions.has("roles")) {
            if (!evaluateRoleCondition(conditions.get("roles"), user)) {
                return false;
            }
        }
        
        // Evaluate custom attributes
        if (conditions.has("attributes")) {
            if (!evaluateCustomAttributes(conditions.get("attributes"), resource)) {
                return false;
            }
        }
        
        return true;
    }
    
    private boolean evaluateTenantCondition(JsonNode allowedTenants, UserContext user, ResourceContext resource) {
        for (JsonNode tenantRule : allowedTenants) {
            String rule = tenantRule.asText();
            switch (rule) {
                case "MATCH":
                    if (resource.getTenantId() != null 
                        && resource.getTenantId().equals(user.getTenantId())) {
                        return true;
                    }
                    break;
                case "GLOBAL":
                    if (resource.getTenantId() == null) {
                        return true;  // Global resource (tenant_id IS NULL)
                    }
                    break;
                case "ANY":
                    return true;  // Any tenant access (system operations)
            }
        }
        return false;
    }
    
    private boolean evaluateWorkspaceCondition(JsonNode allowedWorkspaces, UserContext user, ResourceContext resource) {
        if (resource.getWorkspaceId() == null) {
            return true;  // No workspace scope, no restriction
        }
        
        for (JsonNode wsRule : allowedWorkspaces) {
            String rule = wsRule.asText();
            switch (rule) {
                case "MEMBER":
                    if (user.getWorkspaceIds().contains(resource.getWorkspaceId())) {
                        return true;
                    }
                    break;
                case "PUBLISHED":
                    if (resource.getStatus() == ResourceStatus.PUBLISHED) {
                        return true;  // Published content is tenant-wide
                    }
                    break;
                case "ANY":
                    return true;
            }
        }
        return false;
    }
    
    private boolean evaluateOwnershipCondition(JsonNode allowedOwnership, UserContext user, ResourceContext resource) {
        for (JsonNode ownerRule : allowedOwnership) {
            String rule = ownerRule.asText();
            switch (rule) {
                case "OWNER":
                    if (resource.getCreatedBy() != null 
                        && resource.getCreatedBy().equals(user.getUserId())) {
                        return true;
                    }
                    break;
                case "WORKSPACE":
                    if (user.getWorkspaceIds().contains(resource.getWorkspaceId())) {
                        return true;  // Any workspace member can act
                    }
                    break;
                case "ANY":
                    return true;
            }
        }
        return false;
    }
    
    private boolean evaluateStatusCondition(JsonNode allowedStatuses, ResourceContext resource) {
        if (resource.getStatus() == null) {
            return true;  // No status, no restriction
        }
        
        for (JsonNode status : allowedStatuses) {
            if (status.asText().equals(resource.getStatus().name())) {
                return true;
            }
        }
        return false;
    }
    
    private boolean evaluateClassificationCondition(JsonNode allowedClassifications, UserContext user, ResourceContext resource) {
        if (resource.getClassification() == null) {
            return true;
        }
        
        for (JsonNode classification : allowedClassifications) {
            if (classification.asText().equals(resource.getClassification().name())) {
                return true;
            }
        }
        return false;
    }
    
    private boolean evaluateRoleCondition(JsonNode requiredRoles, UserContext user) {
        for (JsonNode role : requiredRoles) {
            if (user.getRoles().contains(role.asText())) {
                return true;
            }
        }
        return false;  // User must have at least one of the required roles
    }
    
    private boolean evaluateCustomAttributes(JsonNode attributes, ResourceContext resource) {
        Iterator<Map.Entry<String, JsonNode>> fields = attributes.fields();
        while (fields.hasNext()) {
            Map.Entry<String, JsonNode> field = fields.next();
            String attrName = field.getKey();
            JsonNode expectedValue = field.getValue();
            JsonNode actualValue = resource.getAttribute(attrName);
            
            if (actualValue == null || !actualValue.equals(expectedValue)) {
                return false;
            }
        }
        return true;
    }
    
    private Set<String> resolveUserPermissions(UserContext user) {
        // Cache permissions per user in Redis with 5-minute TTL
        // On cache miss: query identity_role_permissions for all user roles
        // Return set of permission codes (e.g., {"story:read", "story:write", "collection:read"})
    }
    
    private List<AbacPolicy> resolveAbacPolicies(String action, ResourceContext resource) {
        // Cache active policies in application memory with 60-second refresh
        // Filter by resource_pattern matching the action
        // Sort by priority (ascending)
        // Return applicable policies
    }
}
```

### Rule 4: User Context and Resource Context

The policy engine requires two context objects populated at request time:

**UserContext** (populated from JWT + database lookup):

```java
public class UserContext {
    private UUID userId;
    private UUID tenantId;                     // Current active tenant
    private Set<String> roles;                 // e.g., {"EDITOR", "RESEARCHER"}
    private Set<String> permissions;           // Cached resolved permissions
    private Set<UUID> workspaceIds;            // Workspaces the user belongs to
    private boolean isSystemAdmin;
    private Map<String, Object> attributes;    // Custom user attributes
    
    // Derived checks
    public boolean hasRole(String role) { return roles.contains(role); }
    public boolean hasPermission(String permission) { return permissions.contains(permission); }
    public boolean isMemberOfWorkspace(UUID workspaceId) { return workspaceIds.contains(workspaceId); }
}
```

**ResourceContext** (populated by the service layer from the database):

```java
public class ResourceContext {
    private String resourceType;               // e.g., "story", "article", "collection"
    private UUID resourceId;
    private UUID tenantId;                     // null = global resource
    private UUID workspaceId;                  // null = no workspace scope
    private UUID createdBy;                    // Owner of the resource
    private ResourceStatus status;             // DRAFT, REVIEW, PUBLISHED, ARCHIVED
    private ResourceClassification classification; // PUBLIC, TENANT, WORKSPACE, RESTRICTED
    private Map<String, JsonNode> attributes;  // Custom resource attributes
    
    // Factory method to create from entity
    public static ResourceContext fromStory(Story story) {
        ResourceContext ctx = new ResourceContext();
        ctx.setResourceType("story");
        ctx.setResourceId(story.getId());
        ctx.setTenantId(story.getTenantId());
        ctx.setWorkspaceId(story.getWorkspaceId());
        ctx.setCreatedBy(story.getCreatedBy());
        ctx.setStatus(story.getStatus());
        ctx.setClassification(story.getClassification());
        ctx.setAttributes(Map.of("ai_generated", JsonNodeFactory.instance.booleanNode(story.isAiGenerated())));
        return ctx;
    }
}
```

### Rule 5: Enforcement Points

Authorization is enforced at four layers:

**Layer 1: API Gateway (Pre-Authentication)**
```yaml
# Gateway validates JWT, extracts tenant context
spring:
  cloud:
    gateway:
      routes:
        - id: content-service
          uri: lb://content-service
          predicates:
            - Path=/api/v1/stories/**
          filters:
            - JwtAuthenticationFilter    # Extract user context from JWT
            - TenantContextFilter        # Validate tenant access
            - name: RequestRateLimiter   # Rate limit per tenant
```

**Layer 2: Controller/Security Filter (Request-Level)**
```java
@Component
public class AuthorizationFilter implements Filter {
    
    private final AuthorizationPolicyEngine policyEngine;
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) {
        // Extract action from HTTP method + path
        String action = resolveAction(request);
        
        // Create UserContext from SecurityContext
        UserContext user = SecurityContextHolder.get().getUser();
        
        // For pre-authorization (non-resource-specific), check RBAC only
        if (isResourceAction(request)) {
            // Resource-specific check deferred to service layer
            // (resource attributes are not available at filter time)
            chain.doFilter(request, response);
        } else {
            // Non-resource action (e.g., create new story, list stories)
            AuthorizationResult result = policyEngine.authorize(user, action, null);
            if (result.isDenied()) {
                sendError(response, HttpStatus.FORBIDDEN, result.getReason());
                return;
            }
            chain.doFilter(request, response);
        }
    }
}
```

**Layer 3: Service Layer (Resource-Specific)**
```java
@Service
public class StoryService {
    
    private final AuthorizationPolicyEngine policyEngine;
    private final StoryRepository storyRepository;
    
    @AuthorizationRequired("story:read")
    public Story getStory(UUID storyId) {
        Story story = storyRepository.findById(storyId)
            .orElseThrow(() -> new NotFoundException("Story not found"));
        
        // ABAC check with full resource context
        UserContext user = TenantContextHolder.get().getUser();
        ResourceContext resource = ResourceContext.fromStory(story);
        
        AuthorizationResult result = policyEngine.authorize(user, "story:read", resource);
        if (result.isDenied()) {
            throw new AccessDeniedException(result.getReason());
        }
        
        return story;
    }
    
    @AuthorizationRequired("story:write")
    public Story updateStory(UUID storyId, StoryUpdate update) {
        Story story = storyRepository.findById(storyId)
            .orElseThrow(() -> new NotFoundException("Story not found"));
        
        UserContext user = TenantContextHolder.get().getUser();
        ResourceContext resource = ResourceContext.fromStory(story);
        
        // For write operations, also check if the content is locked (e.g., published)
        AuthorizationResult result = policyEngine.authorize(user, "story:write", resource);
        if (result.isDenied()) {
            throw new AccessDeniedException(result.getReason());
        }
        
        // Apply update
        story.apply(update);
        return storyRepository.save(story);
    }
}
```

**Layer 4: Database (RLS — Defense-in-Depth)**
```sql
-- RLS policy that mirrors ABAC tenant/workspace rules
CREATE POLICY tenant_workspace_isolation ON content_stories FOR ALL
USING (
    tenant_id = current_setting('app.tenant_id')::UUID
    AND (
        status != 'DRAFT'
        OR workspace_id = ANY(
            string_to_array(current_setting('app.workspace_ids'), ',')::UUID[]
        )
    )
);
```

### Rule 6: Permission Caching

ABAC policy evaluation must not degrade API performance. Caching is essential.

**Cache Strategy**:

| Cache | Key | Value | TTL | Invalidation |
|-------|-----|-------|-----|-------------|
| User permissions | user_id + tenant_id | Set<String> permission codes | 5 minutes | On role assignment change |
| ABAC policies | (none — single cache) | List<AbacPolicy> sorted by priority | 60 seconds | On policy CRUD operation |
| Policy evaluation result | user_id + action + resource_hash | AuthorizationResult | 1 second | Not explicitly invalidated — short TTL |

```java
@Component
public class PermissionCache {
    
    private final CacheManager cacheManager;
    
    public Set<String> getUserPermissions(UUID userId, UUID tenantId) {
        Cache cache = cacheManager.getCache("userPermissions");
        String cacheKey = userId + ":" + tenantId;
        
        Set<String> permissions = cache.get(cacheKey, Set.class);
        if (permissions == null) {
            permissions = loadUserPermissions(userId, tenantId);
            cache.put(cacheKey, permissions);
        }
        return permissions;
    }
    
    public List<AbacPolicy> getActivePolicies() {
        Cache cache = cacheManager.getCache("abacPolicies");
        List<AbacPolicy> policies = cache.get("all", List.class);
        if (policies == null) {
            policies = abacPolicyRepo.findByIsActiveTrueOrderByPriority();
            cache.put("all", policies);
        }
        return policies;
    }
    
    @CacheEvict(value = "userPermissions", key = "#userId + ':' + #tenantId")
    public void invalidateUserPermissions(UUID userId, UUID tenantId) {
        // Called when user roles are modified
    }
    
    @CacheEvict(value = "abacPolicies", allEntries = true)
    public void invalidatePolicies() {
        // Called when ABAC policies are created, updated, or deleted
    }
}
```

### Rule 7: Audit Logging

Every authorization decision must be logged for audit purposes.

```java
@Entity
@Table(name = "audit_authorization")
public class AuthorizationAuditLog {
    
    @Id
    private UUID id;
    
    private UUID userId;
    private String userRole;           // Role at time of request
    private String action;             // Requested action
    private String resourceType;       // Resource type
    private UUID resourceId;           // Resource ID (if available)
    private UUID tenantId;
    private UUID workspaceId;
    
    private String decision;           // ALLOWED, RBAC_DENIED, ABAC_DENIED
    private String reason;             // Human-readable reason
    
    private String rbacPermissions;    // User's effective permissions at time of request
    private String abacPolicies;       // ABAC policies that were evaluated
    private String resourceAttributes; // Resource attributes at time of request
    
    private long evaluationTimeMs;     // Policy evaluation duration
    
    private String requestId;          // Correlation ID for request tracing
    private String clientIp;
    
    private OffsetDateTime createdAt;
}
```

### Rule 8: Authorization Annotations

Service methods should use annotations to declaratively specify authorization requirements.

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface AuthorizationRequired {
    String value();           // Required permission (e.g., "story:write")
    boolean resourceCheck() default true;  // Whether to perform ABAC resource check
}

// AOP aspect that enforces authorization
@Aspect
@Component
public class AuthorizationAspect {
    
    private final AuthorizationPolicyEngine policyEngine;
    
    @Around("@annotation(authRequired)")
    public Object checkAuthorization(ProceedingJoinPoint joinPoint, AuthorizationRequired authRequired) throws Throwable {
        UserContext user = TenantContextHolder.get().getUser();
        String action = authRequired.value();
        
        // Find ResourceContext in method arguments
        ResourceContext resource = findResourceContext(joinPoint.getArgs());
        
        AuthorizationResult result = policyEngine.authorize(user, action, resource);
        if (result.isDenied()) {
            throw new AccessDeniedException(result.getReason());
        }
        
        return joinPoint.proceed();
    }
    
    private ResourceContext findResourceContext(Object[] args) {
        for (Object arg : args) {
            if (arg instanceof ResourceContext) {
                return (ResourceContext) arg;
            }
            // Could also scan for entities and convert via ResourceContext.from*()
        }
        return null;
    }
}
```

# Role-Based Permission Matrix

| Permission | READER | RESEARCHER | EDITOR | REVIEWER | CREATOR | TENANT_ADMIN | SYSTEM_ADMIN |
|------------|--------|------------|--------|----------|---------|--------------|--------------|
| `story:read` | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ | ✓ |
| `story:write` | — | — | ✓ ABAC | — | ✓ ABAC | — | ✓ |
| `story:delete` | — | — | — | — | — | — | ✓ |
| `story:publish` | — | — | ✓ ABAC | — | — | — | ✓ |
| `story:review` | — | — | ✓ ABAC | ✓ ABAC | — | — | ✓ |
| `article:read` | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ | ✓ |
| `article:write` | — | — | ✓ ABAC | — | ✓ ABAC | — | ✓ |
| `article:publish` | — | — | ✓ ABAC | — | — | — | ✓ |
| `knowledge:read` | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ | ✓ |
| `knowledge:write` | — | — | ✓ ABAC | — | — | — | ✓ |
| `knowledge:validate` | — | — | — | ✓ ABAC | — | — | ✓ |
| `knowledge:merge` | — | — | ✓ ABAC | — | — | — | ✓ |
| `collection:read` | — | ✓ ABAC | — | — | — | ✓ | ✓ |
| `collection:write` | — | ✓ ABAC | — | — | — | ✓ | ✓ |
| `collection:delete` | — | ✓ OWN | — | — | — | ✓ | ✓ |
| `annotation:write` | — | ✓ ABAC | — | — | — | ✓ | ✓ |
| `source:write` | — | — | ✓ ABAC | — | ✓ ABAC | ✓ | ✓ |
| `transcript:read` | — | ✓ ABAC | ✓ ABAC | — | ✓ ABAC | ✓ | ✓ |
| `workspace:admin` | — | — | — | — | — | ✓ | ✓ |
| `workspace:member` | — | — | — | — | — | ✓ | ✓ |
| `tenant:admin` | — | — | — | — | — | ✓ | ✓ |
| `system:admin` | — | — | — | — | — | — | ✓ |
| `ai_output:review` | — | — | ✓ ABAC | ✓ ABAC | — | — | ✓ |
| `export:read` | — | ✓ ABAC | — | — | — | ✓ | ✓ |
| `graph:read` | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ ABAC | ✓ | ✓ |

**Legend**:
- `✓` = Base permission granted by role (RBAC)
- `✓ ABAC` = Base permission granted, but ABAC conditions apply
- `✓ OWN` = Base permission granted, but ownership check applies
- `—` = No base permission (RBAC denies before ABAC is evaluated)

# Real-World Authorization Scenarios

## Scenario 1: Researcher reads a published story in their tenant

```
User:      Researcher "Budi" (tenant_id = T1, workspace_ids = [W1, W2])
Action:    story:read
Resource:  Story "Misteri Kuntilanak" (tenant_id = T1, workspace_id = W1, status = PUBLISHED, classification = PUBLIC)

Evaluation:
  Layer 2 (RBAC):     RESEARCHER has "story:read" → PASS
  Layer 3 (ABAC):     
    tenant: "MATCH" → T1 == T1 → PASS
    workspace: "PUBLISHED" → status == PUBLISHED → PASS
    classification: "PUBLIC" → PASS
    status: "PUBLISHED" in ["PUBLISHED"] → PASS
  Result: ALLOW
```

## Scenario 2: Researcher tries to read another tenant's draft

```
User:      Researcher "Budi" (tenant_id = T1)
Action:    story:read
Resource:  Story "Misteri X" (tenant_id = T2, workspace_id = W5, status = DRAFT, classification = WORKSPACE)

Evaluation:
  Layer 2 (RBAC):     RESEARCHER has "story:read" → PASS
  Layer 3 (ABAC):     
    tenant: "MATCH" → T1 != T2 → CHECK "GLOBAL" → tenant_id != NULL → FAIL
  Result: DENY (tenant mismatch)
```

## Scenario 3: Editor reviews AI output

```
User:      Editor "Sari" (tenant_id = T1, workspace_ids = [W1], roles = [EDITOR])
Action:    ai_output:review
Resource:  AI Output "Canonical Story #42" (tenant_id = T1, status = REVIEW_REQUIRED, classification = TENANT)

Evaluation:
  Layer 2 (RBAC):     EDITOR has "ai_output:review" → PASS
  Layer 3 (ABAC):
    tenant: "MATCH" → T1 == T1 → PASS
    status: "REVIEW_REQUIRED" in ["REVIEW_REQUIRED"] → PASS
    classification: "TENANT" in ["PUBLIC", "TENANT"] → PASS
    roles: ["EDITOR"] contains "EDITOR" → PASS
  Result: ALLOW
```

## Scenario 4: Creator tries to publish a story

```
User:      Creator "Rudi" (tenant_id = T1, roles = [CREATOR])
Action:    story:publish
Resource:  Story "Misteri Baru" (tenant_id = T1, workspace_id = W1, status = DRAFT)

Evaluation:
  Layer 2 (RBAC):     CREATOR does NOT have "story:publish" → FAIL
  Result: DENY (RBAC — role does not grant this permission)
```

## Scenario 5: Reader tries to access RESTRICTED content

```
User:      Reader "Ani" (tenant_id = T1, roles = [READER])
Action:    story:read
Resource:  Story "Ritual Terlarang" (tenant_id = T1, status = PUBLISHED, classification = RESTRICTED)

Evaluation:
  Layer 2 (RBAC):     READER has "story:read" → PASS
  Layer 3 (ABAC):
    tenant: "MATCH" → PASS
    workspace: "PUBLISHED" → PASS
    classification: "RESTRICTED" → READER not in ["ADMIN", "SYSTEM_ADMIN"] → FAIL
  Result: DENY (classification requires higher role)
```

# Alternatives Considered

## Alternative 1: Pure RBAC with Role Explosion

**Description**: Use pure Role-Based Access Control. Every combination of permissions is a separate role. Workspace-specific permissions are encoded in role names (e.g., `EDITOR_WORKSPACE_A`, `EDITOR_WORKSPACE_B`). No ABAC dimension evaluation.

**Advantages**:
- Simple mental model — "user has role, role has permissions"
- No policy evaluation engine needed — only permission lookups
- Easy to audit — role assignments are explicit
- Well-understood pattern with mature tooling (Spring Security, database)

**Disadvantages**:
- **Role explosion**: With 7 user types × N workspaces × M tenants × S statuses × C classifications, the number of roles becomes N × M × S × C combinations. For 100 tenants with 5 workspaces each and 3 statuses, that is 7 × 500 × 3 = 10,500 roles. This is unmanageable.
- **No dynamic conditions**: A role like `EDITOR_WORKSPACE_A` grants permissions regardless of content status or classification. "Can edit drafts but not published" requires separate roles per status.
- **Administrative burden**: Tenant admins must assign workspace-specific roles to every user. If a user moves from Workspace A to Workspace B, all role assignments must be updated.
- **No content-based conditions**: "Creator can edit their own draft but not another creator's draft" requires separate `CREATOR_OWN_DRAFT` and `CREATOR_OTHER_DRAFT` roles. This doubles the role count.
- **Audit granularity**: Pure RBAC cannot distinguish "denied because wrong workspace" from "denied because content is published" — both are simply "permission denied."

**Rejection rationale**: Pure RBAC at the platform's scale (100+ tenants, 500+ workspaces, multiple content statuses and classifications) would create 10,000+ roles. This is administratively unmanageable and defeats the purpose of role-based access. ABAC eliminates role explosion by evaluating conditions at runtime instead of encoding them in role names.

## Alternative 2: Pure ABAC Without RBAC

**Description**: Eliminate roles entirely. All authorization decisions are based on attribute evaluation. Every API request is checked against a set of attribute-based policies. No role-permission mapping exists.

**Advantages**:
- Maximum flexibility — any attribute can be used in any policy
- No role management overhead — no roles to create, assign, or maintain
- Fine-grained control — policies can express conditions that would be impossible with roles
- Single authorization model — one policy engine for all decisions

**Disadvantages**:
- **No base permissions**: Without roles, every user must be evaluated against every policy for every request. A reader's request goes through the same policy evaluation as an editor's request. This increases evaluation time.
- **Policy complexity**: Without roles as an abstraction, policies must encode all conditions explicitly. "An editor can review drafts" becomes "any user whose workspaces match AND whose position is 'editor' AND whose status is 'active' AND content status is 'REVIEW_REQUIRED' AND..." — every policy becomes complex.
- **No clear permission model**: New developers cannot look at a user's role and understand what they can do. They must trace through policies for every resource and action.
- **Administrative complexity**: Granting a user access to a new area requires understanding the policy model, not just assigning a role.
- **Harder to audit**: "Why was this user allowed?" requires evaluating all policies, not just checking role assignments.
- **Performance overhead**: Every request evaluates all applicable policies. Without RBAC's pre-filtering, the policy engine handles more requests, increasing evaluation time.

**Rejection rationale**: Pure ABAC removes the useful abstraction layer that roles provide. Roles serve as a "first filter" that quickly denies requests that have no business being allowed (e.g., a Reader trying to publish a story). Removing this filter means the policy engine evaluates more requests, increasing latency and complexity. The RBAC + ABAC hybrid provides the best of both: RBAC as a coarse filter, ABAC as a fine-grained refiner.

## Alternative 3: Hardcoded Authorization in Service Layer

**Description**: No centralized authorization model. Each service method implements its own authorization checks using if-else conditions and database queries. Authorization logic is spread across the codebase.

**Advantages**:
- Full control — each service can implement exactly the checks it needs
- No framework dependency — no policy engine, no annotation processing, no AOP
- Simple debugging — authorization logic is in the same method as business logic
- No configuration overhead — no policy tables, no caching layer

**Disadvantages**:
- **Inconsistent enforcement**: Different services implement authorization differently. One service checks tenant_id, another forgets. One service allows draft editing, another blocks it incorrectly.
- **Duplicate logic**: Every service that accesses stories implements the same tenant/workspace/status checks. Changes to authorization rules require updating N service methods.
- **No auditability**: Without a central policy engine, there is no consistent audit log of authorization decisions. Each service may or may not log its checks.
- **No policy configuration**: Changing authorization rules requires code changes, deployment, and rollback. There is no way to modify policies without redeploying.
- **Testing burden**: Each service method's authorization logic must be tested individually. A change to authorization rules requires updating tests for every affected service.
- **No defense-in-depth**: The authorization layer exists only in the service code. There is no RLS mirror, no filter-level enforcement, no annotation-based protection.

**Rejection rationale**: Hardcoded authorization does not scale to a platform with 5+ domain modules, 7 user types, 100+ tenants, and complex multi-dimensional access rules. The duplication, inconsistency, and lack of auditability create security risks that increase with codebase size. A centralized policy engine is essential for consistent enforcement, auditability, and configurability.

## Alternative 4: Open Policy Agent (OPA) as External Policy Engine

**Description**: Use Open Policy Agent (OPA) as an external policy engine. Authorization decisions are made by querying OPA's REST API with user context and resource attributes. Policies are written in Rego and deployed independently of the application.

**Advantages**:
- Policy-as-code with a dedicated policy language (Rego)
- Policy evaluation is separate from application code — policies can be updated without redeploying
- OPA provides a built-in query optimization and caching layer
- Policies can be tested independently using OPA's test framework
- Can be used across multiple services (Java backend, Python AI workers, API gateway)
- Provides a unified authorization model for the entire platform

**Disadvantages**:
- **Additional network latency**: Every authorization decision requires an HTTP call to OPA. Even with caching, this adds network round-trip time to every API request.
- **Infrastructure complexity**: OPA must be deployed, scaled, monitored, and backed up. This adds operational overhead for a small team.
- **Two languages to maintain**: Application code in Java/Python, policies in Rego. Developers must learn both.
- **Policy testing requires Rego expertise**: Writing and testing Rego policies requires specialized knowledge that the team may not have.
- **Integrating OPA with Java annotations is complex**: The clean `@AuthorizationRequired` pattern would require an OPA client library and custom annotation processing.
- **No database-level enforcement**: OPA operates at the application layer only. RLS policies must still be maintained separately.
- **Overkill for current scale**: OPA is designed for large-scale, multi-service policy decision points. For a modular monolith with a small team, a simpler in-process policy engine is sufficient.

**Rejection rationale**: OPA provides powerful policy-as-code capabilities but introduces network latency, infrastructure complexity, and a specialized policy language that the team must learn. For a modular monolith with a small team operating at the current scale, an in-process policy engine with database-backed policies provides the same flexibility without the operational overhead. OPA can be introduced in the future if the platform grows to require a cross-service policy decision point or if policy complexity exceeds the in-process engine's capabilities.

# Consequences

## Positive

1. **No role explosion**: ABAC conditions (tenant, workspace, ownership, status, classification) are evaluated at runtime. The platform needs only 7 base roles regardless of how many tenants, workspaces, or content states exist.

2. **Fine-grained access control**: Permissions can express complex conditions like "Editors can review drafts from any workspace in their tenant" and "Researchers can only delete their own collections." These conditions are configured in policies, not hardcoded.

3. **Configurable without deployment**: ABAC policies are stored in the database and cached with a 60-second refresh. Policy changes take effect within one minute without redeploying the application.

4. **Clear separation of concerns**: RBAC handles "what can this role do?" (base permissions). ABAC handles "under what conditions can this action be performed?" (runtime attribute checks). The two layers are independently maintainable.

5. **Auditability**: Every authorization decision is logged with user context, resource attributes, RBAC permission check result, ABAC policy evaluation result, and evaluation time. This provides a complete audit trail for compliance and debugging.

6. **Defense-in-depth**: Authorization is enforced at four layers (gateway, filter, service, database). A bug in one layer does not compromise security.

7. **Backward compatibility**: The existing `Role` and `Permission` entities are preserved and extended. The ABAC layer integrates with the existing role-permission mapping without requiring changes to existing code.

8. **Performance**: RBAC pre-filters requests before ABAC evaluation, reducing the number of requests that reach the policy engine. Caching (5-minute TTL for permissions, 60-second TTL for policies, 1-second TTL for evaluation results) ensures sub-millisecond policy evaluation for the common case.

## Negative

1. **Policy evaluation is on the critical path**: Every API request must pass through the policy engine. Even with caching, this adds latency to every request. For simple requests (reader reading published content), the policy evaluation may take longer than the actual data retrieval.

2. **Policy configuration complexity**: Writing and maintaining ABAC policy conditions requires understanding the condition schema, resource attributes, and policy priority. Misconfigured policies can result in unintended access grants or denials.

3. **Resource context must be loaded for every request**: ABAC requires the resource's attributes (tenant_id, workspace_id, status, classification, created_by) to evaluate conditions. This means loading the resource from the database even if the policy will deny access, potentially wasting a database query.

4. **Caching invalidation complexity**: User permissions are cached with 5-minute TTL. If a user's role changes (e.g., promoted from Researcher to Editor), they may have stale permissions for up to 5 minutes. Explicit cache invalidation on role change reduces this but adds complexity.

5. **Two-layer authorization model**: Developers must understand both RBAC and ABAC to correctly implement authorization. A common mistake is to assume RBAC is sufficient and skip ABAC checks, or to put conditions in RBAC that should be in ABAC.

6. **Testing complexity**: Authorization tests must cover both RBAC and ABAC layers. For each permission, tests must verify: (a) RBAC grants it for the correct roles, (b) ABAC allows it for the correct attributes, (c) ABAC denies it for incorrect attributes.

7. **Policy priority management**: As the number of policies grows (50+), managing priority ordering becomes complex. A policy with higher priority than intended can override another policy's effect.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Role management** | 7 base roles only, no explosion | ABAC policy configuration complexity |
| **Access granularity** | Fine-grained attribute-based conditions | Resource context must be loaded for evaluation |
| **Configurability** | Policy changes without deployment | Policy refresh delay (60 seconds max) |
| **Performance** | RBAC pre-filtering, multi-level caching | Policy evaluation on every request critical path |
| **Auditability** | Complete decision logging | Audit log storage grows with request volume |
| **Developer experience** | Declarative annotations | Must understand both RBAC and ABAC models |
| **Security** | 4-layer defense-in-depth | More layers = more code to maintain and test |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Stale permission cache allows unauthorized access** | Low | High — user retains permissions after role revocation | Short TTL (5 minutes). Force cache invalidation on role change. RLS provides database-level defense if cache is stale. |
| **ABAC policy misconfiguration grants unintended access** | Medium | High — overly permissive policy exposes data | Test policies in CI/CD. Run policy evaluation tests that verify access for known scenarios. Use DENY-by-default pattern — only ALLOW policies explicitly grant access. |
| **Resource context not available for evaluation** | Medium | Medium — ABAC check may incorrectly pass or fail | Implement null-safe evaluation. If resource attributes are missing and policy requires them, default to DENY. Log warnings for missing attributes. |
| **Policy evaluation performance degrades at scale** | Low | Medium — increased API latency | Cache evaluation results (1-second TTL). Benchmark policy evaluation under load. Optimize policy matching (index by resource_pattern + action). |
| **Annotation-based authorization not applied to new methods** | Medium | Medium — new feature missing authorization | Enforce authorization annotations in code review. Add ArchUnit test that verifies all service methods with @RequestMapping have @AuthorizationRequired. |
| **ABAC policy priority conflicts** | Low | Low — wrong policy wins | Use unique priority values (no duplicates). Enforce priority uniqueness at database level. Document priority ranges for different policy categories. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Developer misunderstands ABAC and implements incorrect conditions** | Medium | Medium — data leakage or blocked access | Provide ABAC policy templates for common patterns. Review policy changes in code review. Maintain policy documentation with examples. |
| **Audit log volume overwhelms storage** | Medium | Medium — increased storage cost | Configurable sample rate (log all denials, sample allowed requests). Archive audit logs after 90 days. Implement log retention policy. |
| **Role-permission matrix becomes outdated** | Medium | Low — inconsistent permissions | Maintain role-permission matrix as a living document. Automate matrix verification against actual database policies. Include matrix in onboarding documentation. |
| **Temporary role assignment (expires_at) not enforced** | Low | Medium — user retains expired role | Implement scheduled job that checks expires_at and revokes expired roles. Cache invalidation on role revocation ensures timely enforcement. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Policy count exceeds 200** | Policy management becomes complex | Categorize policies by domain. Implement policy namespacing. Consider OPA for advanced policy management. |
| **Cross-service authorization required** | Current in-process engine cannot handle external services | The policy engine is self-contained and can be extracted as a library. OPA can be introduced as a separate service if needed. |
| **Real-time authorization changes required** | 60-second policy refresh delay may be too long | Reduce cache TTL. Implement webhook-based cache invalidation when policies change. |
| **Fine-grained field-level authorization required** | Current model operates at resource level | ABAC conditions can be extended with field-level checks. ResourceContext can include field-level attributes. This is a future enhancement, not a rewrite. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Policy count exceeds 200**: At this scale, policy management (priority, categorization, testing) becomes complex. Consider policy-as-code with OPA or a dedicated policy management UI.

2. **Cross-service authorization required**: If microservices are introduced (per ADR-002 extraction strategy), the in-process policy engine must be extracted as a shared library or replaced with OPA as a sidecar service.

3. **Field-level authorization required**: If the platform needs to restrict access to specific fields within a resource (e.g., "Reviewers can see source citation but not source contact information"), the authorization model must be extended to support field-level ABAC conditions.

4. **Attribute-based roles (ABAR) emerge**: If the platform identifies recurring attribute patterns that could be abstracted into dynamic roles (e.g., "All workspace editors in this tenant"), the role model could be extended with attribute-driven role assignment.

5. **Performance requirements exceed caching capabilities**: If policy evaluation latency exceeds p95 < 5ms under load, consider moving to a more efficient policy evaluation engine, reducing policy complexity, or implementing a policy decision cache with longer TTL.

6. **Regulatory requirements mandate periodic authorization review**: If auditors require periodic review of all authorization policies and role assignments, implement automated policy review workflows and role certification processes.

# References

- **Backend Platform PRD §8** — "Authorization Model" — RBAC + ABAC with specific dimensions.
- **Backend Platform PRD §5** — "User Types" — 7 user types with capabilities.
- **Backend Platform PRD §9** — "State Machines" — Story, Knowledge, Article states that affect authorization.
- **ADR-005: Multi-Tenant Architecture** — Shared database, tenant isolation, workspace isolation, RLS policies.
- **NIST SP 800-162** — "Guide to Attribute Based Access Control (ABAC) Definition and Considerations" — Standard definition of ABAC.
- **Spring Security** — https://spring.io/projects/spring-security — Method-level security with @PreAuthorize.
- **Open Policy Agent** — https://www.openpolicyagent.org/ — Policy-as-code engine (future consideration).
- **AWS IAM Policy Model** — https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html — Inspiration for resource-based policy format.