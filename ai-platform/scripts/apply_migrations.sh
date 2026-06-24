#!/bin/bash

# AI Platform Database Migration Script
# Applies all database migrations to the PostgreSQL database

set -e

echo "=========================================="
echo "Applying Database Migrations"
echo "=========================================="

# Load environment variables
if [ -f scripts/env_ai_platform.sh ]; then
    source scripts/env_ai_platform.sh
else
    echo "❌ Environment file not found: scripts/env_ai_platform.sh"
    exit 1
fi

# Check if PostgreSQL container is running
if ! podman ps --format '{{.Names}}' | grep -q "^ai-platform-postgres$"; then
    echo "❌ PostgreSQL container is not running"
    echo "Run: ./scripts/deploy_infrastructure.sh"
    exit 1
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if podman exec ai-platform-postgres pg_isready -U living_atlas -d living_atlas >/dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

if ! podman exec ai-platform-postgres pg_isready -U living_atlas -d living_atlas >/dev/null 2>&1; then
    echo "❌ PostgreSQL did not become ready in time"
    exit 1
fi

# Apply migrations using the Python migration script
echo "🗄️  Applying database migrations..."

# Create a temporary container to run migrations
podman run --rm \
    --pod living-atlas-ai-platform \
    -e LA_PG_HOST="localhost" \
    -e LA_PG_PORT="6432" \
    -e LA_PG_DATABASE=$LA_PG_DATABASE \
    -e LA_PG_USER=$LA_PG_USER \
    -e LA_PG_PASSWORD=$LA_PG_PASSWORD \
    -e LA_LOG_LEVEL=$LA_LOG_LEVEL \
    ai-platform-shared:latest \
    python -m ai_shared.db.migrate

# Alternatively, apply SQL migrations directly if Python script fails
if [ $? -ne 0 ]; then
    echo "⚠️  Python migration failed, trying SQL migrations directly..."
    
    # Apply SQL migration files in order
    migration_dir="/home/sdibonerate85/Developmet/living-atlas/ai-platform/scripts/migrations"
    
    for migration_file in $(ls -v "$migration_dir"/*.sql); do
        echo "Applying: $(basename $migration_file)"
        podman exec -i ai-platform-postgres psql -U living_atlas -d living_atlas < "$migration_file"
    done
fi

echo "✅ Database migrations applied successfully!"
echo ""
echo "Verifying database schema..."
podman exec ai-platform-postgres psql -U living_atlas -d living_atlas -c "\dn" || true
podman exec ai-platform-postgres psql -U living_atlas -d living_atlas -c "\dt source.*" || true
podman exec ai-platform-postgres psql -U living_atlas -d living_atlas -c "\dt knowledge.*" || true
podman exec ai-platform-postgres psql -U living_atlas -d living_atlas -c "\dt ai.*" || true

echo ""
echo "Next steps:"
echo "  1. Deploy AI services: ./scripts/deploy_ai_services.sh"
echo "  2. Verify deployment: ./scripts/health_checks.sh"
