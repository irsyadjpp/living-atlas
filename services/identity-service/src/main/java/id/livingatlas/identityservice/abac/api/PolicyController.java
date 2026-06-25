package id.livingatlas.identityservice.abac.api;

import id.livingatlas.identityservice.abac.application.AbacService;
import id.livingatlas.identityservice.abac.domain.model.Policy;
import id.livingatlas.sharedweb.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/policies")
@RequiredArgsConstructor
public class PolicyController {

    private final AbacService abacService;

    @GetMapping
    public ResponseEntity<ApiResponse<List<Policy>>> listPolicies() {
        List<Policy> policies = abacService.getAllPolicies();
        return ResponseEntity.ok(ApiResponse.success(policies));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Policy>> getPolicy(@PathVariable UUID id) {
        Policy policy = abacService.getPolicy(id);
        return ResponseEntity.ok(ApiResponse.success(policy));
    }

    @PostMapping
    public ResponseEntity<ApiResponse<Policy>> createPolicy(@RequestBody CreatePolicyRequest request) {
        Policy policy = abacService.createPolicy(
                request.code(),
                request.name(),
                request.effect(),
                request.description()
        );
        return ResponseEntity.ok(ApiResponse.success(policy));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Policy>> updatePolicy(
            @PathVariable UUID id,
            @RequestBody UpdatePolicyRequest request) {
        Policy policy = abacService.updatePolicy(id, request.name(), request.description());
        return ResponseEntity.ok(ApiResponse.success(policy));
    }

    @PatchMapping("/{id}/toggle")
    public ResponseEntity<ApiResponse<Policy>> togglePolicy(@PathVariable UUID id) {
        Policy policy = abacService.getPolicy(id);
        abacService.togglePolicy(id, !policy.getEnabled());
        return ResponseEntity.ok(ApiResponse.success(policy));
    }

    @PostMapping("/{id}/rules")
    public ResponseEntity<ApiResponse<Policy>> addRule(
            @PathVariable UUID id,
            @RequestBody AddRuleRequest request) {
        abacService.addRuleToPolicy(id, request.ruleOrder(), request.ruleExpression());
        Policy policy = abacService.getPolicy(id);
        return ResponseEntity.ok(ApiResponse.success(policy));
    }

    public record CreatePolicyRequest(String code, String name, String effect, String description) {}
    public record UpdatePolicyRequest(String name, String description) {}
    public record AddRuleRequest(Integer ruleOrder, String ruleExpression) {}
}
