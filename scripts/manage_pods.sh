#!/bin/bash

# Management script for Docker Compose environments
# Usage: ./manage_pods.sh [command] [environment]
# Commands: start, stop, restart, status, delete
# Environments: dev, staging, all

set -e

COMMAND=$1
ENV_NAME=$2

# Function to show usage
show_usage() {
    echo "Usage: $0 [command] [environment]"
    echo ""
    echo "Commands:"
    echo "  start     - Start environment(s)"
    echo "  stop      - Stop environment(s)"
    echo "  restart   - Restart environment(s)"
    echo "  status    - Show environment status"
    echo "  delete    - Delete environment(s) and volumes"
    echo ""
    echo "Environment names:"
    echo "  dev       - Development environment only"
    echo "  staging   - Staging environment only"
    echo "  all       - Both environments"
    echo ""
    echo "Examples:"
    echo "  $0 start dev"
    echo "  $0 stop all"
    echo "  $0 status staging"
}

# Function to get compose file by alias
get_compose_file() {
    case $1 in
        dev)
            echo "infrastructure/compose.yml"
            ;;
        staging)
            echo "infrastructure/compose.staging.yml"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Function to start environment
start_env() {
    local compose=$(get_compose_file $1)
    if [ -z "$compose" ]; then
        echo "Invalid environment: $1"
        exit 1
    fi

    echo "Starting $1 environment..."
    docker compose -f $compose up -d
    echo "✅ $1 environment started"
}

# Function to stop environment
stop_env() {
    local compose=$(get_compose_file $1)
    if [ -z "$compose" ]; then
        echo "Invalid environment: $1"
        exit 1
    fi

    echo "Stopping $1 environment..."
    docker compose -f $compose down
    echo "✅ $1 environment stopped"
}

# Function to restart environment
restart_env() {
    local compose=$(get_compose_file $1)
    if [ -z "$compose" ]; then
        echo "Invalid environment: $1"
        exit 1
    fi

    echo "Restarting $1 environment..."
    docker compose -f $compose restart
    echo "✅ $1 environment restarted"
}

# Function to show environment status
show_status() {
    local compose=$(get_compose_file $1)
    if [ -z "$compose" ]; then
        echo "Invalid environment: $1"
        exit 1
    fi

    echo "Status for $1 environment:"
    docker compose -f $compose ps
}

# Function to delete environment
delete_env() {
    local compose=$(get_compose_file $1)
    if [ -z "$compose" ]; then
        echo "Invalid environment: $1"
        exit 1
    fi

    echo "Deleting $1 environment..."
    docker compose -f $compose down -v
    echo "✅ $1 environment deleted"
}

# Main logic
case $COMMAND in
    start)
        if [ "$ENV_NAME" = "all" ]; then
            start_env dev
            start_env staging
        else
            start_env $ENV_NAME
        fi
        ;;
    stop)
        if [ "$ENV_NAME" = "all" ]; then
            stop_env dev
            stop_env staging
        else
            stop_env $ENV_NAME
        fi
        ;;
    restart)
        if [ "$ENV_NAME" = "all" ]; then
            restart_env dev
            restart_env staging
        else
            restart_env $ENV_NAME
        fi
        ;;
    status)
        if [ "$ENV_NAME" = "all" ]; then
            echo "=== All Environments Status ==="
            docker compose ls
        else
            show_status $ENV_NAME
        fi
        ;;
    delete)
        if [ "$ENV_NAME" = "all" ]; then
            read -p "Are you sure you want to delete both environments? (y/n): " confirm
            if [ "$confirm" = "y" ]; then
                delete_env dev
                delete_env staging
            else
                echo "Cancelled"
            fi
        else
            read -p "Are you sure you want to delete $ENV_NAME environment? (y/n): " confirm
            if [ "$confirm" = "y" ]; then
                delete_env $ENV_NAME
            else
                echo "Cancelled"
            fi
        fi
        ;;
    *)
        show_usage
        exit 1
        ;;
esac</write_to_file>
<task_progress>

- [x] Read current infrastructure files
- [x] Convert compose.yml (Podman → Docker)
- [x] Convert Dockerfiles (podman → docker)
- [x] Convert scripts (manage_pods.sh → docker compose)
- [ ] Rename application-podman.yaml → application-docker.yaml
- [ ] Update docs (POD_SETUP_STRATEGY.md, deployment-report.md)
- [ ] Update env scripts

</task_progress>
</write_to_file>