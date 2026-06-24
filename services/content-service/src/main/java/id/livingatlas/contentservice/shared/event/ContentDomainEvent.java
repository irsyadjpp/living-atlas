package id.livingatlas.contentservice.shared.event;

import java.time.OffsetDateTime;
import java.util.UUID;

public record ContentDomainEvent(
    UUID eventId,
    String eventType,
    int eventVersion,
    OffsetDateTime occurredAt,
    String producer,
    String aggregateType,
    UUID aggregateId,
    Object data,
    UUID tenantId,
    UUID workspaceId,
    UUID correlationId,
    UUID causationId
) {
    public ContentDomainEvent {
        eventId = UUID.randomUUID();
        occurredAt = OffsetDateTime.now();
        producer = "content-service";
        eventVersion = 1;
    }

    public ContentDomainEvent(String eventType, String aggregateType, UUID aggregateId, Object data) {
        this(null, eventType, 1, null, "content-service", aggregateType, aggregateId, data, null, null, null, null);
    }

    public ContentDomainEvent(String eventType, String aggregateType, UUID aggregateId, Object data, UUID tenantId) {
        this(null, eventType, 1, null, "content-service", aggregateType, aggregateId, data, tenantId, null, null, null);
    }
}