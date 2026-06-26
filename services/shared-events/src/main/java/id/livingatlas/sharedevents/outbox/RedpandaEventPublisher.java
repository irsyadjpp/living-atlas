package id.livingatlas.sharedevents.outbox;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;

/**
 * Publishes events from the outbox to Redpanda.
 * <p>
 * This is a simple implementation that logs events for development.
 * In production, this should be replaced with the Redpanda/Kafka client
 * (e.g., {@code spring-kafka} or Redpanda's Kafka-compatible producer).
 * <p>
 * The publisher is called by {@link OutboxPollerScheduler} for each
 * pending outbox event. It handles transient failures with retry
 * and delegates dead-letter decisions to the outbox repository.
 */
@Slf4j
@Component
public class RedpandaEventPublisher {

    @Value("${redpanda.bootstrap-servers:localhost:9092}")
    private String bootstrapServers;

    private boolean initialized = false;

    @PostConstruct
    public void init() {
        log.info("RedpandaEventPublisher configured for servers: {}", bootstrapServers);
        this.initialized = true;
    }

    /**
     * Publish a message to a Redpanda topic.
     *
     * @param topic   the target topic
     * @param key     the message key (used for partitioning)
     * @param payload the JSON payload
     * @throws Exception if publishing fails
     */
    public void publish(String topic, String key, String payload) throws Exception {
        if (!initialized) {
            throw new IllegalStateException("RedpandaEventPublisher not initialized");
        }

        // TODO: Replace with actual Redpanda/Kafka producer:
        // In production, inject a KafkaTemplate<String, String> and call:
        //   kafkaTemplate.send(topic, key, payload).get(5, TimeUnit.SECONDS);

        log.info("[REDPANDA] topic={} key={} payload={}", topic, key,
                payload.length() > 500 ? payload.substring(0, 500) + "..." : payload);

        // Simulate a transient failure for testing (remove in production):
        // if (Math.random() < 0.01) throw new RuntimeException("Simulated broker failure");
    }

    @PreDestroy
    public void destroy() {
        log.info("RedpandaEventPublisher shutting down");
        this.initialized = false;
    }
}