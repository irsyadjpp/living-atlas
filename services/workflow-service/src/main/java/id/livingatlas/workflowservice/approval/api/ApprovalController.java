package id.livingatlas.workflowservice.approval.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.workflowservice.approval.application.ApprovalService;
import id.livingatlas.workflowservice.approval.domain.Approval;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/workflow/approvals")
@RequiredArgsConstructor
public class ApprovalController {

    private final ApprovalService approvalService;

    @PostMapping
    public ResponseEntity<ApiResponse<Approval>> createApproval(@RequestBody Approval approval) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(approvalService.createApproval(approval)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Approval>> getApproval(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(approvalService.getApproval(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Approval>> listApprovals(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(PagedResponse.from(approvalService.listApprovals(page, size, status)));
    }

    @PostMapping("/{id}/approve")
    public ResponseEntity<ApiResponse<Approval>> approve(
            @PathVariable UUID id,
            @RequestHeader("X-User-Id") UUID approverId,
            @RequestBody(required = false) Map<String, String> body) {
        String notes = body != null ? body.getOrDefault("notes", "") : "";
        return ResponseEntity.ok(ApiResponse.success(approvalService.approve(id, approverId, notes)));
    }

    @PostMapping("/{id}/reject")
    public ResponseEntity<ApiResponse<Approval>> reject(
            @PathVariable UUID id,
            @RequestHeader("X-User-Id") UUID approverId,
            @RequestBody(required = false) Map<String, String> body) {
        String notes = body != null ? body.getOrDefault("notes", "") : "";
        return ResponseEntity.ok(ApiResponse.success(approvalService.reject(id, approverId, notes)));
    }
}