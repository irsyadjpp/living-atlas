package id.livingatlas.sharedevents.outbox;

import com.fasterxml.jackson.databind.ObjectMapper;
import id.livingatlas.sharedevents.DomainEvent;
import id.livingatlas.sharedevents.EventMetadata;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * Publishes domain events to the transactional outbox.
 * <p>
 * This publisher writes events to the {@code outbox_events} table within the
 * same database transaction as the business operation. A background scheduler
 * ({@link OutboxPollerScheduler}) then reads pending events and publishes
 * them to Redpanda.
 * <p>
 * Usage:
 * <pre>{@code
 * @Transactional
 * public void createStory(CreateStoryCommand cmd) {
 *     Story story = storyRepository.save(new Story(cmd));
 *     outboxEventPublisher.publish(new StoryCreatedEvent(story));
 * }
 * }</pre>
 *
 * @see OutboxEvent
 * @see OutboxPollerScheduler
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class OutboxEventPublisher {

    private final OutboxEventRepository outboxEventRepository;
    private final ObjectMapper objectMapper;

    /**
     * Write a domain event to the transactional outbox.
     * This call happens within the caller's {@code @Transactional} boundary.
     *
     * @param event    the domain event to publish
     * @param topic    the Redpanda topic to publish to
     */
    @Transactional
    public void publish(DomainEvent event, String topic) {
        var outboxEvent = new OutboxEvent();
        outboxEvent.setEventId(event.getEventId());
        outboxEvent.setEventType(event.getEventType());
        outboxEvent.setEventVersion(event.getEventVersion());
        outboxEvent.setAggregateType(event.getAggregateType());
        outboxEvent.setAggregateId(event.getAggregateId());
        outboxEvent.setPayload(event.toJson());

        // Serialize metadata
        if (event.getMetadata() != null) {
            try {
                outboxEvent.setMetadataJson(objectMapper.writeValueAsString(event.getMetadata()));
            } catch (Exception e) {
                log.warn("Failed to serialize event metadata for event {}: {}",
                        event.getEventId(), e.getMessage());
            }
        }

        outboxEvent.setTopic(topic);
        outboxEvent.setStatus(OutboxEvent.OutboxStatus.PENDING);

        outboxEventRepository.save(outboxEvent);

        log.debug("Published event {} to outbox (topic: {}, aggregate: {})",
                event.getEventType(), topic, event.getAggregateId());
    }

    /**
     * Convenience method that publishes an event and infers the topic
     * from the event type using the EventTopics constants.
     */
    @Transactional
    public void publish(DomainEvent event) {
        String topic = resolveTopic(event);
        publish(event, topic);
    }

    /**
     * Resolve the Redpanda topic for a domain event based on its type.
     * <p>
     * Convention: domain events from the backend are published to topics
     * following the pattern {@code {domain}.evt}. AI Platform events
     * use the patterns defined in {@code EventTopics}.
     */
    private String resolveTopic(DomainEvent event) {
        String type = event.getEventType();

        // Map event types to topics based on EventTopics conventions
        if (type.startsWith("Story")) {
            return "content.evt";
        } else if (type.startsWith("Source")) {
            return "content.evt";
        } else if (type.startsWith("Transcript")) {
            return "content.evt";
        } else if (type.startsWith("Knowledge")) {
            return "knowledge.evt";
        } else if (type.startsWith("Article")) {
            return "content.evt";
        } else if (type.startsWith("Review") || type.startsWith("Publication")) {
            return "workflow.evt";
        } else if (type.startsWith("Collection") || type.startsWith("Annotation") || type.startsWith("Export")) {
            return "research.evt";
        } else if (type.startsWith("User") || type.startsWith("Role") || type.startsWith("Tenant")) {
            return "identity.evt";
        }

        // Default fallback
        return "content.evt";
    }
}