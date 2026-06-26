# Deployment & Environment Strategy

## Version 1.0
## Status: Draft

---

# Overview

This document defines the deployment and environment strategy for The Living Atlas platform across four environments: Local, Development, Staging, and Production.

---

# Environment Overview

| Environment | Purpose | Users | Infrastructure | Data |
|-------------|---------|-------|---------------|------|
| **Local** | Developer workstation | 1–5 developers | Docker Compose | Seed data, anonymized |
| **Dev** | Integration testing | 5–10 engineers | Single VM + Docker Compose | Synthetic data |
| **Staging** | Pre-production validation | QA, reviewers | Multi-node (K3s/Docker Swarm) | Anonymized production copy |
| **Production** | Live platform | End users | Kubernetes (future) | Real data |

---

# 1. Local Development Environment

## Prerequisites
- Docker Desktop or Podman
- Java 25 (GraalVM or OpenJDK)
- Python 3.14 + poetry
- Node.js 22 + pnpm
- Make (for build scripts)

## Quick Start
```bash
# Clone and setup
git clone https://github.com/livingatlas/living-atlas.git
cd living-atlas

# Start infrastructure
make infra-up

# Start all services
make dev

# Access
# API Gateway: http://localhost:8080
# PostgreSQL:  localhost:5432
# Neo4j:      http://localhost:7474
# Weaviate:   http://localhost:8081
# Grafana:    http://localhost:3000
```

## Docker Compose Structure
```yaml
# docker-compose.yml
version: "3.9"

services:
  # Data Stores
  postgres:
    image: postgres:18
    ports: ["5432:5432"]
    volumes: ["./data/postgres:/var/lib/postgresql/data"]
    environment:
      POSTGRES_DB: livingatlas
      POSTGRES_USER: livingatlas
      POSTGRES_PASSWORD: livingatlas_dev

  neo4j:
    image: neo4j:5.26
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/livingatlas_dev

  weaviate:
    image: semitechnologies/weaviate:1.37
    ports: ["8081:8080"]
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"

  redpanda:
    image: docker.redpanda.com/redpandadata/redpanda:latest
    ports: ["9092:9092", "9644:9644"]
    # (optional for phase 2)

  # Observability
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    ports: ["4317:4317", "4318:4318"]
    volumes: ["./infrastructure/otel/otel-collector.yml:/etc/otel/config.yaml"]

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes: ["./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml"]

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes: ["./infrastructure/grafana/datasources:/etc/grafana/provisioning/datasources"]

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    volumes: ["./infrastructure/loki/loki.yml:/etc/loki/loki.yml"]

  # Spring Boot Services
  gateway-service:
    build: ./services/gateway-service
    ports: ["8080:8080"]
    depends_on: [postgres, redis]
    environment:
      SPRING_PROFILES_ACTIVE: local

  identity-service:
    build: ./services/identity-service
    ports: ["8081:8080"]
    depends_on: [postgres]
    environment:
      SPRING_PROFILES_ACTIVE: local

  content-service:
    build: ./services/content-service
    ports: ["8082:8080"]
    depends_on: [postgres]
    environment:
      SPRING_PROFILES_ACTIVE: local

  knowledge-service:
    build: ./services/knowledge-service
    ports: ["8083:8080"]
    depends_on: [postgres]
    environment:
      SPRING_PROFILES_ACTIVE: local

  research-service:
    build: ./services/research-service
    ports: ["8084:8080"]
    depends_on: [postgres]
    environment:
      SPRING_PROFILES_ACTIVE: local

  workflow-service:
    build: ./services/workflow-service
    ports: ["8085:8080"]
    depends_on: [postgres]
    environment:
      SPRING_PROFILES_ACTIVE: local

  # AI Platform (Python)
  ingestion-service:
    build: ./ai-platform/ingestion-service
    ports: ["8090:8000"]
    depends_on: [postgres, redpanda]

  extraction-service:
    build: ./ai-platform/extraction-service
    ports: ["8091:8000"]
    depends_on: [postgres, redpanda]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  enrichment-service:
    build: ./ai-platform/enrichment-service
    ports: ["8092:8000"]
    depends_on: [postgres, redpanda]

  embedding-service:
    build: ./ai-platform/embedding-service
    ports: ["8093:8000"]
    depends_on: [postgres, redpanda, weaviate]

  article-service:
    build: ./ai-platform/article-service
    ports: ["8094:8000"]
    depends_on: [postgres, redpanda]

  orchestration-service:
    build: ./ai-platform/orchestration-service
    ports: ["8095:8000"]
    depends_on: [postgres, redpanda]

  # Data Platform
  neo4j-sync:
    build: ./data-platform/neo4j-sync
    depends_on: [postgres, neo4j, redpanda]

  weaviate-sync:
    build: ./data-platform/weaviate-sync
    depends_on: [postgres, weaviate, redpanda]
```

