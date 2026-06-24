#!/bin/bash

# Environment variables for Pod 1 (Development)
# Source this file before running applications in Dev environment

export POD_ENV="development"

# Database
export DATABASE_URL="postgresql://postgres:postgres@localhost:6432/living_atlas_dev"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="6432"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="postgres"
export POSTGRES_DB="living_atlas_dev"

# RabbitMQ
export RABBITMQ_URL="amqp://admin:admin@localhost:6672"
export RABBITMQ_HOST="localhost"
export RABBITMQ_PORT="6672"
export RABBITMQ_USER="admin"
export RABBITMQ_PASSWORD="admin"
export RABBITMQ_MANAGEMENT_PORT="16672"

# Redis
export REDIS_URL="redis://localhost:7379"
export REDIS_HOST="localhost"
export REDIS_PORT="7379"

# MinIO
export MINIO_ENDPOINT="localhost:10000"
export MINIO_ACCESS_KEY="admin"
export MINIO_SECRET_KEY="admin123"
export MINIO_CONSOLE_URL="http://localhost:10001"
export MINIO_USE_SSL="false"

# Application
export APP_PORT="6081"
export FRONTEND_PORT="6080"

echo "✅ Development environment variables loaded"
echo "   Database: postgresql://postgres@localhost:6432/living_atlas_dev"
echo "   RabbitMQ: amqp://admin@localhost:6672"
echo "   Redis: redis://localhost:7379"
echo "   MinIO: http://localhost:9333"
