# ADR-005: Multi-Tenant Architecture — Shared Database, Application-Layer Isolation, ABAC Enforced

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture serves multiple tenant types with fundamentally different data access requirements:

- **Individual researchers** — Access their own collections, annotations, and exports. May contribute stories to the global knowledge base.
- **Research institutions** — Multiple researchers within the same institution share workspaces, collections, and annotations. Require isolation from other institutions.
- **Publishers and production houses** — Manage their own content pipelines, editorial workflows, and published articles. Require strict data isolation for unpublished content.
- **Educational institutions** — Curate custom learning paths from the global knowledge base. Require read access to global data but isolation for their custom content.
- **Government and cultural preservation bodies** — May require the highest level of data isolation for sensitive cultural knowledge.

The platform also maintains a **global knowledge base** of folklore entities, themes, motifs, beliefs, traditions, and cultural narratives that is shared across all tenants. This global knowledge is the core value proposition — no single tenant owns it, but all tenants benefit from it.

## Technical Context

The platform uses a single PostgreSQL 18 database (per ADR-001) deployed as a modular monolith (per ADR-002). The identity domain manages tenants, workspaces, users, roles, and permissions. The authorization model is RBAC + ABAC (per Backend Platform PRD §8).

The current codebase already implements a basic tenant model:

```java
// TenantController.java — existing implementation
@PostMapping("/{tenantId}/workspaces")
public ResponseEntity<ApiResponse<Workspace>> createWorkspace(
    @PathVariable UUID tenantId, @RequestBody Workspace workspace) {
    Workspace saved = workspaceRepo.save(workspace);
    return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(saved));
}
```

The PRD specifies:
- **Model**: Shared Database, Shared Schema
- **Tenant Isolation**: `tenant_id`, `workspace_id`
- **All queries must be tenant-scoped**
- **ABAC Dimensions**: Tenant, Workspace, Ownership, Status, Classification

## Constraints

1. **Global knowledge sharing**: Folklore entities, themes, motifs, beliefs, and traditions must be accessible to all tenants. These are not owned by any single tenant. Tenant isolation must not prevent cross-tenant knowledge discovery.

2. **Tenant-private data**: Collections, annotations, notes, drafts, and unpublished content must be strictly isolated. Tenant A must never see Tenant B's private data.

3. **Workspace-level isolation within tenants**: A research institution may have multiple workspaces (e.g., "Java Folklore Research" and "Sumatran Myth Studies"). Researchers in one workspace must not see data from another workspace within the same tenant unless explicitly shared.

4. **ABAC enforcement**: Authorization is not just about tenant membership. It must consider workspace membership, data ownership, content status (draft vs. published), and content classification (public vs. restricted).

5. **Audit requirements**: Every business table must contain `tenant_id` and `workspace_id` for audit trail purposes.

6. **Scalability target**: 100,000 stories, 10,000,000 transcript segments, 1,000,000 knowledge objects across all tenants. The multi-tenant architecture must not become a performance bottleneck.

7. **99.5% availability**: Tenant isolation logic must not introduce failure modes that affect other tenants. A misconfigured policy for one tenant must not crash the application for all tenants.

8. **Team size**: Small team (3–8 engineers). The multi-tenant architecture must be simple to implement and maintain. Complex per-tenant infrastructure is not feasible.

## Problem Statement

How do we implement multi-tenancy that provides strong data isolation between tenants, supports workspace-level isolation within tenants, enables global knowledge sharing across all tenants, enforces ABAC at the application layer, and remains operationally simple for a small team — all within a single shared PostgreSQL database?

# Decision

**Shared PostgreSQL database with shared schema. Tenant isolation enforced at the application layer via ABAC. All business tables include `tenant_id` and `workspace_id`. Global knowledge tables use `tenant_id IS NULL` to indicate shared data. Row-Level Security (RLS) in PostgreSQL provides defense-in-depth. No per-tenant databases or per-tenant schemas.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Application Layer (ABAC Enforcement)             │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  API Gateway  │  │  Identity    │  │  Domain      │  │  Query     │  │
│  │  (JWT Auth)   │  │  Module      │  │  Services    │  │  Intercept │  │
│  │               │  │              │  │              │  │            │  │
│  │  Extracts:    │  │  Resolves:   │  │  Enforces:   │  │  Appends:  │  │
│  │  - tenant_id  │  │  - User      │  │  - tenant_id │  │  - WHERE   │  │
│  │  - user_id    │  │    roles     │  │  - workspace │  │    tenant   │  │
│  │  - roles      │  │  - ABAC      │  │  - Ownership │  │    _id = ?  │  │
│  │               │  │    policies  │  │  - Status    │  │  - WHERE    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │    workspace│  │
│                                                         │    _id = ?  │  │
│                                                         └────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 18 (Single Database)                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Global Knowledge Tables (tenant_id IS NULL)                     │   │
│  │  ───────────────────────────────────────                         │   │
│  │  knowledge_folklore     │  knowledge_themes     │  knowledge_motifs│  │
│  │  knowledge_beliefs      │  knowledge_traditions │  knowledge_rituals│ │
│  │  knowledge_creatures    │  knowledge_locations  │                 │  │
│  │                                                                   │   │
│  │  These tables have tenant_id = NULL. Readable by all tenants.     │   │
│  │  Writable only by system admins or through contribution workflow. │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Tenant-Scoped Tables (tenant_id NOT NULL)                       │   │
│  │  ─────────────────────────────────────                           │   │
│  │                                                                   │   │
│  │  Identity:                                                        │   │
│  │    identity_tenants     │  identity_workspaces                     │   │
│  │    identity_users       │  identity_user_tenant_mappings           │   │
│  │    identity_roles       │  identity_permissions                    │   │
│  │                                                                   │   │
│  │  Content:                                                         │   │
│  │    content_sources      │  content_transcripts                    │   │
│  │    content_stories      │  content_story_versions                 │   │
│  │    content_articles     │  content_article_versions               │   │
│  │                                                                   │   │
│  │  Knowledge:                                                       │   │
│  │    knowledge_objects    │  knowledge_claims                       │   │
│  │    knowledge_contradictions                                       │   │
│  │                                                                   │   │
│  │  Research:                                                        │   │
│  │    research_collections │  research_annotations                   │   │
│  │    research_notes       │  research_exports                       │   │
│  │                                                                   │   │
│  │  Workflow:                                                        │   │
│  │    workflow_approvals   │  workflow_publications                  │   │
│  │    workflow_moderations                                           │   │
│  │                                                                   │   │
│  │  Governance:                                                      │   │
│  │    audit_logs           │  lineage_records                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Row-Level Security Policies (Defense-in-Depth)                  │   │
│  │                                                                   │   │
│  │  CREATE POLICY tenant_isolation ON content_stories                │   │
│  │  USING (                                                          │   │
│  │    tenant_id = current_setting('app.tenant_id')::UUID             │   │
│  │    OR current_setting('app.is_system_admin')::boolean = true      │   │
│  │  );                                                               │   │
│  │                                                                   │   │
│  │  CREATE POLICY global_knowledge_read ON knowledge_folklore        │   │
│  │  USING (                                                          │   │
│  │    tenant_id IS NULL                                              │   │
│  │    OR tenant_id = current_setting('app.tenant_id')::UUID          │   │
│  │  );                                                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Shared Database, Shared Schema

