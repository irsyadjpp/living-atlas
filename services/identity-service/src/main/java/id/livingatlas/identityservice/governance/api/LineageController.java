package id.livingatlas.identityservice.governance.api;
import id.livingatlas.sharedweb.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/lineage")
@RequiredArgsConstructor
public class LineageController {
    @GetMapping
    public ResponseEntity<ApiResponse<Object>> listLineage() {
        return ResponseEntity.ok(ApiResponse.success(java.util.List.of()));
    }
}
