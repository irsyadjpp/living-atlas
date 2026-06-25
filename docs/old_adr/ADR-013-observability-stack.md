# ADR-013: Observability Stack

## Status
Accepted

## Context
The platform needs observability for debugging, performance monitoring, and business analytics. Multiple services (Spring Boot, Python, PostgreSQL, Neo4j, Weaviate) require a unified observability strategy.

## Decision
We adopt OpenTelemetry as the instrumentation standard, with Prometheus + Grafana for metrics, Loki for logging, and Tempo for tracing.

## Rationale
- **Vendor-neutral**: OpenTelemetry prevents lock-in to any observability backend
- **Unified instrumentation**: Single SDK for all services (Java, Python, Node.js)
- **Correlation**: Traces, metrics, and logs linked via trace IDs
- **Self-hosted**: Full stack runs on-premise or in-cloud

## Stack Components
| Component | Purpose | Implementation |
|-----------|---------|---------------|
| OpenTelemetry SDK | Instrumentation | Java agent, Python SDK, JS SDK |
| Prometheus | Metrics storage | Scrapes /metrics endpoints |
| Grafana | Visualization | Dashboards per service/domain |
| Loki | Log aggregation | Structured JSON logs |
| Tempo | Distributed tracing | Trace ID propagation |
| OpenTelemetry Collector | Aggregation gateway | Batch processing, filtering |

## Required Metrics
- **API**: Request rate, latency (p50/p95/p99), error rate, status codes
- **Database**: Connection pool, query latency, slow queries
- **Events**: Outbox queue depth, processing latency, failure rate
- **AI Pipeline**: Job duration, success/failure rate, model latency
- **Infrastructure**: CPU, memory, disk, network per container

## Logging Standard
```json
{
  "timestamp": "2026-06-20T01:00:00.000Z",
  "level": "INFO",
  "service": "content-service",
  "traceId": "abc123",
  "spanId": "def456",
  "message": "Story created",
  "attributes": {
    "storyId": "uuid",
    "tenantId": "uuid",
    "duration": 150
  }
}
```

## References
- BACKEND-PRD.md §8 Observability
- ai-platform/infrastructure/ - Existing observability configs