All tenants share a single PostgreSQL database and a single set of schemas (the `public` schema or domain-specific schemas). Tenant isolation is achieved through row-level `tenant_id` and `workspace_id` columns, not through database or schema separation.

**Table classification**:

| Category | tenant_id | workspace_id | Example Tables |
|----------|-----------|--------------|----------------|
| **Global Knowledge** | NULL | NULL | `knowledge_folklore`, `knowledge_themes`, `knowledge_motifs`, `knowledge_beliefs`, `knowledge_traditions`, `knowledge_rituals`, `knowledge_creatures`, `knowledge_locations` |
| **Tenant Identity** | NOT NULL | NULL | `identity_tenants`, `identity_workspaces`, `identity_roles`, `identity_permissions` |
| **Tenant Content** | NOT NULL | NULL or NOT NULL | `content_sources`, `content_transcripts`, `content_stories`, `content_articles` |
| **Workspace Content** | NOT NULL | NOT NULL | `research_collections`, `research_annotations`, `research_notes`, `research_exports` |
| **Cross-Tenant Governance** | NOT NULL | NULL | `audit_logs`, `lineage_records`, `workflow_approvals` |

### Rule 2: Application-Layer ABAC Enforcement

All tenant isolation is enforced at the application layer. Every repository query must include tenant and workspace filters. This is the primary isolation mechanism.

**Enforcement layers**:

```
Layer 1: API Gateway
  - Extracts tenant_id, user_id, and roles from JWT
  - Rejects requests without valid tenant context
  - Sets request attributes for downstream filters

Layer 2: Security Context Filter
  - Resolves user's tenant memberships and workspace memberships
  - Populates SecurityContext with TenantContext
  - Validates that the requested tenant_id matches the user's membership

Layer 3: Repository Query Interceptor
  - Automatically appends tenant_id and workspace_id filters to queries
  - For global knowledge tables, allows tenant_id IS NULL access
  - For tenant-scoped tables, enforces tenant_id = current_tenant

Layer 4: Service-Layer ABAC
  - Enforces fine-grained policies beyond tenant isolation
  - Checks: ownership, content status, content classification, role-based permissions
  - Example: "Only the creator or a workspace editor can update a draft story"
```

**TenantContext propagation**:

```java
// Security context populated by JWT filter
public class TenantContext {
    private UUID tenantId;
    private UUID userId;
    private Set<UUID> workspaceIds;       // Workspaces the user belongs to
    private Set<String> roles;            // Global roles (e.g., SYSTEM_ADMIN)
    private Map<String, Object> attributes; // ABAC attributes
    private boolean isSystemAdmin;
}

// ThreadLocal holder for request-scoped access
public class TenantContextHolder {
    private static final ThreadLocal<TenantContext> CONTEXT = new ThreadLocal<>();
    
    public static void set(TenantContext context) { CONTEXT.set(context); }
    public static TenantContext get() { return CONTEXT.get(); }
    public static void clear() { CONTEXT.remove(); }
}
```

**Repository-level enforcement**:

