#!/bin/bash

# AI Platform Unified Deployment Script
# Single command to deploy the entire AI Platform

set -e

echo "=========================================="
echo "🚀 Deploying Living Atlas AI Platform"
echo "=========================================="

# 1. Check prerequisites
echo "📋 Checking prerequisites..."

command -v podman >/dev/null 2>&1 || { echo "❌ podman not found"; exit 1; }

if [ ! -f scripts/env_ai_platform.sh ]; then
    echo "❌ Environment file not found: scripts/env_ai_platform.sh"
    exit 1
fi

# Check for API keys
source scripts/env_ai_platform.sh

if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: No LLM API keys set!"
    echo "   Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY"
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 1
    fi
fi

echo "✅ Prerequisites check passed"

# 2. Create pod
echo ""
echo "🏗️  Creating unified pod..."
if podman pod exists living-atlas-ai-platform; then
    echo "⚠️  Pod already exists, using existing pod"
else
    ./scripts/create_ai_platform_pod.sh
fi

# 3. Deploy infrastructure
echo ""
echo "📦 Deploying infrastructure services..."
./scripts/deploy_infrastructure.sh

# 4. Wait for infrastructure to be healthy
echo ""
echo "⏳ Waiting for infrastructure to be healthy..."
for i in {1..30}; do
    if podman exec ai-platform-postgres pg_isready -U living_atlas -d living_atlas >/dev/null 2>&1; then
        echo "✅ Infrastructure is ready"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# 5. Apply database migrations
echo ""
echo "🗄️  Applying database migrations..."
./scripts/apply_migrations.sh

# 6. Deploy AI services
echo ""
echo "🤖 Deploying AI services..."
./scripts/deploy_ai_services.sh

# 7. Verify deployment
echo ""
echo "🔍 Verifying deployment..."
./scripts/health_checks.sh

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Access Points:"
echo "  📊 Grafana Dashboard:   http://localhost:3000 (admin/admin)"
echo "  📈 Prometheus:         http://localhost:9090"
echo "  🔍 Tracing (Tempo):    http://localhost:3200"
echo "  📝 Logs (Loki):        http://localhost:3100"
echo "  🤖 Prefect UI:         http://localhost:4200"
echo "  🧠 Weaviate:           http://localhost:8081"
echo ""
echo "AI Services:"
echo "  📥 Ingestion Service:  http://localhost:8001/docs"
echo "  🔤 Extraction Service: http://localhost:8002/docs"
echo "  🎯 Enrichment Service: http://localhost:8003/docs"
echo "  🔍 Embedding Service:  http://localhost:8004/docs"
echo "  📝 Article Service:   http://localhost:8005/docs"
echo "  🎮 Orchestration Svc:  http://localhost:8010/docs"
echo ""
echo "Infrastructure:"
echo "  🗄️  PostgreSQL:        postgresql://living_atlas@localhost:6432/living_atlas"
echo "  🔴 Redis:             redis://localhost:7379/0"
echo "  🐰 RabbitMQ:          amqp://admin:admin@localhost:6672"
echo "  📦 MinIO:             http://localhost:10000 (admin/admin123)"
echo ""
echo "Management Commands:"
echo "  View logs:     podman logs -f ai-platform-ingestion"
echo "  All containers: podman ps --pod"
echo "  Stop all:      podman pod stop living-atlas-ai-platform"
echo "  Start all:     podman pod start living-atlas-ai-platform"
echo "  Health check:  ./scripts/health_checks.sh"
echo ""
echo "Next Steps:"
echo "  1. Test the ingestion service with a YouTube URL"
echo "  2. Monitor the pipeline in Grafana dashboards"
echo "  3. Configure API keys for full functionality"
