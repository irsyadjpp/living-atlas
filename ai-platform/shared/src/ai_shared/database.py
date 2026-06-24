"""PostgreSQL connection pool and database helpers.

Provides async connection management using asyncpg with connection pooling.
"""

import asyncpg
import structlog
from typing import Optional
from ai_shared.config import ServiceConfig

logger = structlog.get_logger(__name__)


class Database:
    """PostgreSQL database manager with connection pooling."""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Initialize the connection pool."""
        self.pool = await asyncpg.create_pool(
            host=self.config.pg_host,
            port=self.config.pg_port,
            user=self.config.pg_user,
            password=self.config.pg_password,
            database=self.config.pg_database,
            min_size=self.config.pg_min_connections,
            max_size=self.config.pg_max_connections,
        )
        logger.info(
            "database_connected",
            host=self.config.pg_host,
            database=self.config.pg_database,
        )

    async def disconnect(self) -> None:
        """Close all connections in the pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("database_disconnected")

    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status string."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        """Fetch multiple rows."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch a single value."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute_many(self, query: str, args_list: list[tuple]) -> None:
        """Execute the same query with multiple parameter sets."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)

    async def health_check(self) -> bool:
        """Check if database is responsive."""
        try:
            if self.pool:
                async with self.pool.acquire() as conn:
                    val = await conn.fetchval("SELECT 1")
                    return val == 1
            return False
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False