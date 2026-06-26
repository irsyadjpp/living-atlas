# ADR-003: PostgreSQL as Source of Truth

## Status
Accepted

## Context
The platform uses PostgreSQL, Neo4j (knowledge graph), and Weaviate (vector search). Without clear ownership rules, teams may write directly to graph/vector databases, causing data inconsistency and provenance loss.

## Decision
PostgreSQL is the single source of truth for all operational data. Neo4j and Weaviate are read-only projections updated exclusively via event-driven sync from PostgreSQL.

## Rationale
- **Data integrity**: Single authoritative store prevents split-brain scenarios
- **Provenance**: All data changes traced through PostgreSQL audit logs
- **Recovery**: Graph/vector databases can be rebuilt from PostgreSQL at any time
- **Consistency**: Eventual consistency is acceptable for projections

## Consequences
### Positive
- Clear data ownership boundary
- Rebuildable graph and vector stores
- Simplified backup strategy (PostgreSQL-centric)

### Negative
- Eventual consistency between stores
- Sync failures must be monitored and retried
- Additional latency for graph/vector availability

## Rules
1. **No direct writes to Neo4j** outside neo4j-sync service
2. **No direct writes to Weaviate** outside weaviate-sync service
3. All projection updates must use idempotent event handlers
4. Projection rebuild jobs must be testable and repeatable

## Architecture
```
PostgreSQL (Source of Truth)
    ↓ Domain Events (Transactional Outbox)
    ↓
Neo4j Sync Service → Neo4j (Read-only Graph)
Weaviate Sync Service → Weaviate (Read-only Vector)
```

## References
- plan.md - Database Ownership
- ddl.md - Schema Design Principles
- BACKEND-PRD.md §2.4 PostgreSQL Is Source of Truth