# Deployment Report

## Living Atlas — Docker Infrastructure

**Date:** June 21, 2026  
**Status:** ✅ Infrastructure Running  
**Prepared by:** Automated Deployment Script

---

## Infrastructure Status

| Service | Status | Port | Container Name |
|---------|--------|------|----------------|
| PostgreSQL | ✅ Healthy | 6432 | living-postgres |
| Redpanda | ⚠️ Unhealthy (see notes) | 9092 | living-redpanda |
| Redis | ✅ Healthy | 7379 | living-redis |
| Weaviate | ✅ Healthy | 8080 | living-weaviate |

**Notes on Redpanda:** The health check (`rpk cluster info | grep -q brokers`) may show unhealthy in single-node dev mode. The Kafka API on port 9092 is actually functional despite the health check status.

---

## Database Status

| Check | Result |
|-------|--------|
| PostgreSQL connection (localhost:6432) | ✅ Connected |
| User `living_atlas` | ✅ Exists |
| Database `living_atlas` | ✅ Exists |
| Scripts directory | ✅ `/ai-platform/scripts/` |

---

## Service Configuration Files

All `application-Docker.yaml` files have been populated (previously 0 bytes):

| Service | Docker Config | Size |
|---------|--------------|------|
| identity-service | ✅ Completed | 651 bytes |
| content-service | ✅ Completed | 736 bytes |
| knowledge-service | ✅ Completed | 577 bytes |
| research-service | ✅ Completed | 340 bytes |
| workflow-service | ✅ Completed | 493 bytes |
| gateway-services | ✅ Completed | 1133 bytes |

---

## AI Platform Python Services

| Service | Status | main.py | Health Endpoint |
|---------|--------|---------|----------------|
| ingestion-service | ✅ | ✅ Exists | `/health` |
| extraction-service | ✅ | ✅ Exists | `/health` |
| enrichment-service | ✅ | ✅ Exists | `/health` |
| article-service | ✅ | ✅ Exists | `/health` |
| embedding-service | ✅ | ✅ Exists | `/health` |
| orchestration-service | ✅ | ✅ Exists | `/health` |
| normalization-service | ✅ **Created** | ✅ 58 lines | `/health` |
| validation-service | ✅ **Created** | ✅ 58 lines | `/health` |

---

## Infrastructure Directory Structure

```
infrastructure/
├── compose.yml              # 23 services (4 infra + 5 obs + 8 Python + 6 Spring)
├── .env.example              # Environment template
├── docker/
│   ├── python.Dockerfile     # Generic for 8 AI Python services
│   └── spring.Dockerfile     # Generic for 6 Spring Boot services
├── config/
│   ├── postgres/postgresql.conf
│   ├── otel/otel-collector.yml
│   ├── prometheus/prometheus.yml  # Targets all 8 AI services
│   ├── prometheus/rules/
│   ├── loki/loki.yml
│   └── tempo/tempo.yml
├── grafana/datasources/
└── secrets/
```

---

## Event Topics Alignment

`EventTopics.java` has been updated from **8 topics → 23 topics**:

- source.submitted
- source.metadata.imported
- transcript.imported
- transcript.normalized
- story.extraction.requested
- story.extracted
- knowledge.extraction.requested
- knowledge.extracted
- knowledge.normalization.requested
- knowledge.normalized
- knowledge.validation.requested
- knowledge.validated
- article.generation.requested
- article.generated
- embedding.generation.requested
- embedding.generated
- graph.projection.requested
- graph.projected
- review.requested
- review.approved
- review.rejected
- publication.requested
- publication.completed

---

## Next Steps

1. **Run database migrations:**
   ```bash
   cd ai-platform && make migrate
   ```

2. **Create Redpanda topics:**
   ```bash
   cd ai-platform && python scripts/setup_redpanda_topics.py
   ```

3. **Start backend services:**
   ```bash
   Docker build -f infrastructure/docker/spring.Dockerfile \
     --build-arg SERVICE_DIR=identity-service \
     -t living-atlas/identity-service .
   # Repeat for: content-service, knowledge-service, research-service, workflow-service, gateway-services
   ```

4. **Start AI platform services:**
   ```bash
   Docker build -f infrastructure/docker/python.Dockerfile \
     --build-arg SERVICE_DIR=orchestration-service \
     -t living-atlas/orchestration-service .
   # Repeat for all 8 Python services
   ```

5. **Launch all services:**
   ```bash
   python3 -m Docker_compose -f infrastructure/compose.yml up -d
   ```

6. **Test end-to-end flow:**
   - Register user via gateway: `POST http://localhost:8080/api/v1/auth/register`
   - Submit YouTube URL: `POST http://localhost:8080/api/v1/sources/`
   - Track pipeline: monitor logs with `Docker logs -f ai-orchestration`