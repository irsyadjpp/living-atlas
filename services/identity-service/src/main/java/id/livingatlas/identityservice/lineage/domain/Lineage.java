package id.livingatlas.identityservice.lineage.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "lineage", schema = "identity")
@Getter
@Setter
@NoArgsConstructor
public class Lineage {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "object_id", nullable = false)
    private UUID objectId;

    @Column(name = "object_type", nullable = false, length = 50)
    private String objectType;

    @Column(name = "parent_object_id")
    private UUID parentObjectId;

    @Column(name = "parent_object_type", length = 50)
    private String parentObjectType;

    @Column(name = "relationship_type", length = 50)
    private String relationshipType;

    @Column(columnDefinition = "text")
    private String description;

    @Column(name = "tenant_id")
    private UUID tenantId;

    @Setter(AccessLevel.NONE)
    @Column(name = "created_at", nullable = false, updatable = false)
    @CreationTimestamp
    private OffsetDateTime createdAt;
}