package id.livingatlas.knowledgeservice.folklore.api;

import id.livingatlas.knowledgeservice.folklore.application.FolkloreService;
import id.livingatlas.knowledgeservice.folklore.domain.Folklore;
import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/knowledge/folklore")
@RequiredArgsConstructor
public class FolkloreController {

    private final FolkloreService folkloreService;

    @PostMapping
    public ResponseEntity<ApiResponse<Folklore>> createFolklore(@RequestBody Folklore folklore) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(folkloreService.createFolklore(folklore)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Folklore>> getFolklore(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(folkloreService.getFolklore(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Folklore>> listFolklore(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(folkloreService.listFolklore(page, size)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Folklore>> updateFolklore(@PathVariable UUID id, @RequestBody Folklore folklore) {
        return ResponseEntity.ok(ApiResponse.success(folkloreService.updateFolklore(id, folklore)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteFolklore(@PathVariable UUID id) {
        folkloreService.deleteFolklore(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}