```java
// Base repository with automatic tenant filtering
public interface TenantAwareRepository<T, ID> extends JpaRepository<T, ID> {
    
    @Query("SELECT t FROM #{#entityName} t WHERE t.tenantId = :tenantId")
    List<T> findByTenantId(@Param("tenantId") UUID tenantId);
    
    @Query("SELECT t FROM #{#entityName} t WHERE t.tenantId = :tenantId AND t.workspaceId = :workspaceId")
    List<T> findByTenantIdAndWorkspaceId(
        @Param("tenantId") UUID tenantId, 
        @Param("workspaceId") UUID workspaceId
    );
}

// Usage in service layer
@Service
public class StoryService {
    
    public List<Story> listStories() {
        TenantContext context = TenantContextHolder.get();
        
        if (context.isSystemAdmin()) {
            return storyRepository.findAll();  // System admin sees all
        }
        
        return storyRepository.findByTenantId(context.getTenantId());
    }
    
    public Story getStory(UUID storyId) {
        TenantContext context = TenantContextHolder.get();
        Story story = storyRepository.findById(storyId)
            .orElseThrow(() -> new NotFoundException("Story not found"));
        
        // Enforce tenant isolation
        if (!context.isSystemAdmin() && !story.getTenantId().equals(context.getTenantId())) {
            throw new AccessDeniedException("Access denied");
        }
        
        // Enforce workspace isolation for draft content
        if (story.getStatus() == StoryStatus.DRAFT 
            && !context.getWorkspaceIds().contains(story.getWorkspaceId())) {
            throw new AccessDeniedException("Access denied");
        }
        
        return story;
    }
}
```

### Rule 3: Global Knowledge with Shared Read, Controlled Write

Global knowledge tables (folklore, themes, motifs, beliefs, traditions) are readable by all tenants but writable only through a controlled contribution workflow.

**Read access**: Any authenticated user from any tenant can read global knowledge. No tenant filter is applied.

```sql
-- Global knowledge query — no tenant filter
SELECT * FROM knowledge_folklore WHERE id = :folkloreId;
```

**Write access**: Global knowledge is created/updated through one of two paths:
1. **System admin direct edit**: System administrators can directly modify global knowledge.
2. **Tenant contribution workflow**: A tenant submits a contribution (e.g., "new folklore entity"). This creates a `PENDING_REVIEW` record in a contribution table. A system admin or designated reviewer approves or rejects the contribution. On approval, the data is written to the global knowledge table with `tenant_id = NULL`.

