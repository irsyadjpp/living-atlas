package id.livingatlas.identityservice.governance.api;
import id.livingatlas.sharedweb.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/audit")
@RequiredArgsConstructor
public class AuditLogController {
    @GetMapping
    public ResponseEntity<ApiResponse<Object>> listAuditLogs() {
        return ResponseEntity.ok(ApiResponse.success(java.util.List.of()));
    }
}
