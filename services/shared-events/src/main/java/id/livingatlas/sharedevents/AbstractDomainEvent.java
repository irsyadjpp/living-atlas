package id.livingatlas.sharedevents;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.Getter;

import java.time.Instant;
import java.util.UUID;

/**
 * Abstract base class for domain events providing common serialization.
 * <p>
 * Extend this class for each domain event and implement getData()
 * to return the event-specific payload for serialization.
 */
@Getter
public abstract class AbstractDomainEvent implements DomainEvent {

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    private final UUID eventId;
    private final String eventType;
    private final int eventVersion;
    private final Instant occurredAt;
    private final String producer;
    private final String aggregateType;
    private final UUID aggregateId;
    private final EventMetadata metadata;

    protected AbstractDomainEvent(
            String eventType,
            int eventVersion,
            String producer,
            String aggregateType,
            UUID aggregateId,
            EventMetadata metadata
    ) {
        this.eventId = UUID.randomUUID();
        this.eventType = eventType;
        this.eventVersion = eventVersion;
        this.occurredAt = Instant.now();
        this.producer = producer;
        this.aggregateType = aggregateType;
        this.aggregateId = aggregateId;
        this.metadata = metadata;
    }

    /**
     * Returns the event-specific payload to be serialized into the outbox.
     */
    public abstract Object getData();

    @Override
    public String toJson() {
        try {
            return MAPPER.writeValueAsString(new EventEnvelope(this, getData()));
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize event: " + getEventType(), e);
        }
    }

    /**
     * Envelope that wraps event metadata with payload for serialization.
     */
    @Getter
    private static class EventEnvelope {
        private final UUID eventId;
        private final String eventType;
        private final int eventVersion;
        private final Instant occurredAt;
        private final String producer;
        private final String aggregateType;
        private final UUID aggregateId;
        private final Object data;
        private final EventMetadata metadata;

        EventEnvelope(AbstractDomainEvent event, Object data) {
            this.eventId = event.getEventId();
            this.eventType = event.getEventType();
            this.eventVersion = event.getEventVersion();
            this.occurredAt = event.getOccurredAt();
            this.producer = event.getProducer();
            this.aggregateType = event.getAggregateType();
            this.aggregateId = event.getAggregateId();
            this.data = data;
            this.metadata = event.getMetadata();
        }
    }
}