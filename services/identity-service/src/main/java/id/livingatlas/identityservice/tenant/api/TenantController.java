package id.livingatlas.identityservice.tenant.api;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.tenant.domain.model.Tenant;
import id.livingatlas.identityservice.tenant.domain.model.TenantStatus;
import id.livingatlas.identityservice.tenant.domain.model.Workspace;
import id.livingatlas.identityservice.tenant.domain.TenantRepository;
import id.livingatlas.identityservice.tenant.domain.WorkspaceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/tenants")
@RequiredArgsConstructor
public class TenantController {
    private final TenantRepository tenantRepo;
    private final WorkspaceRepository workspaceRepo;

    @PostMapping
    public ResponseEntity<ApiResponse<Tenant>> createTenant(@RequestBody Tenant tenant) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(tenantRepo.save(tenant)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Tenant>> listTenants(@RequestParam(defaultValue="0") int page, @RequestParam(defaultValue="20") int size) {
        return ResponseEntity.ok(PagedResponse.from(tenantRepo.findAll(PageRequest.of(page, size))));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Tenant>> getTenant(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(tenantRepo.findById(id).orElseThrow()));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Tenant>> updateTenant(@PathVariable UUID id, @RequestBody Map<String, Object> updates) {
        Tenant tenant = tenantRepo.findById(id)
                .orElseThrow(() -> ApiException.notFound("Tenant not found"));

        if (updates.containsKey("name")) {
            tenant.setName((String) updates.get("name"));
        }
        if (updates.containsKey("description")) {
            tenant.setDescription((String) updates.get("description"));
        }
        if (updates.containsKey("subscriptionPlan")) {
            tenant.setSubscriptionPlan((String) updates.get("subscriptionPlan"));
        }
        if (updates.containsKey("metadata")) {
            tenant.setMetadata((String) updates.get("metadata"));
        }

        return ResponseEntity.ok(ApiResponse.success(tenantRepo.save(tenant)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> archiveTenant(@PathVariable UUID id) {
        Tenant tenant = tenantRepo.findById(id)
                .orElseThrow(() -> ApiException.notFound("Tenant not found"));
        tenant.setStatus(TenantStatus.archived);
        tenantRepo.save(tenant);
        return ResponseEntity.ok(ApiResponse.noContent());
    }

    @PostMapping("/{tenantId}/workspaces")
    public ResponseEntity<ApiResponse<Workspace>> createWorkspace(@PathVariable UUID tenantId, @RequestBody Workspace workspace) {
        Workspace saved = workspaceRepo.save(workspace);
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(saved));
    }

    @GetMapping("/{tenantId}/workspaces")
    public ResponseEntity<ApiResponse<List<Workspace>>> listWorkspaces(@PathVariable UUID tenantId) {
        List<Workspace> workspaces = workspaceRepo.findByTenantId(tenantId);
        return ResponseEntity.ok(ApiResponse.success(workspaces));
    }
}
