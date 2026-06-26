# Docker Setup Strategy

## 📋 Overview

All infrastructure and service containers run via Docker Compose using the root-level `infrastructure/` directory. This strategy supports both AI Platform (Python) and Backend (Spring Boot) services in a single unified deployment.

---

## 🎯 Architecture

### Single Compose Deployment

```
infrastructure/
├── compose.yml              # Main Docker Compose file (24 services)
├── .env.example              # Environment variable template
├── docker/
│   ├── python.Dockerfile     # Generic Dockerfile for 8 AI Python services
│   └── spring.Dockerfile     # Generic Dockerfile for 6 Spring Boot services
├── config/
│   ├── postgres/             # PostgreSQL configuration
│   ├── redpanda/             # Redpanda configuration
│   ├── redis/                # Redis configuration
│   ├── weaviate/             # Weaviate configuration
│   ├── otel/                 # OpenTelemetry collector configuration
│   ├── prometheus/           # Prometheus config + alert rules
│   ├── loki/                 # Loki log aggregation config
│   └── tempo/                # Tempo tracing config
├── grafana/
│   ├── datasources/          # Grafana datasource provisioning
│   └── dashboards/           # Grafana dashboard JSON files
└── secrets/                  # GCP credentials (manual)
```

---

## 🚀 Quick Start

### 1. Copy Environment File

```bash
cp infrastructure/.env.example infrastructure/.env
# Edit .env with your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY)
```

### 2. Start All Services

```bash
# From ai-platform/
cd ai-platform && make dev

# Or directly from root:
Docker-compose -f infrastructure/compose.yml up -d
```

### 3. Start Only Infrastructure (Database + Queue)

```bash
cd ai-platform && make dev-db
```

### 4. Stop Everything

```bash
cd ai-platform && make clean
```

---

## 🔌 Port Mapping

| Service | Internal Port | Host Port | Container Name |
|---------|---------------|-----------|----------------|
| PostgreSQL | 5432 | **6432** | living-postgres |
| Redpanda (Kafka) | 9092 | **9092** | living-redpanda |
| Redis | 6379 | **7379** | living-redis |
| Weaviate | 8080 | **8080** | living-weaviate |
| Grafana | 3000 | **3000** | living-grafana |
| Prometheus | 9090 | **9090** | living-prometheus |
| Loki | 3100 | **3100** | living-loki |
| Tempo | 3200 | **3200** | living-tempo |
| OTEL Collector | 4317 | **4317** | living-otel |

### AI Platform (Python) Services

| Service | Port | Container Name | Dockerfile |
|---------|------|----------------|------------|
| ingestion-service | **8001** | ai-ingestion | python.Dockerfile |
| extraction-service | **8002** | ai-extraction | python.Dockerfile |
| normalization-service | **8003** | ai-normalization | python.Dockerfile |
| validation-service | **8004** | ai-validation | python.Dockerfile |
| enrichment-service | **8005** | ai-enrichment | python.Dockerfile |
| article-service | **8006** | ai-article | python.Dockerfile |
| embedding-service | **8007** | ai-embedding | python.Dockerfile |
| orchestration-service | **8008** | ai-orchestration | python.Dockerfile |

### Backend (Spring Boot) Services

| Service | Port | Container Name | Dockerfile |
|---------|------|----------------|------------|
| identity-service | **8081** | svc-identity | spring.Dockerfile |
| content-service | **8082** | svc-content | spring.Dockerfile |
| knowledge-service | **8083** | svc-knowledge | spring.Dockerfile |
| research-service | **8084** | svc-research | spring.Dockerfile |
| workflow-service | **8085** | svc-workflow | spring.Dockerfile |
| gateway-services | **8080** | svc-gateway | spring.Dockerfile |

---

## 🐳 Dockerfiles Overview

### python.Dockerfile

**Location:** `infrastructure/docker/python.Dockerfile`

**Usage:**
```bash
Docker build -f infrastructure/docker/python.Dockerfile \
  --build-arg SERVICE_DIR=ingestion-service \
  -t living-atlas/ingestion-service .
```

**Supports:** ingestion-service, extraction-service, normalization-service, validation-service, enrichment-service, article-service, embedding-service, orchestration-service

### spring.Dockerfile

**Location:** `infrastructure/docker/spring.Dockerfile`

**Usage:**
```bash
Docker build -f infrastructure/docker/spring.Dockerfile \
  --build-arg SERVICE_DIR=content-service \
  -t living-atlas/content-service .
```

