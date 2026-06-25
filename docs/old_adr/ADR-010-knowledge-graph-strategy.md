# ADR-010: Knowledge Graph Strategy

## Status
Accepted

## Context
The platform needs to represent complex relationships between folklore entities, stories, themes, motifs, cultures, and regions. Relational databases handle structured data well but struggle with graph traversals (e.g., "find all entities connected to Kuntilanak within 3 hops").

## Decision
We use Neo4j as a read-only graph projection for relationship-heavy queries, sourced exclusively from PostgreSQL via event-driven synchronization.

## Rationale
- **Relationship complexity**: Graph queries for folklore/culture relationships are inherently graph problems
- **Performance**: Multi-hop traversals in PostgreSQL require recursive CTEs with poor performance
- **Source of Truth**: PostgreSQL remains authoritative; Neo4j is a derived projection
- **Rebuildable**: Neo4j can be rebuilt from PostgreSQL at any time

## Graph Model
```
(:Entity {type: "folklore", name: "Kuntilanak"})
  -[:APPEARS_IN]->(:Location {name: "Pontianak"})
  -[:ASSOCIATED_WITH]->(:Culture {name: "Dayak"})
  -[:HAS_BELIEF]->(:Belief {name: "Ancestral Spirit"})

(:Story {title: "Malam Jumat"})
  -[:FEATURES]->(:Entity {name: "Kuntilanak"})
  -[:HAS_THEME]->(:Theme {name: "Fear"})
  -[:HAS_MOTIF]->(:Motif {name: "Mysterious Voice"})
```

## Sync Strategy
1. Domain event published from PostgreSQL (e.g., `KnowledgeObjectCreated`)
2. neo4j-sync service consumes event
3. Sync service transforms relational data to graph model
4. Upserts into Neo4j (idempotent by source UUID)
5. Full rebuild possible via batch job

## Forbidden
- Direct writes to Neo4j from any service except neo4j-sync
- Using Neo4j as primary data store
- Transactional dependency on Neo4j availability

## References
- plan.md - Data Platform
- ddl.md - Knowledge & Culture Domain
- BACKEND-PRD.md §2.4 PostgreSQL Is Source of Truth