"""Ingestion Service — Event-Driven Worker.

Per PRD v2.0 Queue Driven Architecture:
- NO REST API endpoints exposed
- Consumes source.submitted events from Redpanda
- Triggers YouTube crawling using yt-dlp
- Produces source.metadata.imported and transcript.imported events
"""

import structlog
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ai_shared.config import ServiceConfig
from ai_shared.database import Database
from ai_shared.logging import configure_logging
from ai_shared.metrics import service_health
from ai_shared.redpanda import EventConsumer, EventProducer

logger = structlog.get_logger(__name__)
config = ServiceConfig(service_name="ingestion-service")
db = Database(config)

# Global references for lifecycle management
event_consumer = None
event_producer = None
consume_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to DB + start event consumer."""
    global event_consumer, event_producer, consume_task
    
    configure_logging(config.log_level)
    await db.connect()
    
    # Initialize event producer (for producing results back)
    event_producer = EventProducer(config)
    await event_producer.start()
    
    # Initialize crawler service
    from ingestion.infrastructure.youtube import YouTubeClient
    from ingestion.application.crawler import CrawlerService
    from ingestion.events.producer import IngestionEventProducer
    
    youtube_client = YouTubeClient()
    crawler = CrawlerService(
        db=db,
        youtube_client=youtube_client,
        event_producer=event_producer,
    )
    
    # Initialize event consumer (for source.submitted events)
    from ingestion.events.consumer import IngestionEventConsumer
    
    raw_consumer = EventConsumer(config, group_id="ingestion-service")
    event_consumer = IngestionEventConsumer(
        db=db,
        crawler=crawler,
        event_consumer=raw_consumer,
    )
    
    await event_consumer.start()
    
    # Start consume loop in background
    async def run_consume_loop():
        try:
            await raw_consumer.consume_loop()
        except asyncio.CancelledError:
            logger.info("consume_loop_cancelled")
    
    consume_task = asyncio.create_task(run_consume_loop())
    
    service_health.labels(service="ingestion-service").set(1)
    logger.info("ingestion_service_started_event_driven", port=config.service_port)
    yield
    
    # Cleanup
    if consume_task:
        consume_task.cancel()
    if event_consumer:
        await event_consumer.stop()
    if event_producer:
        await event_producer.stop()
    await db.disconnect()
    service_health.labels(service="ingestion-service").set(0)
    logger.info("ingestion_service_stopped")


app = FastAPI(
    title="Ingestion Service (Event-Driven)",
    description="YouTube ingestion worker — consumes source.submitted events, no REST API",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    db_healthy = await db.health_check()
    consumer_running = event_consumer is not None and event_consumer._running
    return {
        "status": "healthy" if db_healthy and consumer_running else "degraded",
        "service": config.service_name,
        "version": "0.2.0",
        "mode": "event-driven",
        "database": "connected" if db_healthy else "disconnected",
        "consumer": "running" if consumer_running else "stopped",
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
        "version": "0.2.0",
        "mode": "event-driven",
        "consumes": "source.submitted",
        "produces": ["source.metadata.imported", "transcript.imported"],
        "docs": "/docs",
    }
