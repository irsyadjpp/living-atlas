package id.livingatlas.identityservice.rbac.api;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.rbac.domain.PermissionRepository;
import id.livingatlas.identityservice.rbac.domain.model.Permission;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/permissions")
@RequiredArgsConstructor
public class PermissionController {
    private final PermissionRepository permissionRepo;

    @GetMapping
    public ResponseEntity<PagedResponse<Permission>> listPermissions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(permissionRepo.findAll(PageRequest.of(page, size))));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Permission>> getPermission(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(permissionRepo.findById(id).orElseThrow()));
    }

    @PostMapping
    public ResponseEntity<ApiResponse<Permission>> createPermission(@RequestBody Map<String, String> request) {
        String code = request.get("code");
        String name = request.get("name");
        String description = request.get("description");
        String resource = request.get("resource");
        String action = request.get("action");

        Permission permission = new Permission(code, name, resource, action);
        permission.setDescription(description);
        Permission saved = permissionRepo.save(permission);

        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(saved));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Permission>> updatePermission(@PathVariable UUID id, @RequestBody Map<String, String> request) {
        Permission permission = permissionRepo.findById(id)
                .orElseThrow(() -> ApiException.notFound("Permission not found"));

        if (request.containsKey("name")) {
            permission.setName(request.get("name"));
        }
        if (request.containsKey("description")) {
            permission.setDescription(request.get("description"));
        }

        return ResponseEntity.ok(ApiResponse.success(permissionRepo.save(permission)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deletePermission(@PathVariable UUID id) {
        Permission permission = permissionRepo.findById(id)
                .orElseThrow(() -> ApiException.notFound("Permission not found"));
        permissionRepo.delete(permission);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}
