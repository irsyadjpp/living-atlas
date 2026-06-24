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
@Table(name = "tenants", schema = "tenant")
@SQLRestriction("is_deleted = false")
@SQLDelete(sql = "UPDATE tenant.tenants SET is_deleted = true, deleted_at = now(), deleted_by = ? WHERE id = ?")
public class Tenant {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String slug;

    @Column(nullable = false)
    private String name;

    @Column(name = "tenant_type", nullable = false, columnDefinition = "tenant.tenant_type")
    private TenantType tenantType;

    @Column(nullable = false, columnDefinition = "tenant.tenant_status")
    private TenantStatus status;

    @Column(name = "subscription_plan")
    private String subscriptionPlan;

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

    public Tenant(String slug, String name, TenantType tenantType) {
        this.slug = slug;
        this.name = name;
        this.tenantType = tenantType;
        this.status = TenantStatus.active;
        this.metadata = "{}";
        this.version = 1L;
        this.isDeleted = false;
    }
}