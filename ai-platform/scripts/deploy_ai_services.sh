#!/bin/bash

# AI Platform Services Deployment Script
# Deploys all 6 AI Platform microservices using podman

set -e

echo "=========================================="
echo "Deploying AI Platform Services"
echo "=========================================="

# Load environment variables
if [ -f scripts/env_ai_platform.sh ]; then
    source scripts/env_ai_platform.sh
else
    echo "❌ Environment file not found: scripts/env_ai_platform.sh"
    exit 1
fi

# Check if API keys are set
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: No LLM API keys set!"
    echo "   Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY"
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 1
    fi
fi

# Check if pod exists
if ! podman pod exists living-atlas-ai-platform; then
    echo "❌ Pod 'living-atlas-ai-platform' does not exist"
    echo "Run: ./scripts/create_ai_platform_pod.sh"
    exit 1
fi

# Build shared library first
echo "🔨 Building shared library..."
cd shared
podman build -f Dockerfile.shared -t ai-platform-shared:latest .
cd ..

# ============================================================
# Ingestion Service
# ============================================================

echo "🤖 Deploying Ingestion Service..."
podman build -f infrastructure/docker/Dockerfile.python \
    --build-arg SERVICE_DIR=ingestion-service \
    -t ai-platform-ingestion:latest .

podman run -d \
    --name ai-platform-ingestion \
    --pod living-atlas-ai-platform \
    -e LA_SERVICE_NAME="ingestion-service" \
    -e LA_SERVICE_PORT="8000" \
    -e LA_PG_HOST="localhost" \
    -e LA_PG_PORT="6432" \
    -e LA_PG_DATABASE=$LA_PG_DATABASE \
    -e LA_PG_USER=$LA_PG_USER \
    -e LA_PG_PASSWORD=$LA_PG_PASSWORD \
    -e LA_KAFKA_BOOTSTRAP_SERVERS="localhost:9092" \
    -e LA_RABBITMQ_HOST="localhost" \
    -e LA_RABBITMQ_PORT="6672" \
    -e LA_RABBITMQ_USER=$LA_RABBITMQ_USER \
    -e LA_RABBITMQ_PASSWORD=$LA_RABBITMQ_PASSWORD \
    -e LA_REDIS_URL=$LA_REDIS_URL \
    -e LA_LOG_LEVEL=$LA_LOG_LEVEL \
    -e PODMAN_ENVIRONMENT="true" \
    -e OTEL_SERVICE_NAME="ingestion-service" \
    -e OTEL_EXPORTER_OTLP_ENDPOINT=$OTEL_EXPORTER_OTLP_ENDPOINT \
    ai-platform-ingestion:latest

# ============================================================
# Extraction Service
# ============================================================

echo "🤖 Deploying Extraction Service..."
podman build -f infrastructure/docker/Dockerfile.python \
    --build-arg SERVICE_DIR=extraction-service \
    -t ai-platform-extraction:latest .

podman run -d \
    --name ai-platform-extraction \
    --pod living-atlas-ai-platform \
    -e LA_SERVICE_NAME="extraction-service" \
    -e LA_SERVICE_PORT="8000" \
    -e LA_PG_HOST="localhost" \
    -e LA_PG_PORT="6432" \
    -e LA_PG_DATABASE=$LA_PG_DATABASE \
    -e LA_PG_USER=$LA_PG_USER \
    -e LA_PG_PASSWORD=$LA_PG_PASSWORD \
    -e LA_KAFKA_BOOTSTRAP_SERVERS="localhost:9092" \
    -e LA_RABBITMQ_HOST="localhost" \
    -e LA_RABBITMQ_PORT="6672" \
    -e LA_RABBITMQ_USER=$LA_RABBITMQ_USER \
    -e LA_RABBITMQ_PASSWORD=$LA_RABBITMQ_PASSWORD \
    -e LA_REDIS_URL=$LA_REDIS_URL \
    -e LA_LOG_LEVEL=$LA_LOG_LEVEL \
    -e PODMAN_ENVIRONMENT="true" \
    -e LA_GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
    -e LA_ASSEMBLYAI_API_KEY=$ASSEMBLYAI_API_KEY \
    -e LA_DEEPGRAM_API_KEY=$DEEPGRAM_API_KEY \
    -e OTEL_SERVICE_NAME="extraction-service" \
    -e OTEL_EXPORTER_OTLP_ENDPOINT=$OTEL_EXPORTER_OTLP_ENDPOINT \
    -v /home/sdibonerate85/Developmet/living-atlas/ai-platform/infrastructure/secrets:/etc/secrets:ro \
    ai-platform-extraction:latest

