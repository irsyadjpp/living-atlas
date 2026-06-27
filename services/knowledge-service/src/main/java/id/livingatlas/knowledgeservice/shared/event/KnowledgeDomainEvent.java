package id.livingatlas.knowledgeservice.shared.event;

import java.time.OffsetDateTime;
import java.util.UUID;

public record KnowledgeDomainEvent(
        UUID eventId,
        String eventType,
        int eventVersion,
        OffsetDateTime occurredAt,
        String producer,
        String aggregateType,
        UUID aggregateId,
        Object data,
        UUID tenantId,
        UUID correlationId
) {
    public KnowledgeDomainEvent {
        eventId = UUID.randomUUID();
        occurredAt = OffsetDateTime.now();
        producer = "knowledge-service";
        eventVersion = 1;
    }

    public KnowledgeDomainEvent(String eventType, String aggregateType, UUID aggregateId, Object data) {
        this(null, eventType, 1, null, "knowledge-service", aggregateType, aggregateId, data, null, null);
    }

    public KnowledgeDomainEvent(String eventType, String aggregateType, UUID aggregateId, Object data, UUID tenantId) {
        this(null, eventType, 1, null, "knowledge-service", aggregateType, aggregateId, data, tenantId, null);
    }
}