package id.livingatlas.identityservice.audit.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.audit.application.AuditLogService;
import id.livingatlas.identityservice.audit.domain.AuditLog;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/audit")
@RequiredArgsConstructor
public class AuditLogController {

    private final AuditLogService auditLogService;

    @GetMapping
    public ResponseEntity<PagedResponse<AuditLog>> listAuditLogs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID userId,
            @RequestParam(required = false) UUID tenantId,
            @RequestParam(required = false) String resourceType,
            @RequestParam(required = false) UUID resourceId) {
        return ResponseEntity.ok(PagedResponse.from(
            auditLogService.searchAuditLogs(page, size, userId, tenantId, resourceType, resourceId)
        ));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<AuditLog>> getAuditLog(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(auditLogService.getAuditLog(id)));
    }
}