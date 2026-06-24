"""Enrichment Service — FastAPI Application Entry Point (Updated for 3-Stage Pipeline)."""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_shared.config import ServiceConfig
from ai_shared.database import Database
from ai_shared.logging import configure_logging
from ai_shared.metrics import service_health

from enrichment.application.service import EnrichmentService

logger = structlog.get_logger(__name__)
config = ServiceConfig(service_name="enrichment-service")
db = Database(config)
enrichment_service: EnrichmentService = None
event_integration = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(config.log_level)
    
    # Connect to database
    await db.connect()
    
    # Initialize enrichment service (3-stage pipeline)
    global enrichment_service
    enrichment_service = EnrichmentService(db, config)
    try:
        await enrichment_service.start_event_producer()
        logger.info("event_producer_started")
    except Exception as e:
        logger.warning("event_producer_failed", error=str(e), message="Continuing without event producer")
    
    # Initialize event integration (optional)
    global event_integration
    try:
        from enrichment.infrastructure.events import EnrichmentEventIntegration
        event_integration = EnrichmentEventIntegration(config, db, enrichment_service)
        await event_integration.start()
        logger.info("event_integration_started")
    except Exception as e:
        logger.warning("event_integration_failed", error=str(e), message="Continuing without event integration")
        event_integration = None
    
    service_health.labels(service="enrichment-service").set(1)
    logger.info(
        "enrichment_service_started",
        port=config.service_port,
        pipeline="3-stage-canonicalization",
    )
    
    yield
    
    # Cleanup
    if event_integration:
        await event_integration.stop()
    if enrichment_service:
        await enrichment_service.stop_event_producer()
    await db.disconnect()
    service_health.labels(service="enrichment-service").set(0)
    logger.info("enrichment_service_stopped")


app = FastAPI(
    title="Enrichment Service",
    description="Transform transcripts into canonical cultural knowledge using 3-stage pipeline (Canonicalization → Normalization → Validation)",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    db_healthy = await db.health_check()
    event_healthy = event_integration is not None and event_integration._running
    return {
        "status": "healthy" if db_healthy and event_healthy else "degraded",
        "service": config.service_name,
        "version": "2.0.0",
        "pipeline": "3-stage-canonicalization",
        "database": "connected" if db_healthy else "disconnected",
        "event_integration": "running" if event_healthy else "stopped",
    }


@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return generate_latest()


@app.get("/")
async def root():
    return {
        "service": config.service_name,
        "version": "2.0.0",
        "pipeline": "3-stage-canonicalization",
        "docs": "/docs",
        "status": "operational" if event_integration and event_integration._running else "initializing",
    }