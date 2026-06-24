package id.livingatlas.knowledgeservice.claims.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.knowledgeservice.claims.application.ClaimService;
import id.livingatlas.knowledgeservice.claims.domain.Claim;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/knowledge/claims")
@RequiredArgsConstructor
public class ClaimController {

    private final ClaimService claimService;

    @GetMapping
    public ResponseEntity<PagedResponse<Claim>> listClaims(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) UUID entityId) {
        return ResponseEntity.ok(PagedResponse.from(claimService.listClaims(page, size, status, entityId)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Claim>> getClaim(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(claimService.getClaim(id)));
    }

    @PostMapping
    public ResponseEntity<ApiResponse<Claim>> createClaim(@RequestBody Claim claim) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(claimService.createClaim(claim)));
    }
}
