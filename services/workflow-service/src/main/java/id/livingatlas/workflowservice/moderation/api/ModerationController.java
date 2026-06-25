package id.livingatlas.workflowservice.moderation.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.workflowservice.moderation.application.ModerationService;
import id.livingatlas.workflowservice.moderation.domain.Moderation;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/workflow/moderation")
@RequiredArgsConstructor
public class ModerationController {

    private final ModerationService moderationService;

    @PostMapping
    public ResponseEntity<ApiResponse<Moderation>> createModeration(@RequestBody Moderation moderation) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(moderationService.createModeration(moderation)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Moderation>> getModeration(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(moderationService.getModeration(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Moderation>> listModerations(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(PagedResponse.from(moderationService.listModerations(page, size, status)));
    }

    @PostMapping("/{id}/flag")
    public ResponseEntity<ApiResponse<Moderation>> flag(
            @PathVariable UUID id,
            @RequestBody Map<String, String> body) {
        String flagReason = body.getOrDefault("flagReason", "Inappropriate content");
        String notes = body.getOrDefault("notes", "");
        return ResponseEntity.ok(ApiResponse.success(moderationService.flag(id, flagReason, notes)));
    }

    @PostMapping("/{id}/resolve")
    public ResponseEntity<ApiResponse<Moderation>> resolve(
            @PathVariable UUID id,
            @RequestHeader("X-User-Id") UUID moderatorId,
            @RequestBody(required = false) Map<String, String> body) {
        String notes = body != null ? body.getOrDefault("notes", "") : "";
        return ResponseEntity.ok(ApiResponse.success(moderationService.resolve(id, moderatorId, notes)));
    }
}