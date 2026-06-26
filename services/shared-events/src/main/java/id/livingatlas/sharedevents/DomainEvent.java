package id.livingatlas.sharedevents;

import java.time.Instant;
import java.util.UUID;

/**
 * Base interface for all domain events in the platform.
 * <p>
 * Every domain event carries:
 * <ul>
 *   <li>A globally unique event ID (for idempotency tracking)</li>
 *   <li>A timestamp of when the event occurred</li>
 *   <li>An event type string for routing and schema versioning</li>
 *   <li>An event version for schema evolution</li>
 *   <li>An aggregate type and ID for ordered processing per aggregate</li>
 *   <li>Standard metadata (tenant, workspace, correlation, causation)</li>
 * </ul>
 * <p>
 * All domain events are immutable once created. They are stored in the
 * transactional outbox and published to Redpanda for async processing.
 *
 * @see EventMetadata
 * @see BaseEvent
 */
public interface DomainEvent {

    /**
     * Globally unique identifier for this event instance.
     * Used for idempotency tracking in event handlers.
     */
    UUID getEventId();

    /**
     * The type of event (e.g., "StoryCreated", "ReviewApproved").
     * Used for routing to the correct handler and for schema versioning.
     */
    String getEventType();

    /**
     * Schema version for this event type.
     * Starts at 1. Incremented on breaking changes.
     */
    int getEventVersion();

    /**
     * ISO-8601 timestamp of when this event occurred.
     */
    Instant getOccurredAt();

    /**
     * The producer of this event (e.g., "content-service", "workflow-service").
     */
    String getProducer();

    /**
     * The type of aggregate that produced this event (e.g., "Story", "KnowledgeObject").
     * Used for partitioning — events for the same aggregate are delivered in order.
     */
    String getAggregateType();

    /**
     * The ID of the aggregate that produced this event.
     * Used as the partition key for ordered delivery.
     */
    UUID getAggregateId();

    /**
     * Standard metadata for tenant isolation, tracing, and causation tracking.
     */
    EventMetadata getMetadata();

    /**
     * Serialize this event to JSON for storage in the outbox and publication to Redpanda.
     */
    String toJson();
}