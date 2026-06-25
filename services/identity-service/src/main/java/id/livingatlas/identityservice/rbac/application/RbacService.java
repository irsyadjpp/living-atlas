package id.livingatlas.identityservice.rbac.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.identityservice.rbac.domain.model.Permission;
import id.livingatlas.identityservice.rbac.domain.model.Role;
import id.livingatlas.identityservice.rbac.domain.model.RolePermission;
import id.livingatlas.identityservice.rbac.domain.model.RolePermissionId;
import id.livingatlas.identityservice.rbac.domain.PermissionRepository;
import id.livingatlas.identityservice.rbac.domain.RolePermissionRepository;
import id.livingatlas.identityservice.rbac.domain.RoleRepository;
import id.livingatlas.identityservice.rbac.domain.UserRoleRepository;
import id.livingatlas.identityservice.tenant.domain.TenantRepository;
import id.livingatlas.identityservice.tenant.domain.WorkspaceRepository;
import id.livingatlas.identityservice.tenant.domain.model.Tenant;
import id.livingatlas.identityservice.tenant.domain.model.Workspace;
import id.livingatlas.identityservice.user.domain.UserRepository;
import id.livingatlas.identityservice.user.domain.model.User;
import id.livingatlas.identityservice.user.domain.model.UserRole;
import id.livingatlas.identityservice.user.domain.model.UserRoleId;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RbacService {

    private final RoleRepository roleRepository;
    private final PermissionRepository permissionRepository;
    private final RolePermissionRepository rolePermissionRepository;
    private final UserRoleRepository userRoleRepository;
    private final UserRepository userRepository;
    private final TenantRepository tenantRepository;
    private final WorkspaceRepository workspaceRepository;

    @Transactional
    public Role createRole(String code, String name, String description) {
        Role role = new Role(code, name);
        role.setDescription(description);
        return roleRepository.save(role);
    }

    @Transactional
    public Role updateRole(UUID roleId, String name, String description) {
        Role role = roleRepository.findById(roleId)
                .orElseThrow(() -> ApiException.notFound("Role not found: " + roleId));
        if (name != null) role.setName(name);
        if (description != null) role.setDescription(description);
        return roleRepository.save(role);
    }

    @Transactional(readOnly = true)
    public List<Role> getAllRoles() {
        return roleRepository.findAll();
    }

    @Transactional(readOnly = true)
    public Role getRole(UUID roleId) {
        return roleRepository.findById(roleId)
                .orElseThrow(() -> ApiException.notFound("Role not found: " + roleId));
    }

    @Transactional
    public Permission createPermission(String code, String resourceType, String action, String description) {
        Permission permission = new Permission(code, resourceType, action);
        permission.setDescription(description);
        return permissionRepository.save(permission);
    }

    @Transactional(readOnly = true)
    public List<Permission> getAllPermissions() {
        return permissionRepository.findAll();
    }

    @Transactional
    public void assignPermissionToRole(UUID roleId, UUID permissionId) {
        Role role = roleRepository.findById(roleId)
                .orElseThrow(() -> ApiException.notFound("Role not found"));
        Permission permission = permissionRepository.findById(permissionId)
                .orElseThrow(() -> ApiException.notFound("Permission not found"));

        if (rolePermissionRepository.findById(new RolePermissionId(roleId, permissionId)).isEmpty()) {
            rolePermissionRepository.save(new RolePermission(role, permission));
        }
    }

    @Transactional
    public void removePermissionFromRole(UUID roleId, UUID permissionId) {
        rolePermissionRepository.deleteById(new RolePermissionId(roleId, permissionId));
    }

    @Transactional
    public void assignRoleToUser(UUID userId, UUID roleId, UUID tenantId, UUID workspaceId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> ApiException.notFound("User not found"));
        Role role = roleRepository.findById(roleId)
                .orElseThrow(() -> ApiException.notFound("Role not found"));

        Tenant tenant = tenantId != null ? tenantRepository.findById(tenantId).orElse(null) : null;
        Workspace workspace = workspaceId != null ? workspaceRepository.findById(workspaceId).orElse(null) : null;

        UserRoleId id = new UserRoleId(userId, roleId, tenantId, workspaceId);
        if (userRoleRepository.findById(id).isEmpty()) {
            UserRole userRole = new UserRole(user, role, tenant, workspace);
            userRoleRepository.save(userRole);
        }
    }

    @Transactional
    public void removeRoleFromUser(UUID userId, UUID roleId, UUID tenantId, UUID workspaceId) {
        userRoleRepository.deleteById(new UserRoleId(userId, roleId, tenantId, workspaceId));
    }

    @Transactional(readOnly = true)
    public List<Permission> getPermissionsForUser(UUID userId) {
        List<UserRole> userRoles = userRoleRepository.findAllByUserId(userId);
        List<UUID> roleIds = userRoles.stream()
                .map(ur -> ur.getRole().getId())
                .distinct()
                .collect(Collectors.toList());

        return roleIds.stream()
                .flatMap(rid -> rolePermissionRepository.findAllByRoleId(rid).stream())
                .map(RolePermission::getPermission)
                .distinct()
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<Permission> getPermissionsForUserInTenant(UUID userId, UUID tenantId) {
        List<UserRole> userRoles = userRoleRepository.findAllByUserIdAndTenantId(userId, tenantId);
        List<UUID> roleIds = userRoles.stream()
                .map(ur -> ur.getRole().getId())
                .distinct()
                .toList();

        return roleIds.stream()
                .flatMap(rid -> rolePermissionRepository.findAllByRoleId(rid).stream())
                .map(RolePermission::getPermission)
                .distinct()
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public boolean hasPermission(UUID userId, String permissionCode) {
        return getPermissionsForUser(userId).stream()
                .anyMatch(p -> p.getCode().equals(permissionCode));
    }

    @Transactional(readOnly = true)
    public boolean hasPermissionInTenant(UUID userId, UUID tenantId, String permissionCode) {
        return getPermissionsForUserInTenant(userId, tenantId).stream()
                .anyMatch(p -> p.getCode().equals(permissionCode));
    }
}