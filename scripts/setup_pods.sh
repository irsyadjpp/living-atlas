#!/bin/bash

# Setup script untuk 2 environment podman pods
# Pod 1: Development (ports 6xxx)
# Pod 2: Staging (ports 7xxx)

set -e

echo "=========================================="
echo "Setting up 2 Environment Pods"
echo "=========================================="

# Create volume directories
echo "Creating volume directories..."
mkdir -p /home/sdibonerate85/Developmet/living-atlas/data/pod1/{postgres,rabbitmq,redis,minio}
mkdir -p /home/sdibonerate85/Developmet/living-atlas/data/pod2/{postgres,rabbitmq,redis,minio}
chmod -R 777 /home/sdibonerate85/Developmet/living-atlas/data/pod1 /home/sdibonerate85/Developmet/living-atlas/data/pod2

# Create Pod 1: Development Environment
echo "Creating Pod 1 (Development)..."
podman pod create \
    --name living-atlas-dev \
    --publish 6432:5432 \
    --publish 6672:5672 \
    --publish 16672:15672 \
    --publish 7379:6379 \
    --publish 9333:8333 \
    --publish 10000:9000 \
    --publish 10001:9001 \
    --publish 6080:80 \
    --publish 6081:8080

# Create Pod 2: Staging Environment
echo "Creating Pod 2 (Staging)..."
podman pod create \
    --name living-atlas-staging \
    --publish 7432:5432 \
    --publish 7672:5672 \
    --publish 17672:15672 \
    --publish 8379:6379 \
    --publish 10333:8333 \
    --publish 11000:9000 \
    --publish 11001:9001 \
    --publish 7080:80 \
    --publish 7081:8080

# Create PostgreSQL for Pod 1 (Dev)
echo "Creating PostgreSQL for Pod 1..."
podman run -d \
    --name living-atlas-dev-postgres \
    --pod living-atlas-dev \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=living_atlas_dev \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod1/postgres:/var/lib/postgresql/data:Z \
    docker.io/library/postgres:17

# Create PostgreSQL for Pod 2 (Staging)
echo "Creating PostgreSQL for Pod 2..."
podman run -d \
    --name living-atlas-staging-postgres \
    --pod living-atlas-staging \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=living_atlas_staging \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod2/postgres:/var/lib/postgresql/data:Z \
    docker.io/library/postgres:17

# Create RabbitMQ for Pod 1 (Dev)
echo "Creating RabbitMQ for Pod 1..."
podman run -d \
    --name living-atlas-dev-rabbitmq \
    --pod living-atlas-dev \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=admin \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod1/rabbitmq:/var/lib/rabbitmq:Z \
    docker.io/library/rabbitmq:3-management-alpine

# Create RabbitMQ for Pod 2 (Staging)
echo "Creating RabbitMQ for Pod 2..."
podman run -d \
    --name living-atlas-staging-rabbitmq \
    --pod living-atlas-staging \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=admin \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod2/rabbitmq:/var/lib/rabbitmq:Z \
    docker.io/library/rabbitmq:3-management-alpine

# Create Redis for Pod 1 (Dev)
echo "Creating Redis for Pod 1..."
podman run -d \
    --name living-atlas-dev-redis \
    --pod living-atlas-dev \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod1/redis:/data:Z \
    docker.io/library/redis:7-alpine

# Create Redis for Pod 2 (Staging)
echo "Creating Redis for Pod 2..."
podman run -d \
    --name living-atlas-staging-redis \
    --pod living-atlas-staging \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod2/redis:/data:Z \
    docker.io/library/redis:7-alpine

# Create MinIO for Pod 1 (Dev)
echo "Creating MinIO for Pod 1..."
podman run -d \
    --name living-atlas-dev-minio \
    --pod living-atlas-dev \
    -e MINIO_ROOT_USER=admin \
    -e MINIO_ROOT_PASSWORD=admin123 \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod1/minio:/data:Z \
    docker.io/minio/minio:latest \
    server /data --console-address ":9001"

# Create MinIO for Pod 2 (Staging)
echo "Creating MinIO for Pod 2..."
podman run -d \
    --name living-atlas-staging-minio \
    --pod living-atlas-staging \
    -e MINIO_ROOT_USER=admin \
    -e MINIO_ROOT_PASSWORD=admin123 \
    -v /home/sdibonerate85/Developmet/living-atlas/data/pod2/minio:/data:Z \
    docker.io/minio/minio:latest \
    server /data --console-address ":9001"

echo "=========================================="
echo "✅ Pods created successfully!"
echo "=========================================="
echo ""
echo "Pod 1 (Development) - Ports:"
echo "  PostgreSQL:  6432"
echo "  RabbitMQ:    6672 (amqp), 16672 (management)"
echo "  Redis:       7379"
echo "  MinIO API:   10000"
echo "  MinIO Console: 10001"
echo ""
echo "Pod 2 (Staging) - Ports:"
echo "  PostgreSQL:  7432"
echo "  RabbitMQ:    7672 (amqp), 17672 (management)"
echo "  Redis:       8379"
echo "  MinIO API:   11000"
echo "  MinIO Console: 11001"
echo ""
echo "To check pods status:"
echo "  podman pod ps"
echo "  podman ps --pod"
echo ""
