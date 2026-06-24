package id.livingatlas.knowledgeservice.knowledge.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.sharedweb.exception.ApiException;
import id.livingatlas.knowledgeservice.knowledge.application.KnowledgeObjectService;
import id.livingatlas.knowledgeservice.knowledge.domain.KnowledgeObject;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final KnowledgeObjectService knowledgeService;

    @GetMapping("/objects")
    public ResponseEntity<PagedResponse<KnowledgeObject>> listObjects(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String type,
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(PagedResponse.from(knowledgeService.listKnowledgeObjects(page, size, type, status)));
    }

    @GetMapping("/objects/{id}")
    public ResponseEntity<ApiResponse<KnowledgeObject>> getObject(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(knowledgeService.getObject(id)));
    }

    @PostMapping("/objects")
    public ResponseEntity<ApiResponse<KnowledgeObject>> createObject(@RequestBody KnowledgeObject obj) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(knowledgeService.createObject(obj)));
    }

    @GetMapping("/themes")
    public ResponseEntity<PagedResponse<Object>> listThemes(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(knowledgeService.listThemes(page, size)));
    }

    @GetMapping("/search")
    public ResponseEntity<PagedResponse<Object>> search(
            @RequestParam String q,
            @RequestParam(defaultValue = "all") String type,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(knowledgeService.search(q, type, page, size)));
    }
}
