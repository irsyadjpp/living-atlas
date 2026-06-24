package id.livingatlas.identityservice.user.domain;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

import java.time.OffsetDateTime;
import java.util.UUID;

@Getter
@RequiredArgsConstructor
public class UserDomainEvent {
    private final UUID eventId = UUID.randomUUID();
    private final String eventType;
    private final int eventVersion = 1;
    private final OffsetDateTime occurredAt = OffsetDateTime.now();
    private final String producer = "identity-service";
    private final String aggregateType = "User";
    private final UUID aggregateId;
    private final Object data;
    private final UUID tenantId;
    private final UUID workspaceId;
    private final UUID correlationId;
    private final UUID causationId;
}