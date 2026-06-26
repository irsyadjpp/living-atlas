package id.livingatlas.identityservice.rbac.api;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.rbac.domain.model.Role;
import id.livingatlas.identityservice.rbac.domain.RoleRepository;
import id.livingatlas.identityservice.rbac.domain.PermissionRepository;
import id.livingatlas.identityservice.rbac.domain.RolePermissionRepository;
import id.livingatlas.identityservice.rbac.domain.model.Permission;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/roles")
@RequiredArgsConstructor
public class RoleController {
    private final RoleRepository roleRepo;
    private final PermissionRepository permissionRepo;
    private final RolePermissionRepository rolePermissionRepo;

    @GetMapping
    public ResponseEntity<PagedResponse<Role>> listRoles(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(roleRepo.findAll(PageRequest.of(page, size))));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Role>> getRole(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(roleRepo.findById(id).orElseThrow()));
    }

    @PostMapping
    public ResponseEntity<ApiResponse<Role>> createRole(@RequestBody Map<String, String> request) {
        String code = request.get("code");
        String name = request.get("name");
        String description = request.get("description");

        Role role = new Role(code, name);
        role.setDescription(description);
        Role saved = roleRepo.save(role);

        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(saved));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Role>> updateRole(@PathVariable UUID id, @RequestBody Map<String, String> request) {
        Role role = roleRepo.findById(id)
                .orElseThrow(() -> ApiException.notFound("Role not found"));

        if (request.containsKey("name")) {
            role.setName(request.get("name"));
        }
        if (request.containsKey("description")) {
            role.setDescription(request.get("description"));
        }

        return ResponseEntity.ok(ApiResponse.success(roleRepo.save(role)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteRole(@PathVariable UUID id) {
        Role role = roleRepo.findById(id)
                .orElseThrow(() -> ApiException.notFound("Role not found"));
        roleRepo.delete(role);
        return ResponseEntity.ok(ApiResponse.noContent());
    }

    @GetMapping("/{id}/permissions")
    public ResponseEntity<ApiResponse<List<Permission>>> getRolePermissions(@PathVariable UUID id) {
        List<Permission> permissions = rolePermissionRepo.findAllByRoleId(id).stream()
                .map(rp -> rp.getPermission())
                .collect(Collectors.toList());
        return ResponseEntity.ok(ApiResponse.success(permissions));
    }

    @PostMapping("/{id}/permissions")
    public ResponseEntity<ApiResponse<Void>> assignPermissions(@PathVariable UUID id, @RequestBody List<UUID> permissionIds) {
        Role role = roleRepo.findById(id)
                .orElseThrow(() -> ApiException.notFound("Role not found"));

        List<Permission> permissions = permissionRepo.findAllById(permissionIds);

        // Clear existing and assign new (simplified)
        rolePermissionRepo.deleteAll(rolePermissionRepo.findAllByRoleId(id));
        permissions.forEach(permission -> {
            rolePermissionRepo.save(new id.livingatlas.identityservice.rbac.domain.model.RolePermission(role, permission));
        });

        return ResponseEntity.ok(ApiResponse.noContent());
    }
}
