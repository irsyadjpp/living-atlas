package id.livingatlas.sharedevents;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Base event record for communication between Spring Boot services ('services/')
 * and AI platform ('ai-platform/').
 * 
 * Produced/consumed via Redpanda (Kafka-compatible).
 */
public record AiBridgeEvent(
    UUID eventId,
    String eventType,
    int eventVersion,
    OffsetDateTime occurredAt,
    String producer,
    UUID aggregateId,
    String dataJson,
    UUID tenantId,
    UUID correlationId
) {
    public AiBridgeEvent {
        eventId = UUID.randomUUID();
        occurredAt = OffsetDateTime.now();
        eventVersion = 1;
    }

    public AiBridgeEvent(String eventType, String producer, UUID aggregateId, String dataJson) {
        this(null, eventType, 1, null, producer, aggregateId, dataJson, null, null);
    }

    public AiBridgeEvent(String eventType, String producer, UUID aggregateId, String dataJson, UUID tenantId) {
        this(null, eventType, 1, null, producer, aggregateId, dataJson, tenantId, null);
    }
}