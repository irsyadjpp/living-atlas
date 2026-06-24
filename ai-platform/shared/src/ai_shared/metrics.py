"""Prometheus metrics for AI platform services."""

from prometheus_client import Counter, Histogram, Gauge, start_http_server


# Event counters
events_produced_total = Counter(
    "ai_events_produced_total",
    "Total number of events produced",
    ["service", "topic"],
)

events_consumed_total = Counter(
    "ai_events_consumed_total",
    "Total number of events consumed",
    ["service", "topic"],
)

# Job counters
jobs_started_total = Counter(
    "ai_jobs_started_total",
    "Total number of jobs started",
    ["service", "job_type"],
)

jobs_completed_total = Counter(
    "ai_jobs_completed_total",
    "Total number of jobs completed",
    ["service", "job_type", "status"],
)

# Pipeline metrics
pipeline_duration_seconds = Histogram(
    "ai_pipeline_duration_seconds",
    "Pipeline execution duration in seconds",
    ["pipeline_type"],
    buckets=[60, 120, 300, 600, 1800, 3600, 7200],
)

pipeline_steps_total = Counter(
    "ai_pipeline_steps_total",
    "Total number of pipeline steps",
    ["step_name", "status"],
)

# LLM metrics
llm_requests_total = Counter(
    "ai_llm_requests_total",
    "Total number of LLM requests",
    ["provider", "model", "extraction_type"],
)

llm_duration_seconds = Histogram(
    "ai_llm_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model"],
    buckets=[1, 5, 10, 30, 60, 120],
)

llm_tokens_total = Counter(
    "ai_llm_tokens_total",
    "Total tokens consumed by LLM requests",
    ["provider", "model", "token_type"],
)

# Storage metrics
storage_operations_total = Counter(
    "ai_storage_operations_total",
    "Total storage operations",
    ["operation", "bucket"],
)

storage_bytes_total = Counter(
    "ai_storage_bytes_total",
    "Total bytes transferred to/from storage",
    ["operation", "bucket"],
)

# System metrics
active_connections = Gauge(
    "ai_active_connections",
    "Number of active database connections",
    ["service"],
)

service_health = Gauge(
    "ai_service_health",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"],
)