package id.livingatlas.identityservice.user.domain.model;

import id.livingatlas.identityservice.rbac.domain.model.Role;
import id.livingatlas.identityservice.tenant.domain.model.Tenant;
import id.livingatlas.identityservice.tenant.domain.model.Workspace;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Getter
@Setter
@ToString
@EqualsAndHashCode
@NoArgsConstructor
@Table(name = "user_roles", schema = "iam")
public class UserRole {

    @EmbeddedId
    private UserRoleId id;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("userId")
    @JoinColumn(name = "user_id", nullable = false)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("roleId")
    @JoinColumn(name = "role_id", nullable = false)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private Role role;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("tenantId")
    @JoinColumn(name = "tenant_id", nullable = false)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private Tenant tenant;

    @ManyToOne(fetch = FetchType.LAZY)
    @MapsId("workspaceId")
    @JoinColumn(name = "workspace_id")
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private Workspace workspace;

    @Setter(AccessLevel.NONE)
    @Column(name = "assigned_at", nullable = false, updatable = false)
    @CreationTimestamp
    private OffsetDateTime assignedAt;

    @Column(name = "assigned_by")
    private UUID assignedBy;

    public UserRole(User user, Role role, Tenant tenant, Workspace workspace) {
        this.user = user;
        this.role = role;
        this.tenant = tenant;
        this.workspace = workspace;
        this.id = new UserRoleId(
            user != null ? user.getId() : null,
            role != null ? role.getId() : null,
            tenant != null ? tenant.getId() : null,
            workspace != null ? workspace.getId() : null
        );
    }
}