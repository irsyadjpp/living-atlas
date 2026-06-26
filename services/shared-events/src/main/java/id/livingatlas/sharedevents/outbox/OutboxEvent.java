package id.livingatlas.sharedevents.outbox;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Transactional outbox entity.
 * <p>
 * Domain events are written to this table within the same database transaction
 * as the business operation that produced them. A background poller reads
 * unpublished events and forwards them to Redpanda.
 * <p>
 * This ensures at-least-once delivery: if the application crashes after
 * committing the transaction but before publishing to Redpanda, the event
 * is picked up on the next poll cycle.
 *
 * @see OutboxEventPublisher
 */
@Entity
@Table(name = "outbox_events", schema = "events")
@Getter
@Setter
@NoArgsConstructor
@ToString
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class OutboxEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @EqualsAndHashCode.Include
    private UUID id;

    @Column(name = "event_id", nullable = false, unique = true)
    private UUID eventId;

    @Column(name = "event_type", nullable = false, length = 255)
    private String eventType;

    @Column(name = "event_version", nullable = false)
    private int eventVersion = 1;

    @Column(name = "aggregate_type", nullable = false, length = 100)
    private String aggregateType;

    @Column(name = "aggregate_id", nullable = false)
    private UUID aggregateId;

    @Column(name = "payload", nullable = false, columnDefinition = "jsonb")
    private String payload;

    @Column(name = "metadata_json", columnDefinition = "jsonb")
    private String metadataJson;

    @Column(name = "topic", nullable = false, length = 255)
    private String topic;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 50)
    private OutboxStatus status = OutboxStatus.PENDING;

    @Column(name = "published_at")
    private OffsetDateTime publishedAt;

    @Column(name = "retry_count", nullable = false)
    private int retryCount = 0;

    @Column(name = "last_error", columnDefinition = "text")
    private String lastError;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "processed_at")
    private OffsetDateTime processedAt;

    public enum OutboxStatus {
        PENDING,
        PUBLISHED,
        FAILED,
        DEAD_LETTER
    }
}