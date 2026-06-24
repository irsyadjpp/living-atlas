#!/bin/bash

# Management script for 2 environment pods
# Usage: ./manage_pods.sh [command] [pod_name]
# Commands: start, stop, restart, status, delete
# Pod names: dev, staging, all

set -e

COMMAND=$1
POD_NAME=$2

# Function to show usage
show_usage() {
    echo "Usage: $0 [command] [pod_name]"
    echo ""
    echo "Commands:"
    echo "  start     - Start pod(s)"
    echo "  stop      - Stop pod(s)"
    echo "  restart   - Restart pod(s)"
    echo "  status    - Show pod status"
    echo "  delete    - Delete pod(s) and containers"
    echo ""
    echo "Pod names:"
    echo "  dev       - Development pod only"
    echo "  staging   - Staging pod only"
    echo "  all       - Both pods"
    echo ""
    echo "Examples:"
    echo "  $0 start dev"
    echo "  $0 stop all"
    echo "  $0 status staging"
}

# Function to get pod name by alias
get_pod_name() {
    case $1 in
        dev)
            echo "living-atlas-dev"
            ;;
        staging)
            echo "living-atlas-staging"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Function to start pod
start_pod() {
    local pod=$(get_pod_name $1)
    if [ -z "$pod" ]; then
        echo "Invalid pod name: $1"
        exit 1
    fi

    echo "Starting $pod..."
    podman pod start $pod
    echo "✅ $pod started"
}

# Function to stop pod
stop_pod() {
    local pod=$(get_pod_name $1)
    if [ -z "$pod" ]; then
        echo "Invalid pod name: $1"
        exit 1
    fi

    echo "Stopping $pod..."
    podman pod stop $pod
    echo "✅ $pod stopped"
}

# Function to restart pod
restart_pod() {
    local pod=$(get_pod_name $1)
    if [ -z "$pod" ]; then
        echo "Invalid pod name: $1"
        exit 1
    fi

    echo "Restarting $pod..."
    podman pod restart $pod
    echo "✅ $pod restarted"
}

# Function to show pod status
show_status() {
    local pod=$(get_pod_name $1)
    if [ -z "$pod" ]; then
        echo "Invalid pod name: $1"
        exit 1
    fi

    echo "Status for $pod:"
    podman pod ps --filter name=$pod
    echo ""
    echo "Containers in $pod:"
    podman ps --filter pod=$pod
}

# Function to delete pod
delete_pod() {
    local pod=$(get_pod_name $1)
    if [ -z "$pod" ]; then
        echo "Invalid pod name: $1"
        exit 1
    fi

    echo "Deleting $pod..."
    podman pod stop $pod
    podman pod rm $pod
    echo "✅ $pod deleted"
}

# Main logic
case $COMMAND in
    start)
        if [ "$POD_NAME" = "all" ]; then
            start_pod dev
            start_pod staging
        else
            start_pod $POD_NAME
        fi
        ;;
    stop)
        if [ "$POD_NAME" = "all" ]; then
            stop_pod dev
            stop_pod staging
        else
            stop_pod $POD_NAME
        fi
        ;;
    restart)
        if [ "$POD_NAME" = "all" ]; then
            restart_pod dev
            restart_pod staging
        else
            restart_pod $POD_NAME
        fi
        ;;
    status)
        if [ "$POD_NAME" = "all" ]; then
            echo "=== All Pods Status ==="
            podman pod ps
            echo ""
            echo "=== All Containers ==="
            podman ps --pod
        else
            show_status $POD_NAME
        fi
        ;;
    delete)
        if [ "$POD_NAME" = "all" ]; then
            read -p "Are you sure you want to delete both pods? (y/n): " confirm
            if [ "$confirm" = "y" ]; then
                delete_pod dev
                delete_pod staging
            else
                echo "Cancelled"
            fi
        else
            read -p "Are you sure you want to delete $POD_NAME pod? (y/n): " confirm
            if [ "$confirm" = "y" ]; then
                delete_pod $POD_NAME
            else
                echo "Cancelled"
            fi
        fi
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
