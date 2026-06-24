# Multi-Tenant & ABAC Design Document

## Version 1.0
## Status: Draft

---

# Overview

This document details the multi-tenancy and Attribute-Based Access Control (ABAC) design for The Living Atlas platform. The combination of multi-tenancy and fine-grained ABAC enables researchers, publishers, universities, and production houses to share a global knowledge base while maintaining strict data isolation.

---

# Part 1: Multi-Tenancy Design

## 1.1 Tenant Model

### Tenant Types
| Type | Description | Use Case |
|------|-------------|----------|
| `individual` | Single researcher/creator | Personal workspace |
| `research` | Research organization | Collaborative research |
| `publisher` | Content publisher | Editorial workflows |
| `production_house` | Film/TV production | Adaptation scouting |
| `university` | Academic institution | Research & education |
| `government` | Government agency | Cultural preservation |

### Tenant Hierarchy
```
Platform (Super Admin)
├── Tenant A (Publisher)
│   ├── Workspace 1 (Mystery Podcast)
│   ├── Workspace 2 (Folklore Series)
│   └── Workspace 3 (Research)
├── Tenant B (University)
│   ├── Workspace 1 (Anthropology Dept)
│   └── Workspace 2 (Cultural Studies)
└── Tenant C (Individual)
    └── Workspace 1 (Personal Research)
```

## 1.2 Data Isolation Strategy

### Shared Global Data
- Knowledge objects (folklore entities, themes, motifs)
- Culture data (cultures, regions, beliefs, traditions)
- Public stories and articles
- Reference taxonomy (entity types, evidence levels)

### Tenant-Isolated Data
- Private stories and articles (draft/review states)
- Research collections and annotations
- User preferences and saved queries
- Workflow states and reviews
- API keys and webhook configurations

### Isolation Enforcement
1. **Application layer**: Every query includes `tenant_id` filter
2. **Database layer**: Row-Level Security (RLS) as defense-in-depth
3. **API layer**: Gateway validates tenant context from JWT
4. **Event layer**: Events carry tenant context for downstream processing

## 1.3 Workspace Isolation

Workspaces provide sub-tenant isolation for team/project-level boundaries.

```
Tenant: Research Lab
├── Workspace: "Folklore of Sumatra"
│   └── Collections, annotations, notes (scoped)
├── Workspace: "Mystery Podcast Archive"
│   └── Collections, annotations, notes (scoped)
└── Workspace: "Cultural Evolution Study"
    └── Collections, annotations, notes (scoped)
```

### Workspace Visibility
| Visibility | Description | Access |
|------------|-------------|--------|
| `private` | Only workspace members | Explicit membership |
| `team` | All tenant members | Tenant-wide access |
| `public` | Anyone within platform | Platform-wide access |

## 1.4 Cross-Tenant Data Sharing

Global knowledge objects are visible across tenants. Tenant-specific data can be shared via:

1. **Publication**: Story published → globally visible
2. **Explicit share**: Collection shared with other tenant
3. **Citation**: Knowledge object referenced from public story

---

# Part 2: ABAC Design

## 2.1 ABAC vs RBAC

| Aspect | RBAC | ABAC |
|--------|------|------|
| Granularity | Coarse (role-based) | Fine-grained (attribute-based) |
| Flexibility | Static | Dynamic |
| Context | Limited to role | Rich context (resource, environment) |
| Maintenance | Role explosion | Policy-driven |
| Use Case | Simple CRUD | Knowledge platform with multi-tenancy |

**Decision**: ABAC with RBAC as foundation. Roles provide base permissions; ABAC policies refine access based on attributes.

## 2.2 ABAC Architecture

```
Subject (User)
  ├── id, email, username
  ├── roles: [researcher, editor]
  ├── tenant_id: uuid
  └── workspace_memberships: [uuid, uuid]

Action
  ├── create, read, update, delete
  ├── approve, reject, publish, archive
  └── share, export, annotate

Resource
  ├── type: story, article, knowledge_object, collection
  ├── id, tenant_id, workspace_id
  ├── status: draft, published, archived
  ├── owner_id: uuid
  ├── classification: public, sensitive, confidential
  └── metadata: {region, culture_id, ...}

Environment
  ├── ip_address, device_type
  ├── time_of_day
  └── location_sensitivity_requested
```

## 2.3 Policy Definition

### Policy Structure
```json
{
  "policyId": "uuid",
  "code": "researcher_view_published_knowledge",
  "name": "Researcher can view published knowledge objects",
  "effect": "ALLOW",
  "rules": [
    {
      "condition": "subject.role == 'researcher'",
      "condition": "resource.type == 'knowledge_object'",
      "condition": "resource.status == 'published'",
      "condition": "resource.tenant_id == subject.tenant_id || resource.tenant_id IS NULL"
    }
  ]
}
```

### Built-in Policies

#### System Admin
```
Subject.role == 'system_admin' → ALLOW (*)
```

#### Tenant Admin
```
Subject.role == 'tenant_admin' AND
Resource.tenant_id == Subject.tenant_id → ALLOW (*)
```

#### Researcher
```
Subject.role == 'researcher' AND
Resource.tenant_id == Subject.tenant_id AND
Resource.status != 'archived' → ALLOW (read)

Subject.role == 'researcher' AND
Resource.tenant_id == Subject.tenant_id AND
Resource.type == 'collection' → ALLOW (create, read, update, delete)
```

