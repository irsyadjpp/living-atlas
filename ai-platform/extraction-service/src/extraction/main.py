"""Extraction Service — FastAPI Application Entry Point.

Updated for PRD v2.0:
- No WhisperX or local ASR models
- No GPU required
- No speaker diarization
- YouTube subtitles primary, Google STT fallback
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_shared.config import ServiceConfig
from ai_shared.database import Database
from ai_shared.logging import configure_logging
from ai_shared.metrics import service_health

logger = structlog.get_logger(__name__)
config = ServiceConfig(service_name="extraction-service")
db = Database(config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    configure_logging(config.log_level)
    await db.connect()
    service_health.labels(service="extraction-service").set(1)
    logger.info("extraction_service_started", port=config.service_port)
    yield
    await db.disconnect()
    service_health.labels(service="extraction-service").set(0)
    logger.info("extraction_service_stopped")


app = FastAPI(
    title="Extraction Service",
    description="Extract transcripts from YouTube subtitles or third-party STT APIs (no local ASR, no GPU)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    db_healthy = await db.health_check()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": config.service_name,
        "version": "0.1.0",
        "database": "connected" if db_healthy else "disconnected",
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return generate_latest()


@app.get("/")
async def root():
    return {
        "service": config.service_name,
        "version": "0.1.0",
        "docs": "/docs",
    }