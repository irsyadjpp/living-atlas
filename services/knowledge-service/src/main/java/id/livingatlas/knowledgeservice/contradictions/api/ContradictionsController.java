package id.livingatlas.knowledgeservice.contradictions.api;

import id.livingatlas.knowledgeservice.contradictions.application.ContradictionService;
import id.livingatlas.knowledgeservice.contradictions.domain.Contradiction;
import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/knowledge/contradictions")
@RequiredArgsConstructor
public class ContradictionsController {

    private final ContradictionService contradictionService;

    @PostMapping
    public ResponseEntity<ApiResponse<Contradiction>> createContradiction(@RequestBody Contradiction contradiction) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(contradictionService.createContradiction(contradiction)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Contradiction>> getContradiction(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(contradictionService.getContradiction(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Contradiction>> listContradictions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(contradictionService.listContradictions(page, size)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Contradiction>> updateContradiction(@PathVariable UUID id, @RequestBody Contradiction contradiction) {
        return ResponseEntity.ok(ApiResponse.success(contradictionService.updateContradiction(id, contradiction)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteContradiction(@PathVariable UUID id) {
        contradictionService.deleteContradiction(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}