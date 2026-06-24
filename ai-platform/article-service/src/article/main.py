"""Article Service — FastAPI Application Entry Point (Updated for Canonical Story Input)."""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_shared.config import ServiceConfig
from ai_shared.database import Database
from ai_shared.logging import configure_logging
from ai_shared.metrics import service_health

from article.application.service import ArticleService
from article.infrastructure.events import ArticleEventIntegration

logger = structlog.get_logger(__name__)
config = ServiceConfig(service_name="article-service")
db = Database(config)
article_service: ArticleService = None
event_integration = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(config.log_level)
    
    # Connect to database
    await db.connect()
    
    # Initialize article service (uses canonical stories)
    global article_service
    article_service = ArticleService(db, config)
    
    # Initialize event integration (optional)
    global event_integration
    try:
        event_integration = ArticleEventIntegration(config, db, article_service)
        await event_integration.start()
        logger.info("event_integration_started")
    except Exception as e:
        logger.warning("event_integration_failed", error=str(e), message="Continuing without event integration")
        event_integration = None
    
    service_health.labels(service="article-service").set(1)
    logger.info(
        "article_service_started",
        port=config.service_port,
        input_type="canonical_story",
    )
    
    yield
    
    # Cleanup
    if event_integration:
        await event_integration.stop()
    await db.disconnect()
    service_health.labels(service="article-service").set(0)
    logger.info("article_service_stopped")


app = FastAPI(
    title="Article Service",
    description="Generate 4 article types from Validated Canonical Stories (narrative, knowledge, news, creative)",
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
        "input_type": "canonical_story",
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
        "input_type": "canonical_story",
        "docs": "/docs",
        "status": "operational" if event_integration and event_integration._running else "initializing",
    }