```sql
-- Contribution table for global knowledge
CREATE TABLE knowledge_contributions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source tenant
    tenant_id           UUID NOT NULL,
    workspace_id        UUID,
    contributed_by      UUID NOT NULL,
    
    -- Target global entity
    target_table        VARCHAR(100) NOT NULL,  -- 'knowledge_folklore', 'knowledge_themes', etc.
    target_data         JSONB NOT NULL,          -- The proposed entity data
    
    -- Review state
    status              VARCHAR(50) NOT NULL DEFAULT 'PENDING_REVIEW',
    -- PENDING_REVIEW → APPROVED → MERGED
    -- PENDING_REVIEW → REJECTED
    
    reviewed_by         UUID,
    reviewed_at         TIMESTAMPTZ,
    review_notes        TEXT,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Tenant-specific overrides**: A tenant may create tenant-specific annotations on global knowledge (e.g., "In our region, Kuntilanak is called Matianak"). These are stored in tenant-scoped tables with a reference to the global entity:

```sql
CREATE TABLE knowledge_tenant_overrides (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    global_entity_id    UUID NOT NULL,            -- References knowledge_folklore.id
    tenant_id           UUID NOT NULL,
    
    -- Tenant-specific data
    local_name          VARCHAR(500),              -- Regional name variation
    local_description   TEXT,                      -- Regional description
    local_beliefs       JSONB,                     -- Regional belief variations
    metadata            JSONB,
    
    -- Only the owning tenant can read/write this
    UNIQUE(global_entity_id, tenant_id),
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Rule 4: Workspace-Level Isolation Within Tenants

Workspaces provide sub-tenant isolation. A tenant may have multiple workspaces, each with its own members, content, and research data.

**Workspace membership model**:

```sql
CREATE TABLE identity_workspace_members (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL REFERENCES identity_workspaces(id),
    user_id             UUID NOT NULL REFERENCES identity_users(id),
    role                VARCHAR(50) NOT NULL,  -- 'workspace_admin', 'workspace_editor', 'workspace_viewer'
    
    UNIQUE(workspace_id, user_id),
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Workspace-scoped queries**:

```java
// Research data is always workspace-scoped
public List<Collection> listCollections() {
    TenantContext context = TenantContextHolder.get();
    
    // User can only see collections in workspaces they belong to
    return collectionRepository.findByWorkspaceIdIn(context.getWorkspaceIds());
}

// Content can be tenant-scoped or workspace-scoped depending on status
public List<Story> listStories() {
    TenantContext context = TenantContextHolder.get();
    
    // Published stories: visible to entire tenant
    // Draft stories: visible only to workspace members
    return storyRepository.findByTenantIdAndVisibility(
        context.getTenantId(),
        context.getWorkspaceIds()
    );
}
```

**Cross-workspace sharing**: Workspace members can explicitly share content with other workspaces within the same tenant:

```sql
CREATE TABLE content_shared_resources (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type       VARCHAR(50) NOT NULL,  -- 'story', 'collection', 'annotation'
    resource_id         UUID NOT NULL,
    source_workspace_id UUID NOT NULL,
    target_workspace_id UUID NOT NULL,
    permission          VARCHAR(50) NOT NULL DEFAULT 'VIEW',  -- VIEW, EDIT, ADMIN
    
    UNIQUE(resource_type, resource_id, target_workspace_id),
    
    created_by          UUID NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Rule 5: Row-Level Security as Defense-in-Depth

PostgreSQL Row-Level Security (RLS) provides a secondary isolation layer. If a bug in the application layer bypasses tenant filtering, RLS prevents data leakage.

```sql
-- Enable RLS on tenant-scoped tables
ALTER TABLE content_stories ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_annotations ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_claims ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy
CREATE POLICY tenant_isolation ON content_stories FOR ALL
USING (
    tenant_id = current_setting('app.tenant_id')::UUID
    OR current_setting('app.is_system_admin')::boolean = true
);

-- Workspace isolation for draft content
CREATE POLICY workspace_isolation ON content_stories FOR ALL
USING (
    status != 'DRAFT'  -- Published content visible to all tenant members
    OR workspace_id = ANY(
        string_to_array(current_setting('app.workspace_ids'), ',')::UUID[]
    )
    OR current_setting('app.is_system_admin')::boolean = true
);

-- Global knowledge read policy
CREATE POLICY global_knowledge_read ON knowledge_folklore FOR SELECT
USING (
    tenant_id IS NULL  -- Global entities visible to all
    OR tenant_id = current_setting('app.tenant_id')::UUID  -- Tenant-specific overrides
);

-- Global knowledge write policy (only system admins)
CREATE POLICY global_knowledge_write ON knowledge_folklore FOR INSERT
WITH CHECK (
    current_setting('app.is_system_admin')::boolean = true
);
```

**Important**: RLS is a defense-in-depth measure, not the primary isolation mechanism. The application layer is the primary enforcement point. RLS protects against:
- SQL injection that bypasses application filters
- Direct database access by operators
- Bugs in application-layer tenant filtering

### Rule 6: Tenant Context Propagation Through Events

Events published to Redpanda must carry tenant context so that downstream consumers (AI workers, projection workers) enforce tenant isolation.

```json
{
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "eventType": "StoryCreated",
  "eventVersion": 1,
  "data": {
    "storyId": "a1b2c3d4-...",
    "title": "Misteri Kuntilanak"
  },
  "metadata": {
    "tenantId": "11111111-...",       ← Required for tenant isolation
    "workspaceId": "66666666-...",    ← Required for workspace isolation
    "correlationId": "...",
    "causationId": "..."
  }
}
```

**AI Worker tenant isolation**:
```python
async def process_extraction_job(job_id, transcript_id, tenant_id, workspace_id):
    # Read transcript — must be scoped to the tenant
    transcript = await db.fetch_row(
        "SELECT text, metadata FROM content_transcripts "
        "WHERE id = $1 AND tenant_id = $2",  # ← Tenant filter
        transcript_id, tenant_id
    )
    
    # Write result — must include tenant context
    await db.execute("""
        INSERT INTO ai_output_canonical_stories 
            (id, job_id, transcript_id, story_data, 
             tenant_id, workspace_id, status, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, 'REVIEW_REQUIRED', NOW())
    """, story_id, job_id, transcript_id, 
         json.dumps(result),
         tenant_id, workspace_id)  # ← Tenant context preserved
```

**Projection Worker tenant isolation**:
```python
async def handle_graph_projection(event):
    tenant_id = event.metadata['tenantId']
    
    # Neo4j: use tenant_id as a node property for isolation
    await neo4j_session.run(
        """
        MERGE (s:Story {id: $id, tenant_id: $tenant_id})
        SET s.title = $title
        """,
        id=event.aggregate_id,
        tenant_id=tenant_id,  # ← Tenant context in graph
        title=event.data['title']
    )
    
    # Weaviate: use tenant_id for multi-tenancy
    # Weaviate supports native multi-tenancy via tenant_id
    await weaviate_client.data_object.create(
        data_object={
            "title": event.data['title'],
            "tenant_id": str(tenant_id)  # ← Tenant context in vector
        },
        class_name="Story",
        tenant=str(tenant_id)  # ← Weaviate native multi-tenancy
    )
```

### Rule 7: Tenant Onboarding and Deletion

**Tenant onboarding flow**:

1. System admin creates a new tenant via `POST /api/v1/tenants`
2. System creates default workspace for the tenant
3. System creates default roles (workspace_admin, workspace_editor, workspace_viewer)
4. System admin invites the tenant admin user
5. Tenant admin user accepts invitation and is assigned `workspace_admin` role
6. Tenant admin can now create additional workspaces, invite users, and manage the tenant

**Tenant deletion (soft delete)**:

```sql
-- Tenants are soft-deleted
UPDATE identity_tenants 
SET status = 'ARCHIVED', deleted_at = NOW(), deleted_by = $1 
WHERE id = $2;

-- All tenant data is preserved but inaccessible
-- RLS policy blocks access to archived tenants
CREATE POLICY tenant_active_only ON content_stories FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM identity_tenants 
        WHERE id = tenant_id AND status != 'ARCHIVED'
    )
);
```

**Data retention after tenant deletion**:
- Tenant's contributed global knowledge remains (it was contributed to the global knowledge base)
- Tenant's private data is preserved for a retention period (default: 90 days)
- After retention period, tenant data is anonymized or deleted
- Audit logs are preserved indefinitely (regulatory requirement)

### Rule 8: ABAC Policy Model

ABAC policies are evaluated at the service layer. The policy engine checks multiple dimensions before granting access.

```java
// ABAC Policy Evaluation
public class AbacPolicyEngine {
    
    public boolean evaluate(Policy policy, TenantContext context, Resource resource) {
        // Check all required dimensions
        return switch (policy.getEffect()) {
            case ALLOW -> evaluateTenant(policy, context, resource)
                && evaluateWorkspace(policy, context, resource)
                && evaluateOwnership(policy, context, resource)
                && evaluateStatus(policy, context, resource)
                && evaluateClassification(policy, context, resource)
                && evaluateRole(policy, context, resource);
                
            case DENY -> false;  // Explicit deny overrides allow
        };
    }
    
    private boolean evaluateTenant(Policy policy, TenantContext context, Resource resource) {
        // Tenant must match
        return resource.getTenantId() == null  // Global resource
            || resource.getTenantId().equals(context.getTenantId())
            || context.isSystemAdmin();
    }
    
    private boolean evaluateWorkspace(Policy policy, TenantContext context, Resource resource) {
        if (resource.getWorkspaceId() == null) return true;  // No workspace scope
        if (resource.getStatus() == ResourceStatus.PUBLISHED) return true;  // Published is tenant-wide
        return context.getWorkspaceIds().contains(resource.getWorkspaceId());
    }
    
    private boolean evaluateOwnership(Policy policy, TenantContext context, Resource resource) {
        return switch (policy.getOwnershipRequirement()) {
            case ANY -> true;
            case OWNER_ONLY -> resource.getCreatedBy().equals(context.getUserId());
            case WORKSPACE_MEMBER -> context.getWorkspaceIds().contains(resource.getWorkspaceId());
        };
    }
    
    private boolean evaluateStatus(Policy policy, TenantContext context, Resource resource) {
        return switch (resource.getStatus()) {
            case DRAFT -> context.getWorkspaceIds().contains(resource.getWorkspaceId());
            case REVIEW -> context.getRoles().contains("EDITOR") || context.getRoles().contains("REVIEWER");
            case PUBLISHED -> true;  // Published content is visible to all tenant members
            case ARCHIVED -> context.isSystemAdmin();
        };
    }
    
    private boolean evaluateClassification(Policy policy, TenantContext context, Resource resource) {
        return switch (resource.getClassification()) {
            case PUBLIC -> true;
            case TENANT -> resource.getTenantId().equals(context.getTenantId());
            case WORKSPACE -> context.getWorkspaceIds().contains(resource.getWorkspaceId());
            case RESTRICTED -> context.getRoles().contains("ADMIN") || context.isSystemAdmin();
        };
    }
    
    private boolean evaluateRole(Policy policy, TenantContext context, Resource resource) {
        if (policy.getRequiredRoles().isEmpty()) return true;
        return context.getRoles().stream().anyMatch(policy.getRequiredRoles()::contains);
    }
}
```

**ABAC policy configuration** (stored in database):

```sql
CREATE TABLE identity_abac_policies (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_name         VARCHAR(200) NOT NULL UNIQUE,
    effect              VARCHAR(10) NOT NULL DEFAULT 'ALLOW',  -- ALLOW, DENY
    
    -- Resource pattern (e.g., 'content:story:*', 'research:collection:*')
    resource_pattern    VARCHAR(500) NOT NULL,
    
    -- Action (e.g., 'read', 'write', 'delete', 'admin')
    action              VARCHAR(50) NOT NULL,
    
    -- ABAC conditions (JSONB — evaluated by the policy engine)
    conditions          JSONB NOT NULL DEFAULT '{}',
    -- Example:
    -- {
    --   "tenant": "match",
    --   "workspace": "member_or_published",
    --   "ownership": "any",
    --   "status": ["PUBLISHED", "REVIEW"],
    --   "classification": ["PUBLIC", "TENANT"],
    --   "roles": ["EDITOR", "REVIEWER"]
    -- }
    
    -- Priority (lower number = higher priority)
    priority            INTEGER NOT NULL DEFAULT 100,
    
    -- Description for audit
    description         TEXT,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

# Alternatives Considered

## Alternative 1: Database per Tenant

**Description**: Each tenant gets their own PostgreSQL database. A routing layer (connection pool or middleware) directs each request to the appropriate database based on the tenant ID extracted from the JWT.

**Advantages**:
- **Strongest isolation**: A bug in one tenant's data cannot affect another tenant's data. Database-level isolation is absolute.
- **Independent backup and recovery**: Each tenant can be backed up and restored independently. A corrupted database for one tenant does not affect others.
- **Independent performance tuning**: Each tenant's database can be tuned independently. A resource-intensive tenant does not degrade performance for other tenants.
- **Simpler compliance**: Meeting data residency requirements (e.g., "tenant data must stay in Indonesia") is straightforward — deploy the database in the required region.
- **No RLS complexity**: No need for Row-Level Security policies. Database-level authentication handles isolation.

**Disadvantages**:
- **Operational nightmare at scale**: 100 tenants = 100 databases to manage, monitor, back up, and tune. Connection pool management becomes complex. Schema migrations must be applied to 100 databases.
- **No cross-tenant queries**: Global knowledge queries (e.g., "find all folklore entities related to Kuntilanak across all tenants") require querying 100 databases and aggregating results. This is impractical for the platform's core value proposition of a shared knowledge graph.
- **Connection overhead**: Each database requires its own connection pool. At 100 tenants × 10 connections = 1,000 connections, PostgreSQL connection management becomes a bottleneck.
- **Schema migration complexity**: A schema change requires running Flyway migrations against 100 databases. A single failed migration blocks the entire release. Rollback is 100× harder.
- **Infrastructure cost**: 100 databases consume more disk space, memory, and CPU than one database with proper indexing. Connection overhead alone can double infrastructure costs.
- **Global knowledge duplication**: Global knowledge must either be duplicated in each tenant's database (storage waste, sync complexity) or accessed through a separate shared database (defeats the purpose of per-tenant databases).
- **Team scalability**: A small team (3–8 engineers) cannot operationally manage 100+ databases. This approach requires dedicated database administration staff.

**Rejection rationale**: Database-per-tenant provides the strongest isolation but at an operational cost that is prohibitive for a small team. The platform's core value proposition — a shared, cross-tenant knowledge graph — is fundamentally incompatible with database-per-tenant isolation. The operational complexity of managing 100+ databases, running migrations across all of them, and maintaining cross-tenant queries makes this approach infeasible.

## Alternative 2: Schema per Tenant

**Description**: All tenants share a single PostgreSQL database, but each tenant has their own schema (e.g., `tenant_abc123.content_stories`, `tenant_def456.content_stories`). A routing layer sets the `search_path` to the appropriate schema based on the tenant ID.

**Advantages**:
- **Good isolation**: Schema-level isolation prevents cross-tenant data access. A query without the correct schema prefix cannot accidentally access another tenant's data.
- **Single database**: Easier to manage than 100 databases. One PostgreSQL instance, one backup strategy, one monitoring setup.
- **Independent migration per tenant**: Each schema can be migrated independently. A failed migration for one tenant does not block others.
- **Clear separation**: Schema names make tenant boundaries explicit in the database. Operators can see which schemas belong to which tenants.

**Disadvantages**:
- **Global knowledge is complex**: Global knowledge must live in a shared schema (e.g., `global.knowledge_folklore`). Queries that join global and tenant data must explicitly reference both schemas. This adds complexity to every cross-tenant query.
- **Schema proliferation**: 100 tenants × 15 tables = 1,500 tables across 100 schemas. PostgreSQL handles this, but tooling (pgAdmin, monitoring, backup scripts) struggles with schema proliferation.
- **Migration coordination**: While migrations can be independent, they must still be tracked and coordinated. A migration that adds a column to `content_stories` must be applied to 100 schemas. Automation is essential but adds complexity.
- **Connection pool management**: Each schema requires the same connection pool configuration. Connection pooling tools (PgBouncer, HikariCP) must be schema-aware.
- **Cross-tenant analytics**: Queries like "how many stories were created across all tenants today?" require querying all 100 schemas and unioning results. This is slow and complex.
- **No workspace-level isolation within schemas**: Workspace isolation still requires `workspace_id` columns and application-layer enforcement. Schema-per-tenant does not eliminate the need for row-level isolation within the tenant.
- **search_path management**: The application must set `search_path` on every connection. A bug in search_path management can expose the wrong tenant's data.
- **Migration automation burden**: A small team must build and maintain migration automation for 100+ schemas. This is a significant engineering investment.

**Rejection rationale**: Schema-per-tenant provides better isolation than shared-schema but introduces significant complexity for global knowledge queries, migration management, and cross-tenant analytics. The operational burden of managing 100+ schemas is not justified when the primary isolation requirement is already met by application-layer ABAC enforcement with RLS as defense-in-depth. The shared-schema approach is simpler and more maintainable for a small team.

## Alternative 3: Hybrid — Shared Schema for Global, Per-Tenant Schema for Private

**Description**: Use a shared schema for global knowledge and cross-tenant data. Use per-tenant schemas for tenant-private data (research collections, annotations, drafts). The application routes queries to the appropriate schema based on data type.

**Advantages**:
- **Best of both worlds**: Global knowledge is easily queried across tenants. Private data has schema-level isolation.
- **Stronger isolation for sensitive data**: Research data, annotations, and drafts are in tenant-specific schemas. A SQL injection in the research module cannot access another tenant's research data.
- **Independent migration for private schemas**: Tenant-private schema migrations can be applied independently. A failed migration for one tenant's research schema does not block others.
- **Clear data classification boundary**: The schema structure makes the data classification explicit. Global = shared schema. Private = tenant schema.

**Disadvantages**:
- **Two routing mechanisms**: The application must determine whether a query targets the shared schema or a tenant-specific schema. This adds complexity to every database operation.
- **Cross-schema queries are complex**: A query that joins global knowledge (shared schema) with tenant annotations (tenant schema) must explicitly reference both schemas. This is error-prone and hard to maintain.
- **Migration complexity doubled**: Two migration strategies: one for the shared schema (single sequence), one for tenant schemas (applied to each tenant). Migration tooling must handle both.
- **Connection pool management**: The application needs connections that can access both the shared schema and the tenant schema. Connection pooling must be schema-aware.
- **Operational complexity**: Operators must understand two isolation models. Debugging data access issues requires checking both schema routing and application-layer ABAC.
- **No clear boundary for "private" data**: Is a draft story "private" (tenant schema) or "content" (shared schema)? The boundary is not always clear, leading to inconsistent data placement.
- **Migration ordering dependencies**: A migration that adds a column to a shared schema table may need to be applied before tenant schema migrations that reference it. This creates ordering dependencies.

**Rejection rationale**: The hybrid approach adds significant complexity (two routing mechanisms, two migration strategies, cross-schema queries) without providing proportional benefits over the shared-schema approach with RLS. The shared-schema approach with application-layer ABAC and RLS defense-in-depth provides adequate isolation for all data types, including sensitive research data. The hybrid approach's complexity is not justified for a small team.

## Alternative 4: Application-Layer Only, No RLS

**Description**: Enforce tenant isolation exclusively at the application layer. No Row-Level Security policies in PostgreSQL. All tenant filtering is done through repository queries and service-layer checks.

**Advantages**:
- **Simplest database setup**: No RLS policies to create, maintain, or debug. No `current_setting` management. No policy performance tuning.
- **No database-side complexity**: All isolation logic is in the application code, which the team already owns and understands.
- **Easier debugging**: Data access issues are debugged in the application layer, not split between application and database policies.
- **No RLS performance impact**: RLS adds query planning overhead. For complex queries with multiple policy checks, this overhead can be significant.
- **Simpler connection pooling**: No need to set session-level parameters (`app.tenant_id`, `app.workspace_ids`) on every connection.

**Disadvantages**:
- **No defense-in-depth**: A bug in application-layer tenant filtering can leak data across tenants. There is no database-level safety net.
- **SQL injection vulnerability**: If a SQL injection vulnerability exists, an attacker can bypass application-layer filtering entirely and access any tenant's data. RLS would prevent this.
- **Direct database access risk**: Operators or scripts that access the database directly (e.g., for data fixes, reporting) bypass application-layer isolation. RLS would enforce isolation even for direct queries.
- **No protection against application bugs**: A missing `WHERE tenant_id = ?` clause in a repository query silently exposes all tenants' data. RLS would block this query.
- **Audit/compliance concerns**: Compliance requirements (e.g., SOC 2, ISO 27001) may require database-level isolation controls. Application-layer only may not satisfy auditors.

**Rejection rationale**: Application-layer enforcement is necessary but not sufficient. RLS provides essential defense-in-depth against application bugs, SQL injection, and direct database access. The performance overhead of RLS is minimal for well-indexed tables and simple policies. The security benefits of defense-in-depth outweigh the additional complexity of maintaining RLS policies.

# Consequences

## Positive

1. **Operational simplicity**: One database, one set of schemas, one migration sequence. A small team can manage the database without dedicated DBA support. Backups, monitoring, and performance tuning are straightforward.

2. **Global knowledge sharing**: Cross-tenant queries are simple SQL queries — no federation, no cross-database joins, no schema routing. The platform's core value proposition (shared knowledge graph) is directly supported by the architecture.

3. **Flexible isolation levels**: Different data types have different isolation requirements. Global knowledge is shared. Tenant content is isolated by `tenant_id`. Research data is isolated by `workspace_id`. The architecture supports all three levels without complexity.

4. **Defense-in-depth**: Three layers of isolation (application-layer ABAC, repository-level tenant filtering, RLS policies) ensure that a single bug cannot cause cross-tenant data leakage.

5. **Workspace-level isolation**: Within a tenant, workspaces provide sub-isolation. Research teams within the same institution cannot see each other's private data unless explicitly shared.

6. **Contribution workflow for global knowledge**: Tenants can contribute to the global knowledge base through a controlled workflow. This enables community-driven knowledge growth while maintaining data quality.

7. **Tenant context propagation through events**: Events carry tenant context, ensuring that AI workers and projection workers enforce tenant isolation. No downstream component can accidentally mix data across tenants.

8. **ABAC enables fine-grained access control**: Beyond tenant isolation, ABAC policies control access based on ownership, content status, classification, and role. This enables complex scenarios like "editors can review drafts from any workspace in the tenant" or "published content is visible to all tenant members."

## Negative

1. **Application-layer enforcement is critical**: Every repository query, every service method, every API endpoint must correctly apply tenant filtering. A missing filter is a data leakage vulnerability. Code reviews must be rigorous.

2. **RLS policy maintenance**: RLS policies must be created for every tenant-scoped table and updated when table structures change. Forgetting to add RLS to a new table creates a gap in defense-in-depth.

3. **Performance overhead of tenant filtering**: Every query includes `WHERE tenant_id = ?` or `WHERE workspace_id IN (?)`. While these are indexed, they add query planning and execution overhead. At 100,000,000 graph relationships, this overhead is non-trivial.

4. **Global knowledge write complexity**: The contribution workflow adds complexity for what should be a simple write operation. System admins can write directly, but tenant contributions require review. This adds latency to knowledge base updates.

5. **Tenant deletion complexity**: Soft-deleting a tenant requires updating RLS policies, preserving data for retention periods, and handling the interaction between archived tenants and global knowledge contributions.

6. **Cross-tenant analytics are limited**: Queries that aggregate across all tenants (e.g., "total stories created this month") require system admin privileges. Regular tenant users cannot see cross-tenant metrics.

7. **Connection pool sizing**: All tenants share the same connection pool. A tenant with high traffic can consume connections needed by other tenants. Connection pool isolation requires separate pools per tenant or connection pool monitoring.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Operational simplicity** | One database, one migration sequence | All tenants affected by database-level issues |
| **Data isolation** | Three layers of defense (ABAC, queries, RLS) | Every query must include tenant filters |
| **Global knowledge sharing** | Simple cross-tenant queries | Contribution workflow adds write complexity |
| **Workspace isolation** | Sub-tenant isolation for research teams | Additional query complexity for workspace scoping |
| **Performance** | Single database with proper indexing | Tenant filtering adds overhead to every query |
| **Security** | Defense-in-depth against data leakage | RLS policy maintenance burden |
| **Scalability** | Scales to 100+ tenants in one database | Connection pool contention at high tenant counts |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Missing tenant filter in repository query** | Medium | Critical — cross-tenant data leakage | Enforce tenant filtering at the repository base class level. Use ArchUnit tests to verify that all repository methods include tenant filters. Run periodic data isolation audits. |
| **RLS policy misconfiguration** | Low | High — data leakage or blocked access | Test RLS policies in CI/CD pipeline. Run integration tests that verify tenant isolation from the database layer. Review RLS policies in code review. |
| **Tenant context propagation failure in async processing** | Medium | Medium — AI worker processes data with wrong tenant context | Validate tenant context in every event handler. Log tenant context mismatches. Implement dead letter queue for events with missing or invalid tenant context. |
| **Connection pool exhaustion by a single tenant** | Low | Medium — degraded performance for all tenants | Implement per-tenant connection pool limits using PgBouncer or application-level connection pool partitioning. Monitor connection usage per tenant. Alert on connection pool contention. |
| **Global knowledge table contention** | Medium | Low — write contention on popular global entities | Global knowledge is read-heavy. Writes are infrequent (contribution workflow). Use READ COMMITTED isolation level. Consider advisory locks for critical write operations. |
| **Workspace membership cache staleness** | Low | Medium — user sees stale workspace permissions | Cache workspace membership with short TTL (60 seconds). Invalidate cache on membership changes. Use database-level RLS as fallback if cache is stale. |
| **ABAC policy evaluation performance** | Medium | Low — increased API latency | Cache ABAC policy evaluation results per user-role-resource combination. Use indexed policy lookup. Evaluate policies asynchronously where possible. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Tenant onboarding misconfiguration** | Medium | Medium — new tenant has incorrect isolation | Automate tenant onboarding with tested scripts. Verify tenant isolation with automated tests after onboarding. Document manual steps for edge cases. |
| **Data migration across tenants** | Low | High — data corruption if migration is incorrect | Data migration across tenants is rare. When required, use a controlled process with review, testing, and rollback capability. Log all cross-tenant data operations. |
| **Audit log tenant context missing** | Medium | Medium — cannot trace data access to tenant | Enforce tenant context in audit log entries. Validate tenant context before writing audit logs. Alert on audit log entries with missing tenant context. |
| **Compliance audit requires per-tenant data export** | Medium | Medium — complex data extraction | Implement per-tenant data export API. Use tenant-scoped queries for export. Test export process regularly. Document data retention and deletion procedures. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Tenant count exceeds 500** | Connection pool contention, query performance degradation | Evaluate read replicas for global knowledge queries. Consider connection pool per tenant group. Evaluate schema-per-tenant migration for high-volume tenants. |
| **Regulatory requirement for data residency** | Must store tenant data in specific geographic regions | Database-per-tenant or schema-per-tenant in region-specific PostgreSQL instances. Global knowledge replicated across regions. This is a significant architectural change. |
| **Tenant requires custom schema extensions** | Shared schema cannot accommodate tenant-specific fields | Use JSONB for extensible fields. Evaluate schema-per-tenant for tenants with custom schema requirements. Document extension patterns. |
| **Merger of two tenants** | Complex data migration | Implement tenant merge workflow. Map source tenant data to target tenant. Handle data conflicts (e.g., both tenants have a story with the same title). |
| **Multi-region deployment** | Global knowledge must be synchronized across regions | Use PostgreSQL logical replication for global knowledge tables. Tenant data stays in region. Cross-region queries use federation or application-level aggregation. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Tenant count exceeds 500**: At this scale, connection pool contention and query performance may require migration to schema-per-tenant or database-per-tenant for high-volume tenants. The shared-schema approach should be re-evaluated.

2. **Data residency requirements emerge**: If regulations require tenant data to be stored in specific geographic regions, the shared-database approach must be revised. Consider region-specific PostgreSQL instances with global knowledge replication.

3. **Tenant-specific schema extensions are required**: If tenants need custom fields or tables that cannot be supported through JSONB, schema-per-tenant may be necessary for those tenants.

4. **Performance degradation due to tenant filtering**: If the overhead of `WHERE tenant_id = ?` on every query becomes a bottleneck at scale, consider partitioning tables by `tenant_id` (PostgreSQL native partitioning) to improve query performance.

5. **New data classification categories emerge**: If new data types require different isolation levels (e.g., "public" data that is visible to unauthenticated users), the data classification model and RLS policies must be updated.

6. **ABAC policy engine becomes a performance bottleneck**: If ABAC policy evaluation adds significant latency to API requests, consider caching policies, moving to a policy-as-code approach (e.g., Open Policy Agent), or simplifying the policy model.

# References

- **Backend Platform PRD §7** — "Multi Tenant Architecture" — Shared Database, Shared Schema, tenant_id + workspace_id isolation.
- **Backend Platform PRD §8** — "Authorization Model" — RBAC + ABAC with Tenant, Workspace, Ownership, Status, Classification dimensions.
- **Backend Platform PRD §12** — "Audit Requirements" — Every business table must contain tenant_id and workspace_id.
- **ADR-001: PostgreSQL as Source of Truth** — Single PostgreSQL database for all operational data.
- **ADR-002: Modular Monolith First** — Shared database across all domain modules.
- **ADR-003: Event-Driven Architecture** — Tenant context propagation through events.
- **ADR-004: Queue-Driven AI Platform** — AI workers and projection workers enforce tenant isolation.
- **PostgreSQL Row-Level Security** — https://www.postgresql.org/docs/18/ddl-rowsecurity.html
- **Weaviate Multi-Tenancy** — https://weaviate.io/developers/weaviate/manage-data/multi-tenancy — Native multi-tenancy support for vector data.
- **ABAC (Attribute-Based Access Control)** — NIST SP 800-162 — Guide to ABAC definition and implementation.
- **Open Policy Agent** — https://www.openpolicyagent.org/ — Policy-as-code engine for ABAC enforcement (future consideration).