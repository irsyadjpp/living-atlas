package id.livingatlas.identityservice.apikeys.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.apikeys.application.ApiKeyService;
import id.livingatlas.identityservice.apikeys.domain.ApiKey;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users/{userId}/api-keys")
@RequiredArgsConstructor
public class ApiKeyController {

    private final ApiKeyService apiKeyService;

    @PostMapping
    public ResponseEntity<ApiResponse<ApiKey>> createApiKey(
            @PathVariable UUID userId,
            @RequestBody ApiKey apiKey) {
        apiKey.setUserId(userId);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(apiKeyService.createApiKey(apiKey)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<ApiKey>> getApiKey(@PathVariable UUID userId, @PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(apiKeyService.getApiKey(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<ApiKey>> listApiKeys(
            @PathVariable UUID userId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(apiKeyService.listApiKeys(page, size, userId)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteApiKey(@PathVariable UUID userId, @PathVariable UUID id) {
        apiKeyService.deleteApiKey(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}