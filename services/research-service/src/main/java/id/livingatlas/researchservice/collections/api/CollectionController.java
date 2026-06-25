package id.livingatlas.researchservice.collections.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.researchservice.collections.application.CollectionService;
import id.livingatlas.researchservice.collections.domain.Collection;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/collections")
@RequiredArgsConstructor
public class CollectionController {

    private final CollectionService collectionService;

    @PostMapping
    public ResponseEntity<ApiResponse<Collection>> createCollection(@RequestBody Collection collection) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(collectionService.createCollection(collection)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Collection>> getCollection(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(collectionService.getCollection(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Collection>> listCollections(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID ownerId) {
        return ResponseEntity.ok(PagedResponse.from(collectionService.listCollections(page, size, ownerId)));
    }

    @GetMapping("/shared")
    public ResponseEntity<ApiResponse<List<Collection>>> getSharedCollections() {
        return ResponseEntity.ok(ApiResponse.success(collectionService.getSharedCollections()));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Collection>> updateCollection(
            @PathVariable UUID id,
            @RequestBody Map<String, String> request) {
        return ResponseEntity.ok(ApiResponse.success(
            collectionService.updateCollection(id, request.get("name"), request.get("description"))));
    }

    @PostMapping("/{id}/share")
    public ResponseEntity<ApiResponse<Void>> shareCollection(
            @PathVariable UUID id,
            @RequestBody Map<String, Boolean> request) {
        collectionService.shareCollection(id, request.getOrDefault("share", true));
        return ResponseEntity.ok(ApiResponse.noContent());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteCollection(@PathVariable UUID id) {
        collectionService.deleteCollection(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}