package id.livingatlas.identityservice.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Getter
@Setter
@ToString
@EqualsAndHashCode
@NoArgsConstructor
@Table(name = "workspaces", schema = "tenant")
@SQLRestriction("is_deleted = false")
@SQLDelete(sql = "UPDATE tenant.workspaces SET is_deleted = true, deleted_at = now(), deleted_by = ? WHERE id = ?")
public class Workspace {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tenant_id", nullable = false)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private Tenant tenant;

    @Column(nullable = false)
    private String slug;

    @Column(nullable = false)
    private String name;

    @Column(name = "workspace_type", nullable = false)
    private String workspaceType;

    @Column(nullable = false)
    private String visibility = "private";

    @Column(columnDefinition = "TEXT")
    private String description;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb", nullable = false)
    private String metadata = "{}";

    @Setter(AccessLevel.NONE)
    @Column(name = "created_at", nullable = false, updatable = false)
    @CreationTimestamp
    private OffsetDateTime createdAt;

    @Column(name = "created_by")
    private UUID createdBy;

    @Setter(AccessLevel.NONE)
    @Column(name = "updated_at", nullable = false)
    @UpdateTimestamp
    private OffsetDateTime updatedAt;

    @Column(name = "updated_by")
    private UUID updatedBy;

    @Setter(AccessLevel.NONE)
    @Column(name = "deleted_at")
    private OffsetDateTime deletedAt;

    @Setter(AccessLevel.NONE)
    @Column(name = "deleted_by")
    private UUID deletedBy;

    @Setter(AccessLevel.NONE)
    @Version
    @Column(nullable = false)
    private Long version = 1L;

    @Setter(AccessLevel.NONE)
    @Column(name = "is_deleted", nullable = false)
    private Boolean isDeleted = false;

    public Workspace(Tenant tenant, String slug, String name, String workspaceType) {
        this.tenant = tenant;
        this.slug = slug;
        this.name = name;
        this.workspaceType = workspaceType;
        this.visibility = "private";
        this.metadata = "{}";
        this.version = 1L;
        this.isDeleted = false;
    }
}