package id.livingatlas.researchservice.shared.event;

import java.time.OffsetDateTime;
import java.util.UUID;

public record ResearchDomainEvent(
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
    public ResearchDomainEvent {
        eventId = UUID.randomUUID();
        occurredAt = OffsetDateTime.now();
        producer = "research-service";
        eventVersion = 1;
    }

    public ResearchDomainEvent(String eventType, String aggregateType, UUID aggregateId, Object data) {
        this(null, eventType, 1, null, "research-service", aggregateType, aggregateId, data, null, null);
    }
}