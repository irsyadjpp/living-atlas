package id.livingatlas.researchservice.annotation.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.researchservice.annotation.application.AnnotationService;
import id.livingatlas.researchservice.annotation.domain.Annotation;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/research/annotations")
@RequiredArgsConstructor
public class AnnotationController {

    private final AnnotationService annotationService;

    @PostMapping
    public ResponseEntity<ApiResponse<Annotation>> createAnnotation(@RequestBody Annotation annotation) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(annotationService.createAnnotation(annotation)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Annotation>> getAnnotation(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(annotationService.getAnnotation(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Annotation>> listAnnotations(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String targetType,
            @RequestParam(required = false) UUID targetId) {
        return ResponseEntity.ok(PagedResponse.from(annotationService.listAnnotations(page, size, targetType, targetId)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteAnnotation(@PathVariable UUID id) {
        annotationService.deleteAnnotation(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}
