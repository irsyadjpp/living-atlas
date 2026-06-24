#!/bin/bash

# AI Platform Environment Configuration for Podman
# This script sets environment variables for podman deployment

export PODMAN_ENVIRONMENT="true"

# ============================================================
# Database Configuration (PostgreSQL)
# ============================================================
export LA_PG_HOST="localhost"
export LA_PG_PORT="6432"
export LA_PG_DATABASE="living_atlas"
export LA_PG_USER="living_atlas"
export LA_PG_PASSWORD="living_atlas"

# ============================================================
# Message Queue Configuration (RabbitMQ)
# ============================================================
export LA_RABBITMQ_HOST="localhost"
export LA_RABBITMQ_PORT="6672"
export LA_RABBITMQ_USER="admin"
export LA_RABBITMQ_PASSWORD="admin"
export LA_RABBITMQ_MANAGEMENT_PORT="16672"
# For Kafka compatibility (if needed)
export LA_KAFKA_BOOTSTRAP_SERVERS="localhost:9092"

# ============================================================
# Cache Configuration (Redis)
# ============================================================
export LA_REDIS_HOST="localhost"
export LA_REDIS_PORT="7379"
export LA_REDIS_URL="redis://localhost:7379/0"

# ============================================================
# Vector Database Configuration (Weaviate)
# ============================================================
export LA_WEAVIATE_HOST="localhost"
export LA_WEAVIATE_PORT="8081"
export LA_WEAVIATE_URL="http://localhost:8081"
export LA_WEAVIATE_API_KEY=""

# ============================================================
# Object Storage Configuration (MinIO)
# ============================================================
export LA_MINIO_ENDPOINT="localhost"
export LA_MINIO_PORT="10000"
export LA_MINIO_ACCESS_KEY="admin"
export LA_MINIO_SECRET_KEY="admin123"
export LA_MINIO_CONSOLE_URL="http://localhost:10001"
export LA_MINIO_USE_SSL="false"

# ============================================================
# Orchestration Configuration (Prefect)
# ============================================================
export LA_PREFECT_HOST="localhost"
export LA_PREFECT_PORT="4200"
export LA_PREFECT_API_URL="http://localhost:4200/api"

# ============================================================
# Service Ports
# ============================================================
export INGESTION_SERVICE_PORT="8001"
export EXTRACTION_SERVICE_PORT="8002"
export ENRICHMENT_SERVICE_PORT="8003"
export EMBEDDING_SERVICE_PORT="8004"
export ARTICLE_SERVICE_PORT="8005"
export ORCHESTRATION_SERVICE_PORT="8010"

# ============================================================
# LLM API Keys (Required - must be set)
# ============================================================
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-}"

# Default LLM provider for enrichment (gemini | claude | openai)
export LLM_PROVIDER="${LLM_PROVIDER:-gemini}"

# ============================================================
# STT API Keys (Required for fallback)
# ============================================================
export ASSEMBLYAI_API_KEY="${ASSEMBLYAI_API_KEY:-}"
export DEEPGRAM_API_KEY="${DEEPGRAM_API_KEY:-}"

# ============================================================
# Google Cloud (for STT)
# ============================================================
export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-./infrastructure/secrets/gcp-credentials.json}"

# ============================================================
# Observability Configuration
# ============================================================
export LA_LOG_LEVEL="${LA_LOG_LEVEL:-INFO}"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-}"

# ============================================================
# Grafana Configuration
# ============================================================
export GF_SECURITY_ADMIN_USER="admin"
export GF_SECURITY_ADMIN_PASSWORD="admin"
export GF_SERVER_ROOT_URL="http://localhost:3000"

# ============================================================
# Monitoring Configuration
# ============================================================
export PROMETHEUS_URL="http://localhost:9090"
export LOKI_URL="http://localhost:3100"
export TEMPO_URL="http://localhost:3200"
export GRAFANA_URL="http://localhost:3000"

echo "✅ AI Platform Podman Environment Variables Loaded"
echo "   PostgreSQL:  postgresql://living_atlas@localhost:6432/living_atlas"
echo "   RabbitMQ:   amqp://admin:admin@localhost:6672"
echo "   Redis:      redis://localhost:7379/0"
echo "   Weaviate:   http://localhost:8081"
echo "   MinIO:      http://localhost:10000"
echo "   Prefect:    http://localhost:4200/api"
echo ""
echo "⚠️  IMPORTANT: Set your API keys before deploying:"
echo "   export OPENAI_API_KEY='sk-...'"
echo "   export ANTHROPIC_API_KEY='sk-ant-...'"
echo "   export GEMINI_API_KEY='AIza...'"
