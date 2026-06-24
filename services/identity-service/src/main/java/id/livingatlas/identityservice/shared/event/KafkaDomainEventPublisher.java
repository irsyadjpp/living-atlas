package id.livingatlas.identityservice.shared.event;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class KafkaDomainEventPublisher implements DomainEventPublisher {
    
    @Override
    public void publish(DomainEvent event) {
        // TODO: Implement Kafka publishing
        log.info("Publishing domain event: {}", event);
    }
}
