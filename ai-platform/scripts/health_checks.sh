#!/bin/bash

# AI Platform Health Check Script
# Checks health of all deployed services

set -e

echo "=========================================="
echo "AI Platform Health Checks"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local service_name=$1
    local url=$2
    local description=$3
    
    echo -n "Checking $service_name ($description)... "
    
    if curl -f -s -o /dev/null "$url"; then
        echo -e "${GREEN}✓ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}✗ UNHEALTHY${NC}"
        return 1
    fi
}

# Function to check container status
check_container() {
    local container_name=$1
    
    if podman ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${GREEN}✓ RUNNING${NC}"
        return 0
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        return 1
    fi
}

# ============================================================
# Infrastructure Health Checks
# ============================================================

echo "📦 Infrastructure Services:"
echo "   PostgreSQL:      $(check_container ai-platform-postgres)"
echo "   Redis:           $(check_container ai-platform-redis)"
echo "   RabbitMQ:        $(check_container ai-platform-rabbitmq)"
echo "   MinIO:           $(check_container ai-platform-minio)"
echo "   Weaviate:        $(check_container ai-platform-weaviate)"
echo "   Prefect:         $(check_container ai-platform-prefect)"

echo ""
echo "📊 Monitoring Stack:"
echo "   Loki:            $(check_container ai-platform-loki)"
echo "   Tempo:           $(check_container ai-platform-tempo)"
echo "   OTel Collector:  $(check_container ai-platform-otel-collector)"
echo "   Prometheus:      $(check_container ai-platform-prometheus)"
echo "   Grafana:         $(check_container ai-platform-grafana)"

# ============================================================
# AI Services Health Checks
# ============================================================

echo ""
echo "🤖 AI Platform Services:"
echo "   Ingestion Service:   $(check_container ai-platform-ingestion)"
echo "   Extraction Service:  $(check_container ai-platform-extraction)"
echo "   Enrichment Service:  $(check_container ai-platform-enrichment)"
echo "   Embedding Service:   $(check_container ai-platform-embedding)"
echo "   Article Service:     $(check_container ai-platform-article)"
echo "   Orchestration Svc:   $(check_container ai-platform-orchestration)"

# ============================================================
# HTTP Health Checks
# ============================================================

echo ""
echo "🔗 HTTP Health Endpoints:"

# Check if services are responding
check_service "PostgreSQL" "http://localhost:6432" "Database"
check_service "Redis" "http://localhost:7379" "Cache"
check_service "Weaviate" "http://localhost:8081/v1/.well-known/ready" "Vector DB"
check_service "Prefect" "http://localhost:4200/api/health" "Orchestration"
check_service "Grafana" "http://localhost:3000/api/health" "Dashboard"
check_service "Prometheus" "http://localhost:9090/-/healthy" "Metrics"

# Check AI services
check_service "Ingestion Service" "http://localhost:8001/health" "API"
check_service "Extraction Service" "http://localhost:8002/health" "API"
check_service "Enrichment Service" "http://localhost:8003/health" "API"
check_service "Embedding Service" "http://localhost:8004/health" "API"
check_service "Article Service" "http://localhost:8005/health" "API"
check_service "Orchestration Service" "http://localhost:8010/health" "API"

# ============================================================
# Database Connection Check
# ============================================================

echo ""
echo "🗄️  Database Connection:"
echo -n "   PostgreSQL connection... "
if podman exec ai-platform-postgres pg_isready -U living_atlas -d living_atlas >/dev/null 2>&1; then
    echo -e "${GREEN}✓ CONNECTED${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# ============================================================
# Summary
# ============================================================

echo ""
echo "=========================================="
echo "Health Check Summary"
echo "=========================================="

# Count total and healthy containers
total_containers=$(podman ps --filter pod=living-atlas-ai-platform --format '{{.Names}}' | wc -l)
healthy_containers=$(podman ps --filter pod=living-atlas-ai-platform --filter status=running --format '{{.Names}}' | wc -l)

echo "Total containers: $total_containers"
echo "Running containers: $healthy_containers"

if [ $healthy_containers -eq $total_containers ]; then
    echo -e "${GREEN}All services are healthy!${NC}"
    exit 0
else
    echo -e "${YELLOW}Some services are not healthy${NC}"
    exit 1
fi
