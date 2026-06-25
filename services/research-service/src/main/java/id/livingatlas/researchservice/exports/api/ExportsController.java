package id.livingatlas.researchservice.exports.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.researchservice.exports.application.ExportService;
import id.livingatlas.researchservice.exports.domain.Export;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/research/exports")
@RequiredArgsConstructor
public class ExportsController {

    private final ExportService exportService;

    @PostMapping
    public ResponseEntity<ApiResponse<Export>> createExport(@RequestBody Export export) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(exportService.createExport(export)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Export>> getExport(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(exportService.getExport(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Export>> listExports(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID tenantId) {
        return ResponseEntity.ok(PagedResponse.from(exportService.listExports(page, size, tenantId)));
    }
}