package id.livingatlas.identityservice.shared.event;

import java.time.Instant;
import java.util.UUID;

public class DomainEvent {

    private final UUID eventId;
    private final String eventType;
    private final Instant occurredAt;

    public DomainEvent(String eventType) {
        this.eventId = UUID.randomUUID();
        this.eventType = eventType;
        this.occurredAt = Instant.now();
    }

    public UUID getEventId() {
        return eventId;
    }

    public String getEventType() {
        return eventType;
    }

    public Instant getOccurredAt() {
        return occurredAt;
    }
}