# ============================================================
# Living Atlas — Python AI Service (Generic)
# ============================================================
# Build:
#   docker build -f infrastructure/docker/python.Dockerfile \
#     --build-arg SERVICE_DIR=ingestion-service \
#     -t living-atlas/ingestion-service .
#
# Args: SERVICE_DIR = one of: ingestion-service, extraction-service,
#                         normalization-service, validation-service,
#                         enrichment-service, article-service,
#                         embedding-service, orchestration-service
# ============================================================

ARG PYTHON_VERSION=3.12-slim

# ---- Builder Stage ----
FROM python:${PYTHON_VERSION} AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install shared package first (Docker layer cache)
COPY ai-platform/shared/ ./ai-platform/shared/
RUN pip install --no-cache-dir -e ./ai-platform/shared

# Install service package
ARG SERVICE_DIR
COPY ai-platform/${SERVICE_DIR}/pyproject.toml ./ai-platform/${SERVICE_DIR}/
COPY ai-platform/${SERVICE_DIR}/src/ ./ai-platform/${SERVICE_DIR}/src/
RUN pip install --no-cache-dir -e ./ai-platform/${SERVICE_DIR}

# ---- Runtime Stage ----
FROM python:${PYTHON_VERSION}

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appuser /app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ARG SERVICE_MODULE
ENV SERVICE_MODULE=${SERVICE_MODULE}
USER appuser
CMD sh -c "python -m uvicorn ${SERVICE_MODULE}.main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 100"