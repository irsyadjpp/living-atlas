package id.livingatlas.sharedevents.outbox;

import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Background scheduler that polls the transactional outbox for pending events
 * and publishes them to Redpanda.
 * <p>
 * This is the reliable delivery mechanism for the event-driven architecture.
 * Events are published in batches with exponential backoff on failure.
 * After {@code maxRetries} failures, events are moved to DEAD_LETTER status
 * for manual review.
 * <p>
 * Poll interval: 100ms (configurable via {@code outbox.poller.interval-ms}).
 * Batch size: 100 (configurable via {@code outbox.poller.batch-size}).
 *
 * @see OutboxEvent
 * @see OutboxEventPublisher
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class OutboxPollerScheduler {

    private final OutboxEventRepository outboxEventRepository;
    private final RedpandaEventPublisher redpandaPublisher;

    @Value("${outbox.poller.batch-size:100}")
    private int batchSize;

    @Value("${outbox.poller.max-retries:5}")
    private int maxRetries;

    @PostConstruct
    public void init() {
        log.info("Outbox poller initialized: batchSize={}, maxRetries={}", batchSize, maxRetries);
    }

    /**
     * Polls the outbox for pending events and publishes them to Redpanda.
     * Runs every 100ms by default.
     */
    @Scheduled(fixedDelayString = "${outbox.poller.interval-ms:100}")
    @Transactional
    public void pollOutbox() {
        List<OutboxEvent> pendingEvents = outboxEventRepository.findPendingEventsLimited(batchSize);

        if (pendingEvents.isEmpty()) {
            return;
        }

        log.debug("Outbox poller found {} pending events", pendingEvents.size());

        for (OutboxEvent event : pendingEvents) {
            processEvent(event);
        }
    }

    private void processEvent(OutboxEvent event) {
        try {
            // Publish to Redpanda
            redpandaPublisher.publish(event.getTopic(), event.getEventId().toString(), event.getPayload());

            // Mark as published
            outboxEventRepository.markPublished(event.getId(), OffsetDateTime.now());

            log.trace("Published outbox event {} ({}) to topic {}",
                    event.getEventId(), event.getEventType(), event.getTopic());
        } catch (Exception e) {
            log.error("Failed to publish outbox event {} to topic {}: {}",
                    event.getEventId(), event.getTopic(), e.getMessage());

            // Record failure and potentially move to dead letter
            outboxEventRepository.handleFailure(
                    event.getId(),
                    e.getMessage(),
                    maxRetries,
                    OffsetDateTime.now()
            );

            if (event.getRetryCount() + 1 >= maxRetries) {
                log.warn("Outbox event {} moved to DEAD_LETTER after {} retries",
                        event.getEventId(), maxRetries);
            }
        }
    }
}