package id.livingatlas.sharedevents.outbox;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for the transactional outbox table.
 * <p>
 * Provides methods for the outbox publisher to poll pending events
 * and mark them as published or failed.
 */
@Repository
public interface OutboxEventRepository extends JpaRepository<OutboxEvent, UUID> {

    /**
     * Find pending events ordered by creation time, with a limit.
     * Uses a partial index on (status, created_at) for efficient polling.
     */
    @Query("SELECT e FROM OutboxEvent e WHERE e.status = 'PENDING' ORDER BY e.createdAt ASC")
    List<OutboxEvent> findPendingEvents();

    /**
     * Find pending events with batch size limit.
     */
    @Query(value = "SELECT e FROM OutboxEvent e WHERE e.status = 'PENDING' ORDER BY e.createdAt ASC")
    List<OutboxEvent> findPendingEventsLimited(@Param("limit") int limit);

    /**
     * Find a specific event by its domain event ID (for idempotency checks).
     */
    Optional<OutboxEvent> findByEventId(UUID eventId);

    /**
     * Mark an event as published.
     */
    @Modifying
    @Query("UPDATE OutboxEvent e SET e.status = 'PUBLISHED', e.publishedAt = :now WHERE e.id = :id")
    void markPublished(@Param("id") UUID id, @Param("now") OffsetDateTime now);

    /**
     * Increment retry count and optionally move to DEAD_LETTER.
     */
    @Modifying
    @Query("UPDATE OutboxEvent e SET e.retryCount = e.retryCount + 1, " +
           "e.lastError = :error, " +
           "e.status = CASE WHEN e.retryCount + 1 >= :maxRetries THEN 'DEAD_LETTER' ELSE 'PENDING' END, " +
           "e.processedAt = :now WHERE e.id = :id")
    void handleFailure(@Param("id") UUID id, @Param("error") String error,
                       @Param("maxRetries") int maxRetries, @Param("now") OffsetDateTime now);

    /**
     * Count pending events for monitoring.
     */
    long countByStatus(OutboxEvent.OutboxStatus status);
}