#### Editor
```
Subject.role == 'editor' AND
Resource.tenant_id == Subject.tenant_id AND
Resource.type == 'story' AND
Resource.status == 'draft' → ALLOW (create, read, update)

Subject.role == 'editor' AND
Resource.tenant_id == Subject.tenant_id AND
Resource.type == 'story' → ALLOW (read)
```

#### Reviewer
```
Subject.role == 'reviewer' AND
Resource.tenant_id == Subject.tenant_id AND
Resource.type == 'story' AND
Resource.status == 'review' → ALLOW (read, approve, reject)
```

#### Creator
```
Subject.role == 'creator' AND
Resource.tenant_id == Subject.tenant_id AND
Resource.owner_id == Subject.id → ALLOW (create, read, update)

Subject.role == 'creator' AND
Resource.status == 'published' → ALLOW (read)
```

## 2.4 Advanced ABAC Rules

### Sensitive Location Access
```
Subject.role IN ('researcher', 'editor') AND
Resource.type == 'location' AND
Resource.is_sensitive == TRUE AND
Subject.has_sensitive_location_permission == TRUE → ALLOW (read_coordinates)

Subject.role IN ('researcher', 'editor', 'reader') AND
Resource.type == 'location' → ALLOW (read_public_region)
```

### AI Extraction Review
```
Subject.role == 'reviewer' AND
Resource.type == 'claim' AND
Resource.confidence_score < 0.9 → ALLOW (review, verify, reject)
```

### Cross-Tenant Knowledge Access
```
Subject.role IN ('researcher', 'editor') AND
Resource.type == 'knowledge_object' AND
Resource.tenant_id IS NULL → ALLOW (read)

Subject.role IN ('researcher', 'editor') AND
Resource.type == 'knowledge_object' AND
Resource.status == 'published' → ALLOW (read)
```

## 2.5 Policy Evaluation Flow

```
Request → Gateway → Extract Subject Attributes
                      ↓
                  Get Resource Attributes
                      ↓
                  Load Applicable Policies
                      ↓
                  Evaluate Rules (ALLOW/DENY)
                      ↓
                  DENY by default? → DENY
                  ALLOW first match → ALLOW
                      ↓
                  Return Decision
```

### Evaluation Algorithm
1. Collect all policies where resource type matches
2. Sort by priority (most specific first)
3. Evaluate each rule expression
4. First match wins (ALLOW or DENY)
5. Default: DENY (explicit deny unless allowed)

---

# Part 3: Implementation

## 3.1 Database Schema

```sql
-- ABAC Policies
CREATE TABLE iam.policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    effect VARCHAR(20) NOT NULL CHECK (effect IN ('ALLOW', 'DENY')),
    description TEXT,
    priority INTEGER NOT NULL DEFAULT 100,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Policy Rules
CREATE TABLE iam.policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES iam.policies(id),
    rule_order INTEGER NOT NULL,
    rule_expression JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Example rule_expression:
{
  "effect": "ALLOW",
  "conditions": {
    "subject.role": {"eq": "researcher"},
    "resource.type": {"eq": "knowledge_object"},
    "resource.status": {"eq": "published"},
    "resource.tenant_id": {
      "any_of": ["subject.tenant_id", null]
    }
  }
}
```

## 3.2 Policy Enforcement

### API Layer (Spring Boot)
```java
@PreAuthorize("@abacPolicy.evaluate('story', 'read', #storyId)")
public StoryDto getStory(String storyId) {
    // Implementation
}
```

### Service Layer
```java
public class AbacPolicyEvaluator {
    
    public boolean evaluate(String resourceType, String action, String resourceId) {
        Subject subject = SecurityContext.getCurrentSubject();
        Resource resource = resourceService.getResource(resourceType, resourceId);
        Environment env = EnvironmentContext.getCurrent();
        
        List<Policy> policies = policyRepository.findByResourceType(resourceType);
        return evaluatePolicies(subject, resource, env, policies);
    }
}
```

### Database Layer (RLS)
```sql
CREATE POLICY tenant_isolation ON content.stories
USING (
    tenant_id = current_setting('app.current_tenant_id')::UUID 
    OR tenant_id IS NULL
    OR EXISTS (
        SELECT 1 FROM iam.user_roles ur
        WHERE ur.user_id = current_setting('app.current_user_id')::UUID
        AND ur.role_id IN (SELECT id FROM iam.roles WHERE code = 'system_admin')
    )
);
```

## 3.3 JWT Claims

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "roles": ["researcher", "editor"],
  "tenant_id": "tenant-uuid",
  "workspaces": ["ws-1", "ws-2"],
  "permissions": [
    "story:read",
    "story:create",
    "knowledge_object:read",
    "collection:create"
  ],
  "attributes": {
    "has_sensitive_location_permission": false,
    "max_confidence_threshold": 0.9
  },
  "iat": 1624168800,
  "exp": 1624169700
}
```

---

# Part 4: Audit & Compliance

## 4.1 Access Logging

Every ABAC decision is logged:

```sql
CREATE TABLE governance.access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    tenant_id UUID,
    action VARCHAR(100),
    resource_type VARCHAR(100),
    resource_id UUID,
    decision VARCHAR(10),  -- ALLOW / DENY
    policy_id UUID,
    policy_code VARCHAR(255),
    reason TEXT,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE(created_at);
```

## 4.2 Deny Audit

Denied access attempts are flagged for review:
- Threshold: 10 denied attempts in 5 minutes → rate limit
- Repeated denied access to sensitive resources → alert admin

---

# References

- ADR-007: Multi-Tenancy Strategy
- ADR-016: Security Architecture
- ddl.md - IAM Domain, ABAC Domain
- BACKEND-PRD.md §3 Identity Domain