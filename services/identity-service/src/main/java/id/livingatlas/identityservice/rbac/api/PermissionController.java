package id.livingatlas.identityservice.rbac.api;
import id.livingatlas.sharedweb.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/permissions")
@RequiredArgsConstructor
public class PermissionController {
    @GetMapping
    public ResponseEntity<ApiResponse<Object>> listPermissions() {
        return ResponseEntity.ok(ApiResponse.success(java.util.List.of()));
    }
}
