"""Redpanda/Kafka producer and consumer helpers.

Provides async event publishing and consumption using aiokafka.
"""

import json
import structlog
import orjson
from typing import Callable, Awaitable, Optional
from uuid import UUID
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from pydantic import BaseModel
from ai_shared.config import ServiceConfig

logger = structlog.get_logger(__name__)


class EventProducer:
    """Async Kafka event producer."""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Initialize and start the producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.config.kafka_bootstrap_servers,
            value_serializer=lambda v: orjson.dumps(v),
            key_serializer=lambda k: str(k).encode() if k else None,
        )
        await self.producer.start()
        logger.info("kafka_producer_started")

    async def stop(self) -> None:
        """Stop the producer."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("kafka_producer_stopped")

    async def produce(
        self,
        topic: str,
        event: BaseModel | dict,
        key: Optional[str] = None,
    ) -> None:
        """Publish an event to the specified topic."""
        if not self.producer:
            raise RuntimeError("Producer not started")

        if isinstance(event, BaseModel):
            value = event.model_dump(mode="json")
        else:
            value = event

        await self.producer.send(
            topic=topic,
            value=value,
            key=key.encode() if key else None,
        )
        logger.debug("event_produced", topic=topic, key=key)

    async def produce_event(self, topic: str, event: BaseModel) -> None:
        """Publish a Pydantic event model to a topic."""
        await self.produce(topic, event, key=str(getattr(event, "video_id", getattr(event, "pipeline_id", None))))


class EventConsumer:
    """Async Kafka event consumer with handler registration."""

    def __init__(
        self,
        config: ServiceConfig,
        group_id: Optional[str] = None,
    ):
        self.config = config
        self.group_id = group_id or config.kafka_consumer_group
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.handlers: dict[str, list[Callable[[dict], Awaitable[None]]]] = {}

    def register_handler(
        self,
        topic: str,
        handler: Callable[[dict], Awaitable[None]],
    ) -> None:
        """Register a handler function for a topic."""
        if topic not in self.handlers:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)
        logger.info("handler_registered", topic=topic, handler=handler.__name__)

    async def start(self, topics: list[str]) -> None:
        """Start consuming from specified topics."""
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.config.kafka_bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: orjson.loads(v) if v else None,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self.consumer.start()
        logger.info("kafka_consumer_started", topics=topics, group=self.group_id)

    async def stop(self) -> None:
        """Stop the consumer."""
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
            logger.info("kafka_consumer_stopped")

    async def consume_loop(self) -> None:
        """Main consume loop — processes messages continuously."""
        if not self.consumer:
            raise RuntimeError("Consumer not started")

        try:
            async for msg in self.consumer:
                topic = msg.topic
                value = msg.value
                if not value:
                    continue

                handlers = self.handlers.get(topic, [])
                for handler in handlers:
                    try:
                        await handler(value)
                    except Exception as e:
                        logger.error(
                            "handler_failed",
                            topic=topic,
                            handler=handler.__name__,
                            error=str(e),
                        )
        except asyncio.CancelledError:
            logger.info("consume_loop_cancelled")
        finally:
            await self.stop()