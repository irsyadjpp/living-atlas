# ADR-020: Deployment and Infrastructure Strategy

## Status
Accepted

## Context
The platform consists of Spring Boot services, Python AI services, PostgreSQL, Neo4j, Weaviate, and Redpanda. Deployment must support local development, multiple environments, and future Kubernetes migration.

## Decision
We use Docker Compose for local development, with environment-specific configurations for dev/staging/production. Kubernetes manifests are prepared for future migration but not the initial deployment target.

## Rationale
- **Local parity**: Docker Compose provides environment parity with production
- **Simplicity**: No Kubernetes overhead during initial development
- **Migration path**: Docker Compose services map 1:1 to Kubernetes deployments
- **CI/CD**: Same container images promoted across environments

## Environment Strategy
| Environment | Infrastructure | Purpose |
|-------------|---------------|---------|
| Local | Docker Compose | Developer workstation |
| Dev | Single VM + Docker Compose | Integration testing |
| Staging | Multi-node Docker or K3s | Pre-production validation |
| Production | Kubernetes (future) | Live platform |

## Docker Compose Architecture
```yaml
services:
  # Data Stores
  postgres:        # PostgreSQL 18
  neo4j:           # Neo4j 5.26
  weaviate:        # Weaviate 1.37
  redpanda:        # Redpanda (future)

  # Spring Boot Services
  gateway-service:
  identity-service:
  content-service:
  knowledge-service:
  research-service:
  workflow-service:

  # AI Platform (Python)
  ingestion-service:
  extraction-service:
  enrichment-service:
  embedding-service:
  article-service:
  orchestration-service:

  # Observability
  otel-collector:
  prometheus:
  grafana:
  loki:
  tempo:
```

## CI/CD Pipeline
```
Commit → Build Test → Container Build → Dev Deploy → Staging → Production
   ↓          ↓             ↓               ↓          ↓          ↓
  Lint     Unit +        Docker         Docker       K8s        K8s
  Check    Integrate     Build         Compose     (future)   (future)
```

## Resource Requirements (per environment)
| Environment | CPU | RAM | Storage | Services |
|-------------|-----|-----|---------|----------|
| Local | 4 cores | 8 GB | 20 GB | All (reduced replicas) |
| Dev | 8 cores | 16 GB | 50 GB | All (single replica) |
| Staging | 16 cores | 32 GB | 100 GB | All (HA database) |
| Production | 32+ cores | 64+ GB | 500+ GB | All (HA, scaled) |

## References
- plan.md - Infrastructure
- BACKEND-PRD.md §6 Non Functional Requirements