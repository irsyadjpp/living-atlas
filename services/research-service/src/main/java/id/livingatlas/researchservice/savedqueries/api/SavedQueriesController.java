package id.livingatlas.researchservice.savedqueries.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.researchservice.savedqueries.application.SavedQueryService;
import id.livingatlas.researchservice.savedqueries.domain.SavedQuery;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/research/saved-queries")
@RequiredArgsConstructor
public class SavedQueriesController {

    private final SavedQueryService savedQueryService;

    @PostMapping
    public ResponseEntity<ApiResponse<SavedQuery>> createSavedQuery(@RequestBody SavedQuery savedQuery) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(savedQueryService.createSavedQuery(savedQuery)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<SavedQuery>> getSavedQuery(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(savedQueryService.getSavedQuery(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<SavedQuery>> listSavedQueries(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID tenantId) {
        return ResponseEntity.ok(PagedResponse.from(savedQueryService.listSavedQueries(page, size, tenantId)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<SavedQuery>> updateSavedQuery(@PathVariable UUID id, @RequestBody SavedQuery savedQuery) {
        return ResponseEntity.ok(ApiResponse.success(savedQueryService.updateSavedQuery(id, savedQuery)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteSavedQuery(@PathVariable UUID id) {
        savedQueryService.deleteSavedQuery(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}