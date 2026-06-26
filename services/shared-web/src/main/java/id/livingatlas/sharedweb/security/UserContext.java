package id.livingatlas.sharedweb.security;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Authenticated user context populated from JWT at request time.
 * <p>
 * This is the primary security context object used by the
 * {@link id.livingatlas.identityservice.abac.domain.AbacPolicyEngine}
 * for RBAC and ABAC authorization decisions.
 *
 * @see ResourceContext
 * @see id.livingatlas.sharedweb.annotation.AuthorizationRequired
 */
@Data
@Builder
@AllArgsConstructor
public class UserContext {

    private UUID userId;
    private UUID tenantId;
    private String username;
    private String email;

    private Set<String> roles;
    private Set<String> permissions;
    private Set<UUID> workspaceIds;
    private boolean isSystemAdmin;

    private Map<String, Object> attributes;

    // Derived checks

    public boolean hasRole(String role) {
        return roles != null && roles.contains(role);
    }

    public boolean hasPermission(String permission) {
        return permissions != null && permissions.contains(permission);
    }

    public boolean isMemberOfWorkspace(UUID workspaceId) {
        return workspaceIds != null && workspaceIds.contains(workspaceId);
    }

    public boolean hasAnyRole(String... roleNames) {
        if (roles == null) return false;
        for (String role : roleNames) {
            if (roles.contains(role)) return true;
        }
        return false;
    }
}