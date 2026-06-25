package id.livingatlas.workflowservice.publishing.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.workflowservice.publishing.application.PublicationService;
import id.livingatlas.workflowservice.publishing.domain.Publication;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/workflow/publications")
@RequiredArgsConstructor
public class PublishingController {

    private final PublicationService publicationService;

    @PostMapping
    public ResponseEntity<ApiResponse<Publication>> createPublication(@RequestBody Publication publication) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(publicationService.createPublication(publication)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Publication>> getPublication(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(publicationService.getPublication(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Publication>> listPublications(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(PagedResponse.from(publicationService.listPublications(page, size, status)));
    }

    @PostMapping("/{id}/publish")
    public ResponseEntity<ApiResponse<Publication>> publish(
            @PathVariable UUID id,
            @RequestHeader("X-User-Id") UUID publishedBy) {
        return ResponseEntity.ok(ApiResponse.success(publicationService.publish(id, publishedBy)));
    }

    @PostMapping("/{id}/unpublish")
    public ResponseEntity<ApiResponse<Publication>> unpublish(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(publicationService.unpublish(id)));
    }
}