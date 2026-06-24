"""Base configuration for all AI platform services.

Uses pydantic-settings to load configuration from environment variables
with the LA_ prefix. All services inherit from ServiceConfig.

Updated for PRD v2.0:
- Removed MinIO/S3 config
- Added third-party API keys
- Added Weaviate and Prefect config

Updated for Podman Integration:
- Added podman environment detection
- Automatic service discovery adaptation
- Support for both Docker and Podman environments
"""

import os
from pydantic_settings import BaseSettings


class ServiceConfig(BaseSettings):
    """Base configuration for AI platform services.

    All settings can be overridden via environment variables with LA_ prefix.
    Example: LA_PG_HOST=postgres, LA_KAFKA_BOOTSTRAP_SERVERS=redpanda:9092

    Automatically adapts to Podman environment when PODMAN_ENVIRONMENT=true.
    """

    # Service identity
    service_name: str = "unknown"
    service_port: int = 8000

    # Environment detection
    podman_environment: bool = False  # Set via PODMAN_ENVIRONMENT=true

    # PostgreSQL (defaults for Docker, auto-adapted for Podman)
    pg_host: str = "postgres"
    pg_port: int = 5432
    pg_database: str = "living_atlas"
    pg_user: str = "living_atlas"
    pg_password: str = "living_atlas"
    pg_min_connections: int = 2
    pg_max_connections: int = 10

    # RabbitMQ / Kafka (defaults for Docker, auto-adapted for Podman)
    kafka_bootstrap_servers: str = "redpanda:9092"
    kafka_consumer_group: str = "ai-platform"
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    # Redis (defaults for Docker, auto-adapted for Podman)
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_url: str = "redis://localhost:6379/0"

    # Third-party API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    google_application_credentials: str = ""  # For Google Cloud STT
    assemblyai_api_key: str = ""  # Fallback STT
    deepgram_api_key: str = ""  # Fallback STT

    # Weaviate (defaults for Docker, auto-adapted for Podman)
    weaviate_host: str = "weaviate"
    weaviate_port: int = 8080
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str = ""

    # Prefect (defaults for Docker, auto-adapted for Podman)
    prefect_host: str = "prefect-server"
    prefect_port: int = 4200
    prefect_api_url: str = "http://localhost:4200/api"

    # MinIO (for Podman environments)
    minio_host: str = "localhost"
    minio_port: int = 9000
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_console_url: str = ""

    # Logging
    log_level: str = "INFO"

    # Health
    health_check_interval: int = 30

    class Config:
        env_prefix = "LA_"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-detect podman environment if not explicitly set
        if os.getenv("PODMAN_ENVIRONMENT", "").lower() == "true":
            self.podman_environment = True
        self._adapt_for_podman()

    def _adapt_for_podman(self):
        """Adapt configuration for Podman environment."""
        if not self.podman_environment:
            return

        # Adapt service discovery from Docker network names to localhost + mapped ports
        # PostgreSQL: 5432 -> 6432
        if self.pg_host == "postgres":
            self.pg_host = "localhost"
            self.pg_port = 6432

        # RabbitMQ: 5672 -> 6672
        if self.rabbitmq_host == "rabbitmq":
            self.rabbitmq_host = "localhost"
            self.rabbitmq_port = 6672

        # Redis: 6379 -> 7379
        if self.redis_host == "redis":
            self.redis_host = "localhost"
            self.redis_port = 7379

        # Weaviate: 8080 -> 8081
        if self.weaviate_host == "weaviate":
            self.weaviate_host = "localhost"
            self.weaviate_port = 8081

        # Prefect: 4200 -> 4200 (same port, but localhost)
        if self.prefect_host == "prefect-server":
            self.prefect_host = "localhost"

        # MinIO: 9000 -> 10000
        if self.minio_port == 9000:
            self.minio_host = "localhost"
            self.minio_port = 10000

        # Update derived URLs
        self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"
        self.weaviate_url = f"http://{self.weaviate_host}:{self.weaviate_port}"
        self.prefect_api_url = f"http://{self.prefect_host}:{self.prefect_port}/api"

    @property
    def pg_dsn(self) -> str:
        """PostgreSQL connection string."""
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    @property
    def rabbitmq_url(self) -> str:
        """RabbitMQ connection string."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"

    @property
    def minio_url(self) -> str:
        """MinIO connection URL."""
        return f"http://{self.minio_host}:{self.minio_port}"