# ============================================================
# Enrichment Service
# ============================================================

echo "🤖 Deploying Enrichment Service..."
podman build -f infrastructure/docker/Dockerfile.python \
    --build-arg SERVICE_DIR=enrichment-service \
    -t ai-platform-enrichment:latest .

podman run -d \
    --name ai-platform-enrichment \
    --pod living-atlas-ai-platform \
    -e LA_SERVICE_NAME="enrichment-service" \
    -e LA_SERVICE_PORT="8000" \
    -e LA_PG_HOST="localhost" \
    -e LA_PG_PORT="6432" \
    -e LA_PG_DATABASE=$LA_PG_DATABASE \
    -e LA_PG_USER=$LA_PG_USER \
    -e LA_PG_PASSWORD=$LA_PG_PASSWORD \
    -e LA_KAFKA_BOOTSTRAP_SERVERS="localhost:9092" \
    -e LA_RABBITMQ_HOST="localhost" \
    -e LA_RABBITMQ_PORT="6672" \
    -e LA_RABBITMQ_USER=$LA_RABBITMQ_USER \
    -e LA_RABBITMQ_PASSWORD=$LA_RABBITMQ_PASSWORD \
    -e LA_REDIS_URL=$LA_REDIS_URL \
    -e LA_LOG_LEVEL=$LA_LOG_LEVEL \
    -e PODMAN_ENVIRONMENT="true" \
    -e LA_GEMINI_API_KEY=$GEMINI_API_KEY \
    -e LA_ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    -e LA_OPENAI_API_KEY=$OPENAI_API_KEY \
    -e LLM_PROVIDER=$LLM_PROVIDER \
    -e OTEL_SERVICE_NAME="enrichment-service" \
    -e OTEL_EXPORTER_OTLP_ENDPOINT=$OTEL_EXPORTER_OTLP_ENDPOINT \
    ai-platform-enrichment:latest

# ============================================================
# Embedding Service
# ============================================================

echo "🤖 Deploying Embedding Service..."
podman build -f infrastructure/docker/Dockerfile.python \
    --build-arg SERVICE_DIR=embedding-service \
    -t ai-platform-embedding:latest .

podman run -d \
    --name ai-platform-embedding \
    --pod living-atlas-ai-platform \
    -e LA_SERVICE_NAME="embedding-service" \
    -e LA_SERVICE_PORT="8000" \
    -e LA_PG_HOST="localhost" \
    -e LA_PG_PORT="6432" \
    -e LA_PG_DATABASE=$LA_PG_DATABASE \
    -e LA_PG_USER=$LA_PG_USER \
    -e LA_PG_PASSWORD=$LA_PG_PASSWORD \
    -e LA_KAFKA_BOOTSTRAP_SERVERS="localhost:9092" \
    -e LA_RABBITMQ_HOST="localhost" \
    -e LA_RABBITMQ_PORT="6672" \
    -e LA_RABBITMQ_USER=$LA_RABBITMQ_USER \
    -e LA_RABBITMQ_PASSWORD=$LA_RABBITMQ_PASSWORD \
    -e LA_REDIS_URL=$LA_REDIS_URL \
    -e LA_LOG_LEVEL=$LA_LOG_LEVEL \
    -e PODMAN_ENVIRONMENT="true" \
    -e LA_OPENAI_API_KEY=$OPENAI_API_KEY \
    -e LA_WEAVIATE_URL=$LA_WEAVIATE_URL \
    -e OTEL_SERVICE_NAME="embedding-service" \
    -e OTEL_EXPORTER_OTLP_ENDPOINT=$OTEL_EXPORTER_OTLP_ENDPOINT \
    ai-platform-embedding:latest

# ============================================================
# Article Service
# ============================================================