**Supports:** identity-service, content-service, knowledge-service, research-service, workflow-service, gateway-services

---

## 📁 Volume Structure

Docker volumes are managed automatically by compose:
```
postgres_data   → /var/lib/docker/volumes/postgres_data
redpanda_data   → /var/lib/docker/volumes/redpanda_data
redis_data      → /var/lib/docker/volumes/redis_data
weaviate_data   → /var/lib/docker/volumes/weaviate_data
prometheus_data → /var/lib/docker/volumes/prometheus_data
grafana_data    → /var/lib/docker/volumes/grafana_data
loki_data       → /var/lib/docker/volumes/loki_data
tempo_data      → /var/lib/docker/volumes/tempo_data
```

For persistent local storage, volumes can be mapped to host directories:
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: /data/pod1/postgres
      o: bind
```

---

## 🔐 Credentials

### Default Development Credentials

```
PostgreSQL:
  User: living_atlas
  Password: living_atlas
  Database: living_atlas
  Host: localhost:6432

Redpanda:
  Port: 9092 (Kafka API)
  No authentication (dev mode)

Redis:
  Host: localhost:7379
  No authentication

Grafana:
  User: admin
  Password: admin
  URL: http://localhost:3000

Prometheus:
  URL: http://localhost:9090

Weaviate:
  URL: http://localhost:8080
```

---

## 🔧 Configuration Files

| Component | Config Path | Notes |
|-----------|-------------|-------|
| PostgreSQL | `infrastructure/config/postgres/postgresql.conf` | Tuned for development |
| Prometheus | `infrastructure/config/prometheus/prometheus.yml` | Scrapes all 8 AI services |
| Prometheus Rules | `infrastructure/config/prometheus/rules/ai_platform_alerts.yml` | Alert rules |
| Grafana Datasources | `infrastructure/grafana/datasources/datasources.yml` | Prometheus + Loki + Tempo |
| Loki | `infrastructure/config/loki/loki.yml` | Log aggregation |
| Tempo | `infrastructure/config/tempo/tempo.yml` | Distributed tracing |
| OTEL Collector | `infrastructure/config/otel/otel-collector.yml` | Trace collection |
| Environment | `infrastructure/.env` | API keys, passwords (create from .env.example) |

---

## 📊 Monitoring Stack

| Tool | Purpose | URL |
|------|---------|-----|
| **Grafana** | Visualization | http://localhost:3000 |
| **Prometheus** | Metrics | http://localhost:9090 |
| **Loki** | Logs | http://localhost:3100 |
| **Tempo** | Traces | http://localhost:3200 |

All datasources are pre-configured in Grafana. The stack provides:
- Service metrics (request rate, latency, errors)
- Consumer lag for Redpanda topics
- AI provider metrics (token usage, cost, latency)
- Pipeline job metrics
- Distributed tracing for pipeline flows

---

## 🔍 Troubleshooting

### Check Container Status
```bash
Docker ps --all
Docker logs living-postgres
Docker logs ai-ingestion
```

### Check Redpanda Topics
```bash
Docker exec living-redpanda rpk topic list
```

### Run Migrations
```bash
cd ai-platform && make migrate
```

### Fix Volume Permissions
```bash
sudo chown -R 1000:1000 /data/pod1/postgres
```

---

## 🚦 Best Practices

### Development Workflow
```bash
# 1. Start infrastructure
cd ai-platform && make dev-db

# 2. Run migrations
cd ai-platform && make migrate

# 3. Setup topics
cd ai-platform && python scripts/setup_redpanda_topics.py

# 4. Start services
cd ai-platform && make dev
```

### Testing Individual Services
```bash
# Test a specific service
Docker build -f infrastructure/docker/python.Dockerfile \
  --build-arg SERVICE_DIR=normalization-service \
  -t living-atlas/normalization-service .

Docker run --rm -p 8003:8000 living-atlas/normalization-service
```

---

## 📝 Summary

✅ **Single Compose File** — All 24 services in one deployment
✅ **Generic Dockerfiles** — python.Dockerfile for 8 services, spring.Dockerfile for 6 services
✅ **Centralized Config** — All infrastructure configs in `infrastructure/config/`
✅ **Observability Ready** — Prometheus + Grafana + Loki + Tempo pre-configured
✅ **Health Checks** — Every service has health checks + depends_on
✅ **Non-Root** — All containers run as non-root user
✅ **Port Isolation** — Clear port mapping per service type