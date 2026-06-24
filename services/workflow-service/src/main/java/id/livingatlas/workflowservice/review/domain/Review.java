package id.livingatlas.workflowservice.review.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "reviews", schema = "workflow")
@Getter
@Setter
@NoArgsConstructor
public class Review {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "target_type", nullable = false, length = 100)
    private String targetType;

    @Column(name = "target_id", nullable = false)
    private UUID targetId;

    @Column(name = "reviewer_id")
    private UUID reviewerId;

    @Column(name = "requested_by")
    private UUID requestedBy;

    @Column(length = 50)
    private String status;

    @Column(columnDefinition = "text")
    private String notes;

    @Column(length = 50)
    private String priority;

    @Column(name = "tenant_id")
    private UUID tenantId;

    @Column(name = "workspace_id")
    private UUID workspaceId;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "created_by")
    private UUID createdBy;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    @Column(name = "updated_by")
    private UUID updatedBy;

    @Column(name = "approved_at")
    private OffsetDateTime approvedAt;

    @Column(name = "rejected_at")
    private OffsetDateTime rejectedAt;
}