#!/bin/bash

# AI Platform Services Deployment - Simplified Approach
# Deploys services using existing Python environment and dev pod infrastructure

set -e

echo "=========================================="
echo "Deploying AI Platform Services (Simplified)"
echo "=========================================="

# Load environment variables
if [ -f scripts/env_ai_platform.sh ]; then
    source scripts/env_ai_platform.sh
else
    echo "❌ Environment file not found: scripts/env_ai_platform.sh"
    exit 1
fi

# Set podman environment
export PODMAN_ENVIRONMENT=true

# Update environment to use existing dev pod infrastructure
export LA_PG_HOST="localhost"
export LA_PG_PORT="6432"
export LA_PG_DATABASE="living_atlas_dev"
export LA_PG_USER="postgres"
export LA_PG_PASSWORD="postgres"

export LA_REDIS_URL="redis://localhost:7379/0"

export LA_RABBITMQ_HOST="localhost"
export LA_RABBITMQ_PORT="6672"
export LA_RABBITMQ_USER="guest"
export LA_RABBITMQ_PASSWORD="guest"

export LA_WEAVIATE_URL="http://localhost:8081"

export LA_PREFECT_API_URL="http://localhost:4200/api"

echo "Environment Configuration:"
echo "  PostgreSQL: postgresql://postgres@localhost:6432/living_atlas_dev"
echo "  Redis: redis://localhost:7379/0"
echo "  RabbitMQ: amqp://guest:guest@localhost:6672/"
echo "  Weaviate: http://localhost:8081"
echo "  Prefect: http://localhost:4200/api"
echo ""

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    local module_path=$4
    
    echo "🤖 Deploying $service_name on port $port..."
    
    # Navigate to ai-platform root directory
    cd /home/sdibonerate85/Developmet/living-atlas/ai-platform
    
    # Install shared library first
    echo "   Installing shared library..."
    pip install -e ./shared --quiet
    
    # Navigate to service directory
    echo "   Installing dependencies for $service_name..."
    cd $service_dir
    pip install -e . --quiet
    
    # Start service in background with proper working directory and Python path
    echo "   Starting $service_name..."
    export PATH="/home/sdibonerate85/.local/bin:$PATH"
    export PYTHONPATH="/home/sdibonerate85/Developmet/living-atlas/ai-platform/shared/src:/home/sdibonerate85/Developmet/living-atlas/ai-platform/$service_dir/src:$PYTHONPATH"
    
    cd /home/sdibonerate85/Developmet/living-atlas/ai-platform/$service_dir
    nohup python -m uvicorn ${module_path}:app \
        --host 0.0.0.0 \
        --port $port \
        --workers 1 \
        --limit-concurrency 100 \
        > /tmp/$service_name.log 2>&1 &
    
    local pid=$!
    echo $pid > /tmp/$service_name.pid
    echo "   $service_name started with PID $pid"
    
    # Wait for service to start
    echo "   Waiting for $service_name to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:$port/health >/dev/null 2>&1; then
            echo "   ✅ $service_name is ready!"
            cd /home/sdibonerate85/Developmet/living-atlas/ai-platform
            return 0
        fi
        sleep 2
    done
    
    echo "   ⚠️  $service_name did not start within timeout"
    cd /home/sdibonerate85/Developmet/living-atlas/ai-platform
    return 1
}

# Deploy services sequentially
echo "Deploying AI Platform Services..."
echo ""

# Define services with their module paths
declare -A services=(
    ["ingestion-service"]="ingestion-service:8001:ingestion.main"
    ["extraction-service"]="extraction-service:8002:extraction.main"
    ["enrichment-service"]="enrichment-service:8003:enrichment.main"
    ["embedding-service"]="embedding-service:8004:embedding.main"
    ["article-service"]="article-service:8005:article.main"
    ["orchestration-service"]="orchestration-service:8010:orchestration.main"
)

for service_name in "${!services[@]}"; do
    if [ -d "$service_name" ]; then
        IFS=':' read -r service_dir port module_path <<< "${services[$service_name]}"
        deploy_service "$service_name" "$service_dir" "$port" "$module_path"
    else
        echo "⚠️  $service_name not found, skipping"
    fi
    echo ""
done

echo ""
echo "=========================================="
echo "Service Deployment Complete"
echo "=========================================="
echo ""
echo "Check service status:"
echo "  curl http://localhost:8001/health"
echo ""
echo "View logs:"
echo "  tail -f /tmp/ingestion-service.log"
echo ""
echo "Stop services:"
echo "  kill $(cat /tmp/ingestion-service.pid)"
