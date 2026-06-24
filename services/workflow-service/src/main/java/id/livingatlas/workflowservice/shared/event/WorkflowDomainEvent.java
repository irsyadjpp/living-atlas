package id.livingatlas.workflowservice.shared.event;

import java.time.OffsetDateTime;
import java.util.UUID;

public record WorkflowDomainEvent(
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
    public WorkflowDomainEvent {
        eventId = UUID.randomUUID();
        occurredAt = OffsetDateTime.now();
        producer = "workflow-service";
        eventVersion = 1;
    }

    public WorkflowDomainEvent(String eventType, String aggregateType, UUID aggregateId, Object data) {
        this(null, eventType, 1, null, "workflow-service", aggregateType, aggregateId, data, null, null);
    }
}