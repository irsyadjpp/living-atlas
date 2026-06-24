package id.livingatlas.identityservice.abac.api;
import id.livingatlas.sharedweb.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/policies")
@RequiredArgsConstructor
public class PolicyController {
    @GetMapping
    public ResponseEntity<ApiResponse<Object>> listPolicies() {
        return ResponseEntity.ok(ApiResponse.success(java.util.List.of()));
    }
}
