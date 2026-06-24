package id.livingatlas.identityservice.shared.event;

public interface DomainEventPublisher {
    void publish(DomainEvent event);
}