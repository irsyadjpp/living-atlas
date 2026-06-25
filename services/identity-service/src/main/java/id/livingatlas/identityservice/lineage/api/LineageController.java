package id.livingatlas.identityservice.lineage.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.identityservice.lineage.application.LineageService;
import id.livingatlas.identityservice.lineage.domain.Lineage;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/lineage")
@RequiredArgsConstructor
public class LineageController {

    private final LineageService lineageService;

    @PostMapping
    public ResponseEntity<ApiResponse<Lineage>> createLineage(@RequestBody Lineage lineage) {
        return ResponseEntity.ok(ApiResponse.success(lineageService.createLineage(lineage)));
    }

    @GetMapping("/object/{objectId}")
    public ResponseEntity<ApiResponse<List<Lineage>>> getLineage(
            @PathVariable UUID objectId,
            @RequestParam String objectType) {
        return ResponseEntity.ok(ApiResponse.success(lineageService.getLineage(objectId, objectType)));
    }

    @GetMapping("/parent/{parentObjectId}")
    public ResponseEntity<ApiResponse<List<Lineage>>> getChildren(@PathVariable UUID parentObjectId) {
        return ResponseEntity.ok(ApiResponse.success(lineageService.getChildren(parentObjectId)));
    }
}