## Local Configuration Profiles

### Spring Boot profile: `local`
```yaml
# application-local.yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/livingatlas
    username: livingatlas
    password: livingatlas_dev
  jpa:
    show-sql: true
    hibernate:
      ddl-auto: update
  kafka:
    bootstrap-servers: localhost:9092
    enabled: false  # Use outbox polling in local

logging:
  level:
    com.livingatlas: DEBUG
```

### Environment Variables
```bash
# .env.local
SPRING_PROFILES_ACTIVE=local
POSTGRES_URL=jdbc:postgresql://localhost:5432/livingatlas
POSTGRES_USER=livingatlas
POSTGRES_PASSWORD=livingatlas_dev
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=livingatlas_dev
WEAVIATE_URL=http://localhost:8081
REDPANDA_BROKERS=localhost:9092
OPENAI_API_KEY=sk-...  # Optional for local testing
ANTHROPIC_API_KEY=sk-ant-...  # Optional for local testing
```

---

# 2. Development Environment

## Infrastructure
- **Hosting**: Single VM (8 CPU, 16 GB RAM, 50 GB SSD)
- **Container Runtime**: Docker Compose (same as local)
- **CI/CD**: GitHub Actions or GitLab CI
- **Database**: Managed PostgreSQL (e.g., Neon, Supabase)
- **Storage**: Managed object storage (S3-compatible)

