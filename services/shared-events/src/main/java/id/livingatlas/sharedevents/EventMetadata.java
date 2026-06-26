package id.livingatlas.sharedevents;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

/**
 * Standard metadata carried by every domain event.
 * Enables tenant isolation, tracing, and causation tracking across async flows.
 *
 * @see BaseEvent
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EventMetadata {

    private UUID tenantId;
    private UUID workspaceId;
    private String correlationId;
    private String causationId;
    private String producer;

    /**
     * Creates metadata with auto-generated correlation and causation IDs.
     */
    public static EventMetadata create(UUID tenantId, UUID workspaceId, String producer) {
        return EventMetadata.builder()
                .tenantId(tenantId)
                .workspaceId(workspaceId)
                .correlationId(UUID.randomUUID().toString())
                .causationId(UUID.randomUUID().toString())
                .producer(producer)
                .build();
    }

    /**
     * Creates metadata that chains from a parent event (for causation tracking).
     */
    public static EventMetadata fromParent(EventMetadata parent, String producer) {
        return EventMetadata.builder()
                .tenantId(parent.getTenantId())
                .workspaceId(parent.getWorkspaceId())
                .correlationId(parent.getCorrelationId())
                .causationId(parent.getCausationId())
                .producer(producer)
                .build();
    }
}