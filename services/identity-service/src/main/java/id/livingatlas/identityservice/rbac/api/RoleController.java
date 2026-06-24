package id.livingatlas.identityservice.rbac.api;
import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.model.Role;
import id.livingatlas.identityservice.rbac.domain.RoleRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/roles")
@RequiredArgsConstructor
public class RoleController {
    private final RoleRepository roleRepo;
    @GetMapping
    public ResponseEntity<ApiResponse<Object>> listRoles() {
        return ResponseEntity.ok(ApiResponse.success(roleRepo.findAll()));
    }
}