echo "🤖 Deploying Article Service..."
podman build -f infrastructure/docker/Dockerfile.python \
    --build-arg SERVICE_DIR=article-service \
    -t ai-platform-article:latest .

podman run -d \
    --name ai-platform-article \
    --pod living-atlas-ai-platform \
    -e LA_SERVICE_NAME="article-service" \
    -e LA_SERVICE_PORT="8000" \
    -e LA_PG_HOST="localhost" \
    -e LA_PG_PORT="6432" \
    -e LA_PG_DATABASE=$LA_PG_DATABASE \
    -e LA_PG_USER=$LA_PG_USER \
    -e LA_PG_PASSWORD=$LA_PG_PASSWORD \
    -e LA_KAFKA_BOOTSTRAP_SERVERS="localhost:9092" \
    -e LA_RABBITMQ_HOST="localhost" \
    -e LA_RABBITMQ_PORT="6672" \
    -e LA_RABBITMQ_USER=$LA_RABBITMQ_USER \
    -e LA_RABBITMQ_PASSWORD=$LA_RABBITMQ_PASSWORD \
    -e LA_REDIS_URL=$LA_REDIS_URL \
    -e LA_LOG_LEVEL=$LA_LOG_LEVEL \
    -e PODMAN_ENVIRONMENT="true" \
    -e LA_ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    -e LA_OPENAI_API_KEY=$OPENAI_API_KEY \
    -e OTEL_SERVICE_NAME="article-service" \
    -e OTEL_EXPORTER_OTLP_ENDPOINT=$OTEL_EXPORTER_OTLP_ENDPOINT \
    ai-platform-article:latest

# ============================================================
# Orchestration Service
# ============================================================

echo "🤖 Deploying Orchestration Service..."
podman build -f infrastructure/docker/Dockerfile.python \
    --build-arg SERVICE_DIR=orchestration-service \
    -t ai-platform-orchestration:latest .

podman run -d \
    --name ai-platform-orchestration \
    --pod living-atlas-ai-platform \
    -e LA_SERVICE_NAME="orchestration-service" \
    -e LA_SERVICE_PORT="8000" \
    -e LA_PG_HOST="localhost" \
    -e LA_PG_PORT="6432" \
    -e LA_PG_DATABASE=$LA_PG_DATABASE \
    -e LA_PG_USER=$LA_PG_USER \
    -e LA_PG_PASSWORD=$LA_PG_PASSWORD \
    -e LA_KAFKA_BOOTSTRAP_SERVERS="localhost:9092" \
    -e LA_RABBITMQ_HOST="localhost" \
    -e LA_RABBITMQ_PORT="6672" \
    -e LA_RABBITMQ_USER=$LA_RABBITMQ_USER \
    -e LA_RABBITMQ_PASSWORD=$LA_RABBITMQ_PASSWORD \
    -e LA_REDIS_URL=$LA_REDIS_URL \
    -e LA_LOG_LEVEL=$LA_LOG_LEVEL \
    -e PODMAN_ENVIRONMENT="true" \
    -e LA_PREFECT_API_URL=$LA_PREFECT_API_URL \
    -e LA_WEAVIATE_URL=$LA_WEAVIATE_URL \
    -e OTEL_SERVICE_NAME="orchestration-service" \
    -e OTEL_EXPORTER_OTLP_ENDPOINT=$OTEL_EXPORTER_OTLP_ENDPOINT \
    ai-platform-orchestration:latest

echo "=========================================="
echo "✅ AI Platform services deployed!"
echo "=========================================="
echo ""
echo "Services deployed:"
echo "  Ingestion Service:   http://localhost:8001"
echo "  Extraction Service: http://localhost:8002"
echo "  Enrichment Service:  http://localhost:8003"
echo "  Embedding Service:   http://localhost:8004"
echo "  Article Service:     http://localhost:8005"
echo "  Orchestration Svc:   http://localhost:8010"
echo ""
echo "Next steps:"
echo "  1. Check service health: curl http://localhost:8001/health"
echo "  2. View all services: podman ps --pod"
echo "  3. Check logs: podman logs ai-platform-ingestion"
echo "  4. Access API docs: http://localhost:8001/docs"
