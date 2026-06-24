#!/bin/bash

# AI Platform Extended Pod Creation Script
# Creates a unified podman pod for Living Atlas AI Platform
# Integrates existing infrastructure with new AI services

set -e

echo "=========================================="
echo "Creating AI Platform Extended Pod"
echo "=========================================="

# Check if pod already exists
if podman pod exists living-atlas-ai-platform; then
    echo "⚠️  Pod 'living-atlas-ai-platform' already exists"
    read -p "Do you want to remove and recreate it? (y/n): " recreate
    if [ "$recreate" = "y" ]; then
        echo "Removing existing pod..."
        podman pod rm living-atlas-ai-platform
    else
        echo "Using existing pod"
        exit 0
    fi
fi

# Create volume directories
echo "Creating volume directories..."
mkdir -p /home/sdibonerate85/Developmet/living-atlas/data/ai-platform/{postgres,rabbitmq,redis,minio,weaviate,prefect,tempo,loki,prometheus,grafana}
chmod -R 777 /home/sdibonerate85/Developmet/living-atlas/data/ai-platform

# Create the AI Platform extended pod
echo "Creating extended pod with all port mappings..."
podman pod create \
    --name living-atlas-ai-platform \
    --publish 6432:5432 \
    --publish 6672:5672 \
    --publish 16672:15672 \
    --publish 7379:6379 \
    --publish 10000:9000 \
    --publish 10001:9001 \
    --publish 8081:8081 \
    --publish 9092:9092 \
    --publish 9644:9644 \
    --publish 4200:4200 \
    --publish 8001:8001 \
    --publish 8002:8002 \
    --publish 8003:8003 \
    --publish 8004:8004 \
    --publish 8005:8005 \
    --publish 8010:8010 \
    --publish 3100:3100 \
    --publish 3200:3200 \
    --publish 9090:9090 \
    --publish 3000:3000 \
    --publish 4317:4317 \
    --publish 4318:4318 \
    --publish 8888:8888 \
    --publish 8889:8889 \
    --publish 8005:8005 \
    --publish 8010:8010

echo "✅ Extended pod 'living-atlas-ai-platform' created successfully!"
echo ""
echo "Port mappings:"
echo "  Existing Infrastructure:"
echo "    PostgreSQL:    6432:5432"
echo "    RabbitMQ AMQP:  6672:5672"
echo "    RabbitMQ Mgmt:  16672:15672"
echo "    Redis:         7379:6379"
echo "    MinIO API:     10000:9000"
echo "    MinIO Console: 10001:9001"
echo ""
echo "  AI Platform Services:"
echo "    Weaviate:           8081:8081"
echo "    Redpanda Kafka:      9092:9092"
echo "    Redpanda Admin:      9644:9644"
echo "    Prefect Server:      4200:4200"
echo "    Ingestion Service:   8001:8001"
echo "    Extraction Service: 8002:8002"
echo "    Enrichment Service: 8003:8003"
echo "    Embedding Service:  8004:8004"
echo "    Article Service:    8005:8005"
echo "    Orchestration Svc:   8010:8010"
echo ""
echo "  Monitoring Stack:"
echo "    Loki:              3100:3100"
echo "    Tempo:             3200:3200"
echo "    Prometheus:        9090:9090"
echo "    Grafana:           3000:3000"
echo "    OTel Collector:    4317:4317 (gRPC)"
echo "    OTel Collector:    4318:4318 (HTTP)"
echo "    OTel Metrics:      8888:8888"
echo "    OTel Exporter:     8889:8889"
echo ""
echo "Next steps:"
echo "  1. Deploy infrastructure: ./scripts/deploy_infrastructure.sh"
echo "  2. Deploy AI services: ./scripts/deploy_ai_services.sh"
echo "  3. Check pod status: podman pod ps"
echo "  4. View containers: podman ps --pod"
