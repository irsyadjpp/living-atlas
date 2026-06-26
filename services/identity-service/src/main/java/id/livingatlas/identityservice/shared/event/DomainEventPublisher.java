package id.livingatlas.identityservice.shared.event;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class DomainEventPublisher {

    public void publish(DomainEvent event) {
        log.info("Domain event published: type={}, id={}", event.getEventType(), event.getEventId());
    }
}