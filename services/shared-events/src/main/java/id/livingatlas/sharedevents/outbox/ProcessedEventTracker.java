package id.livingatlas.sharedevents.outbox;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Tracks processed events for idempotent event handling.
 * <p>
 * Event handlers should check {@link #isProcessed(UUID)} before processing
 * and call {@link #markProcessed(UUID)} after successful processing.
 * <p>
 * This prevents duplicate processing when Redpanda delivers the same
 * event multiple times (at-least-once delivery semantics).
 * <p>
 * Per ADR-003 Rule 8: Idempotent Event Handlers.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ProcessedEventTracker {

    private static final String TABLE_NAME = "events.processed_events";

    @PersistenceContext
    private EntityManager entityManager;

    /**
     * Check if an event has already been processed.
     *
     * @param eventId the unique event ID
     * @return true if the event was already processed
     */
    @Transactional(readOnly = true)
    public boolean isProcessed(UUID eventId) {
        Long count = (Long) entityManager
                .createNativeQuery(
                        "SELECT COUNT(*) FROM " + TABLE_NAME + " WHERE event_id = :eventId")
                .setParameter("eventId", eventId)
                .getSingleResult();
        return count > 0;
    }

    /**
     * Mark an event as processed.
     *
     * @param eventId the unique event ID
     */
    @Transactional
    public void markProcessed(UUID eventId) {
        entityManager.createNativeQuery(
                        "INSERT INTO " + TABLE_NAME + " (event_id, processed_at) VALUES (:eventId, :now) " +
                        "ON CONFLICT (event_id) DO NOTHING")
                .setParameter("eventId", eventId)
                .setParameter("now", OffsetDateTime.now())
                .executeUpdate();
    }
}