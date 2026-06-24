# ADR-004: Event-Driven Architecture with Transactional Outbox

## Status
Accepted

## Context
Multiple services need to react to state changes (e.g., story created → trigger knowledge extraction → trigger embedding generation). Direct REST calls create temporal coupling and reduce resilience. Full Kafka/Redpanda infrastructure adds operational overhead at initial scale.

## Decision
We will implement event-driven architecture using a Transactional Outbox pattern, starting with database-polling and evolving to Redpanda when volume demands.

## Rationale
- **Decoupling**: Services react to events without blocking callers
- **Reliability**: Transactional outbox guarantees at-least-once delivery
- **Evolution path**: Same event schema works with Redpanda migration
- **Observability**: Event log provides audit trail and replay capability

## Consequences
### Positive
- Loose coupling between services
- Built-in audit trail via event log
- Replay capability for projection rebuilds
- Smooth migration path to Redpanda

### Negative
- Eventual consistency between services
- Requires idempotent event handlers
- Outbox polling adds latency (~100ms–1s)

## Event Schema
```json
{
  "eventId": "uuid",
  "eventType": "StoryCreated",
  "eventVersion": 1,
  "occurredAt": "2026-06-20T01:00:00Z",
  "producer": "content-service",
  "aggregateType": "Story",
  "aggregateId": "uuid",
  "data": {},
  "metadata": {
    "tenantId": "uuid",
    "workspaceId": "uuid",
    "correlationId": "uuid",
    "causationId": "uuid"
  }
}
```

## Outbox Table
```sql
CREATE TABLE system.outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(255) NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ
);
```

## Migration Path
1. **Phase 1**: Transactional Outbox + Polling Publisher
2. **Phase 2**: Transactional Outbox + Redpanda Producer (dual-write)
3. **Phase 3**: Redpanda-only, outbox table deprecated

## References
- plan.md - Event Architecture
- BACKEND-PRD.md §2.3 Event Driven Ready, §5 Event Architecture