package id.livingatlas.researchservice.collection.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.researchservice.collection.application.CollectionService;
import id.livingatlas.researchservice.collection.domain.Collection;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/research/collections")
@RequiredArgsConstructor
public class CollectionController {

    private final CollectionService collectionService;

    @PostMapping
    public ResponseEntity<ApiResponse<Collection>> createCollection(@RequestBody Collection collection) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(collectionService.createCollection(collection)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Collection>> getCollection(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(collectionService.getCollection(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Collection>> listCollections(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID tenantId) {
        return ResponseEntity.ok(PagedResponse.from(collectionService.listCollections(page, size, tenantId)));
    }

    @PostMapping("/{collectionId}/items")
    public ResponseEntity<ApiResponse<Void>> addItem(@PathVariable UUID collectionId, @RequestBody Object request) {
        collectionService.addItem(collectionId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.noContent());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteCollection(@PathVariable UUID id) {
        collectionService.deleteCollection(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}
