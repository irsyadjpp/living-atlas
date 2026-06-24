package id.livingatlas.identityservice.tenant.api;
import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.model.Tenant;
import id.livingatlas.identityservice.model.Workspace;
import id.livingatlas.identityservice.tenant.domain.TenantRepository;
import id.livingatlas.identityservice.tenant.domain.WorkspaceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
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
    @PostMapping("/{tenantId}/workspaces")
    public ResponseEntity<ApiResponse<Workspace>> createWorkspace(@PathVariable UUID tenantId, @RequestBody Workspace workspace) {
        // Tenant is set via constructor or manually
        Workspace saved = workspaceRepo.save(workspace);
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(saved));
    }
}
