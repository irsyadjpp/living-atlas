.PHONY: help dev dev-db migrate seed test lint build clean

help:
	@echo "Living Atlas — AI Platform"
	@echo ""
	@echo "Usage:"
	@echo "  make dev          Start all services in development mode"
	@echo "  make dev-db       Start only infrastructure (postgres, redpanda, etc.)"
	@echo "  make migrate      Run database migrations"
	@echo "  make seed         Seed initial taxonomy data"
	@echo "  make test         Run all tests"
	@echo "  make lint         Lint all services"
	@echo "  make build        Build all Podman images"
	@echo "  make clean        Stop and remove all containers"

COMPOSE_FILE = ../infrastructure/compose.yml

dev:
	podman-compose -f $(COMPOSE_FILE) up --build

dev-db:
	podman-compose -f $(COMPOSE_FILE) up postgres redpanda redis weaviate

migrate:
	cd shared && python -m ai_shared.db.migrate

seed:
	cd shared && python -m ai_shared.db.seed

test:
	for dir in shared ingestion-service extraction-service normalization-service validation-service enrichment-service embedding-service article-service orchestration-service; do \
		cd $$dir && python -m pytest -v && cd ..; \
	done

lint:
	for dir in shared ingestion-service extraction-service normalization-service validation-service enrichment-service embedding-service article-service orchestration-service; do \
		cd $$dir && ruff check . && cd ..; \
	done

build:
	podman-compose -f $(COMPOSE_FILE) build

clean:
	podman-compose -f $(COMPOSE_FILE) down -v
