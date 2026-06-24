#!/bin/bash

# AI Platform Infrastructure Deployment Script
# Deploys core infrastructure services using podman

set -e

echo "=========================================="
echo "Deploying AI Platform Infrastructure"
echo "=========================================="

# Load environment variables
if [ -f scripts/env_ai_platform.sh ]; then
    source scripts/env_ai_platform.sh
else
    echo "❌ Environment file not found: scripts/env_ai_platform.sh"
    exit 1
fi

# Check if pod exists
if ! podman pod exists living-atlas-ai-platform; then
    echo "❌ Pod 'living-atlas-ai-platform' does not exist"
    echo "Run: ./scripts/create_ai_platform_pod.sh"
    exit 1
fi

# ============================================================
# Data Infrastructure
# ============================================================

echo "📦 Deploying PostgreSQL..."
podman run -d \
    --name ai-platform-postgres \
    --pod living-atlas-ai-platform \
    -e POSTGRES_DB=$LA_PG_DATABASE \
    -e POSTGRES_USER=$LA_PG_USER \
    -e POSTGRES_PASSWORD=$LA_PG_PASSWORD \
    -e POSTGRES_INITDB_ARGS="--data-checksums" \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/postgres:/var/lib/postgresql:Z \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/postgres/postgresql.conf:/etc/postgresql/postgresql.conf:ro,Z \
    docker.io/pgvector/pgvector:pg18 \
    postgres -c config_file=/etc/postgresql/postgresql.conf

echo "📦 Deploying Redis..."
podman run -d \
    --name ai-platform-redis \
    --pod living-atlas-ai-platform \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/redis:/data:Z \
    docker.io/library/redis:7-alpine

echo "📦 Deploying RabbitMQ..."
podman run -d \
    --name ai-platform-rabbitmq \
    --pod living-atlas-ai-platform \
    -e RABBITMQ_DEFAULT_USER=$LA_RABBITMQ_USER \
    -e RABBITMQ_DEFAULT_PASS=$LA_RABBITMQ_PASSWORD \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/rabbitmq:/var/lib/rabbitmq:Z \ \
    docker.io/library/rabbitmq:3-management-alpine

echo "📦 Deploying MinIO..."
podman run -d \
    --name ai-platform-minio \
    --pod living-atlas-ai-platform \
    -e MINIO_ROOT_USER=$LA_MINIO_ACCESS_KEY \
    -e MINIO_ROOT_PASSWORD=$LA_MINIO_SECRET_KEY \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/minio:/data:Z \
    docker.io/minio/minio:latest \
    server /data --console-address ":9001"

# ============================================================
# Vector Database
# ============================================================

echo "📦 Deploying Weaviate..."
podman run -d \
    --name ai-platform-weaviate \
    --pod living-atlas-ai-platform \
    -e QUERY_DEFAULTS_LIMIT=25 \
    -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED="true" \
    -e PERSISTENCE_DATA_PATH="/var/lib/weaviate" \
    -e DEFAULT_VECTORIZER_MODULE="none" \
    -e CLUSTER_HOSTNAME="node1" \
    -e LOG_LEVEL="error" \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/weaviate:/var/lib/weaviate:Z \
    docker.io/semitechnologies/weaviate:latest

# ============================================================
# Orchestration
# ============================================================

echo "📦 Deploying Prefect Server..."
podman run -d \
    --name ai-platform-prefect \
    --pod living-atlas-ai-platform \
    -e PREFECT_UI_URL="http://localhost:4200/api" \
    -e PREFECT_API_URL="http://localhost:4200/api" \
    -e PREFECT_SERVER_ANALYTICS_ENABLED="false" \
    -e PREFECT_LOGGING_LEVEL="WARNING" \
    docker.io/prefecthq/prefect:3-latest \
    prefect server start --host 0.0.0.0

# ============================================================
# Monitoring Stack
# ============================================================

echo "📦 Deploying Loki..."
podman run -d \
    --name ai-platform-loki \
    --pod living-atlas-ai-platform \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/loki:/etc/loki:ro \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/loki:/loki:Z \
    docker.io/grafana/loki:latest \
    -config.file=/etc/loki/loki.yml

echo "📦 Deploying Tempo..."
podman run -d \
    --name ai-platform-tempo \
    --pod living-atlas-ai-platform \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/tempo:/etc/tempo:ro \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/tempo:/tmp/tempo:Z \
    docker.io/grafana/tempo:latest \
    -config.file=/etc/tempo.yml

echo "📦 Deploying OTel Collector..."
podman run -d \
    --name ai-platform-otel-collector \
    --pod living-atlas-ai-platform \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/otel:/etc/otel-collector:ro \
    docker.io/otel/opentelemetry-collector-contrib:latest \
    --config=/etc/otel-collector.yml

echo "📦 Deploying Prometheus..."
podman run -d \
    --name ai-platform-prometheus \
    --pod living-atlas-ai-platform \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/prometheus:/etc/prometheus:ro \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/prometheus/rules:/etc/prometheus/rules:ro \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/prometheus:/prometheus:Z \
    docker.io/prom/prometheus:latest \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus \
    --storage.tsdb.retention.time=30d

echo "📦 Deploying Grafana..."
podman run -d \
    --name ai-platform-grafana \
    --pod living-atlas-ai-platform \
    -e GF_SECURITY_ADMIN_USER=$GF_SECURITY_ADMIN_USER \
    -e GF_SECURITY_ADMIN_PASSWORD=$GF_SECURITY_ADMIN_PASSWORD \
    -e GF_INSTALL_PLUGINS="grafana-piechart-panel" \
    -e GF_AUTH_ANONYMOUS_ENABLED="false" \
    -e GF_SERVER_ROOT_URL=$GF_SERVER_ROOT_URL \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/grafana/datasources:/etc/grafana/provisioning/datasources:ro \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro \
    -v /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/grafana:/var/lib/grafana:Z \
    docker.io/grafana/grafana:latest

echo "=========================================="
echo "✅ Infrastructure deployment complete!"
echo "=========================================="
echo ""
echo "Services deployed:"
echo "  PostgreSQL:    http://localhost:6432"
echo "  Redis:         http://localhost:7379"
echo "  RabbitMQ:      http://localhost:6672 (AMQP)"
echo "  RabbitMQ Mgmt: http://localhost:16672"
echo "  MinIO API:     http://localhost:10000"
echo "  MinIO Console: http://localhost:10001"
echo "  Weaviate:      http://localhost:8081"
echo "  Prefect:       http://localhost:4200"
echo "  Grafana:       http://localhost:3000"
echo "  Prometheus:    http://localhost:9090"
echo ""
echo "Next steps:"
echo "  1. Wait for services to be healthy: ./scripts/health_checks.sh"
echo "  2. Apply database migrations: ./scripts/apply_migrations.sh"
echo "  3. Deploy AI services: ./scripts/deploy_ai_services.sh"
