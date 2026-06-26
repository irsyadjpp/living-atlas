# ADR-007: Multi-Tenancy Strategy

## Status
Accepted

## Context
The platform serves multiple tenant types (individual, research, publisher, production house, university, government). Each tenant requires data isolation while maintaining a shared knowledge graph for global folklore/culture entities.

## Decision
We will implement a hybrid multi-tenancy model: **shared schema with row-level tenant isolation** for global knowledge, and **tenant-scoped schemas** for private research data.

## Rationale
- **Global Knowledge**: Folklore, culture, themes, motifs are shared across all tenants
- **Private Data**: Workspaces, collections, annotations must be isolated
- **Complexity**: Separate databases per tenant is operationally prohibitive at current scale
- **Migration path**: Row-level isolation can migrate to schema-per-tenant if needed

## Tenant Data Classification

| Data Type | Isolation Level | Tenant ID Column | Example |
|-----------|----------------|-----------------|---------|
| Global Knowledge | Shared | NULL | Folklore entities, themes, motifs |
| Tenant Content | Row-level | tenant_id | Stories, articles created by tenant |
| Private Research | Row-level | tenant_id + workspace_id | Collections, annotations |
| User Identity | Global | NULL | Users (user-tenant mapping separate) |
| Governance | Row-level | tenant_id | Audit logs, reviews |

## Implementation
1. Every resource table includes `tenant_id UUID` or NULL for global data
2. ABAC policies enforce tenant-scoped access at the application layer
3. RLS (Row-Level Security) in PostgreSQL as defense-in-depth
4. Workspace isolation enforced through composite tenant_id + workspace_id

## RLS Policy Example
```sql
CREATE POLICY tenant_isolation ON content.stories
USING (tenant_id = current_setting('app.current_tenant_id')::UUID OR tenant_id IS NULL);
```

## References
- ddl.md - Tenant Domain Schema
- BACKEND-PRD.md §3 Identity Domain