## Differences from Local
| Aspect | Local | Dev |
|--------|-------|-----|
| Database | Docker volume | Managed PostgreSQL |
| Storage | Local filesystem | S3/MinIO |
| GPUs | Optional (local only) | Not available |
| Monitoring | Basic | Full stack (Grafana, Loki, Tempo) |
| Secrets | .env file | Vault/Secrets Manager |
| TLS | HTTP | HTTPS (self-signed or Let's Encrypt) |

## CI/CD Pipeline
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint Check
        run: make lint
      - name: Type Check
        run: make typecheck

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_DB: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - name: Unit & Integration Tests
        run: make test
      - name: Upload Coverage
        uses: codecov/codecov-action@v3

  build:
    needs: [quality, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker Images
        run: make build
      - name: Push to Registry
        run: make push
        env:
          REGISTRY: ghcr.io/livingatlas

  deploy-dev:
    needs: [build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    steps:
      - name: Deploy to Dev
        run: make deploy-dev
```

---

# 3. Staging Environment

## Infrastructure
- **Hosting**: Multi-node (3 nodes, 16 CPU, 32 GB RAM each)
- **Container Runtime**: K3s or Docker Swarm
- **Database**: Managed PostgreSQL with read replicas
- **Storage**: S3-compatible (MinIO or Cloud)
- **GPU**: 1× GPU node for AI pipeline testing
- **Monitoring**: Full observability stack

## Configuration Differences
| Aspect | Dev | Staging |
|--------|-----|---------|
| Replicas | 1 per service | 2+ per critical service |
| Database | Single instance | Primary + replica |
| Redis/Cache | None | Redis cluster |
| CDN | None | CloudFront/Cloudflare |
| Data | Synthetic | Anonymized production |
| Load Testing | None | Regular load tests |
| TLS | Self-signed | Valid certificate |

## Staging Data Strategy
- Weekly anonymized snapshot from production
- PII fields (email, name) randomized
- Location coordinates obfuscated (city-level)
- All secrets rotated

---

# 4. Production Environment

## Infrastructure (Phase 1)
- **Hosting**: Managed Kubernetes (EKS, AKS, or GKE)
- **Compute**: 
  - API services: 3–5 nodes (8 CPU, 16 GB RAM)
  - AI services: 2–3 GPU nodes (A10G or better)
  - Data stores: Managed services
- **Database**: 
  - PostgreSQL: Managed (RDS, Cloud SQL, or Neon)
  - Neo4j: AuraDB or self-managed
  - Weaviate: Cloud or self-managed
- **Storage**: S3-compatible object storage
- **CDN**: CloudFront, Cloudflare, or Fastly
- **Monitoring**: Grafana Cloud or self-hosted

## High Availability
| Component | Strategy | RTO | RPO |
|-----------|----------|-----|-----|
| PostgreSQL | Point-in-time recovery + read replicas | 1 hour | 5 min |
| Neo4j | Causal clustering | 5 min | 1 min |
| Weaviate | Replication factor 3 | 2 min | 1 min |
| API Services | Horizontal scaling (3+ pods) | 1 min | 0 |
| AI Pipeline | Queue persistence + retry | 5 min | N/A |

## Security Hardening
1. **Network**: Private subnets, security groups, no public DB access
2. **TLS**: TLS 1.3 everywhere, automatic cert renewal
3. **Secrets**: Vault or cloud-native secrets manager
4. **WAF**: Web application firewall (Cloudflare/AWS WAF)
5. **DDoS**: Rate limiting at gateway + CDN
6. **Backup**: Daily automated backups, 30-day retention
7. **Encryption**: AES-256 at rest for all data stores

## Scaling Targets (Production)
| Metric | Target | Scaling Trigger |
|--------|--------|-----------------|
| API requests | 1000 req/s | CPU > 70% |
| Concurrent users | 1000 | Auto-scaling groups |
| Database connections | 200 | Connection pooling |
| AI pipeline jobs | 100/day | Queue depth > 50 |
| Storage | 500 GB+ | Auto-scaling volumes |

---

# 5. Environment Promotion Strategy

## Promotion Flow
```
Developer → Local → Dev → Staging → Production
                ↑
            Feature Branch
                ↓
            Main Branch
```

## Gates
| Gate | Check | Required |
|------|-------|----------|
| Code Review | PR approval + lint | Yes |
| Unit Tests | All pass, >80% coverage | Yes |
| Integration Tests | Service-level tests | Yes |
| Security Scan | Dependency check, SAST | Yes |
| Staging Tests | E2E, load test | Before production |
| Manual Approval | QA + Tech Lead | Production only |

## Rollback Strategy
1. **Immediate**: Revert commit, redeploy (Git revert)
2. **Database**: Point-in-time recovery
3. **Canary**: 10% traffic → 50% → 100% (production only)
4. **Feature flags**: Toggle off problematic features

---

# 6. Makefile Commands

```makefile
# Development
dev              # Start all services (local)
dev-backend      # Start backend services only
dev-frontend     # Start frontend apps only
dev-ai           # Start AI services only

# Infrastructure
infra-up        # Start databases + message queue
infra-down      # Stop infrastructure
infra-reset     # Reset infrastructure (delete data)

# Build
build           # Build all Docker images
build-service   # Build single service (SERVICE=name)

# Test
test            # Run all tests
test-service    # Test single service (SERVICE=name)
test-integration # Run integration tests
test-e2e        # Run end-to-end tests

# Quality
lint            # Run all linters
typecheck       # Run TypeScript type checking
format          # Format code

# Database
db-migrate      # Run migrations
db-rollback     # Rollback last migration
db-seed         # Seed database with test data

# Deployment
deploy-dev      # Deploy to dev environment
deploy-staging  # Deploy to staging environment
deploy-prod     # Deploy to production environment

# Monitoring
logs            # Tail service logs
metrics         # Show service metrics
health          # Check service health

# Utility
clean           # Clean build artifacts
setup           # Initial project setup
update          # Update dependencies
```

---

# 7. Resource Requirements Summary

| Environment | Nodes | CPU Total | RAM Total | Storage | GPU | Monthly Cost (est.) |
|-------------|-------|-----------|-----------|---------|-----|-------------------|
| Local | 1 | 4 cores | 8 GB | 20 GB | Optional | $0 (local) |
| Dev | 1 | 8 cores | 16 GB | 50 GB | No | ~$100–200 |
| Staging | 3 | 48 cores | 96 GB | 200 GB | 1× GPU | ~$500–1000 |
| Production | 8–12 | 128+ cores | 256+ GB | 1 TB+ | 2–3× GPU | ~$3000–8000 |

---

# 8. Monitoring & Alerting by Environment

| Metric | Local | Dev | Staging | Production |
|--------|-------|-----|---------|------------|
| API Latency p95 | Log only | Alert > 1s | Alert > 500ms | Alert > 300ms |
| Error Rate | Log only | Alert > 5% | Alert > 2% | Alert > 1% |
| DB Connections | Log only | Alert > 80% | Alert > 70% | Alert > 60% |
| Disk Usage | N/A | Alert > 80% | Alert > 80% | Alert > 75% |
| Pipeline Failures | N/A | Alert > 20% | Alert > 10% | Alert > 5% |
| Certificate Expiry | N/A | N/A | 30-day warning | 30-day warning |

---

# References

- ADR-020: Deployment and Infrastructure Strategy
- plan.md - Infrastructure
- BACKEND-PRD.md §6 Non Functional Requirements
- ai-platform/PRD.md - AI Platform PRD