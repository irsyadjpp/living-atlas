#!/bin/bash

# Environment variables for Pod 2 (Staging)
# Source this file before running applications in Staging environment

export POD_ENV="staging"

# Database
export DATABASE_URL="postgresql://postgres:postgres@localhost:7432/living_atlas_staging"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="7432"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="postgres"
export POSTGRES_DB="living_atlas_staging"

# RabbitMQ
export RABBITMQ_URL="amqp://admin:admin@localhost:7672"
export RABBITMQ_HOST="localhost"
export RABBITMQ_PORT="7672"
export RABBITMQ_USER="admin"
export RABBITMQ_PASSWORD="admin"
export RABBITMQ_MANAGEMENT_PORT="17672"

# Redis
export REDIS_URL="redis://localhost:8379"
export REDIS_HOST="localhost"
export REDIS_PORT="8379"

# MinIO
export MINIO_ENDPOINT="localhost:11000"
export MINIO_ACCESS_KEY="admin"
export MINIO_SECRET_KEY="admin123"
export MINIO_CONSOLE_URL="http://localhost:11001"
export MINIO_USE_SSL="false"

# Application
export APP_PORT="7081"
export FRONTEND_PORT="7080"

echo "✅ Staging environment variables loaded"
echo "   Database: postgresql://postgres@localhost:7432/living_atlas_staging"
echo "   RabbitMQ: amqp://admin@localhost:7672"
echo "   Redis: redis://localhost:8379"
echo "   MinIO: http://localhost:10333"
