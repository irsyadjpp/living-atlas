package id.livingatlas.identityservice.preferences.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.preferences.application.UserPreferenceService;
import id.livingatlas.identityservice.preferences.domain.UserPreference;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users/{userId}/preferences")
@RequiredArgsConstructor
public class UserPreferenceController {

    private final UserPreferenceService userPreferenceService;

    @PostMapping
    public ResponseEntity<ApiResponse<UserPreference>> createOrUpdatePreference(
            @PathVariable UUID userId,
            @RequestBody Map<String, String> request) {
        String preferenceKey = request.get("preferenceKey");
        String preferenceValue = request.get("preferenceValue");

        UserPreference preference = new UserPreference();
        preference.setUserId(userId);
        preference.setPreferenceKey(preferenceKey);
        preference.setPreferenceValue(preferenceValue);

        return ResponseEntity.ok(ApiResponse.success(userPreferenceService.createOrUpdatePreference(preference)));
    }

    @GetMapping("/{preferenceKey}")
    public ResponseEntity<ApiResponse<UserPreference>> getPreference(
            @PathVariable UUID userId,
            @PathVariable String preferenceKey) {
        return ResponseEntity.ok(ApiResponse.success(userPreferenceService.getPreference(userId, preferenceKey)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<UserPreference>> listPreferences(
            @PathVariable UUID userId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(userPreferenceService.listPreferences(page, size, userId)));
    }

    @DeleteMapping("/{preferenceKey}")
    public ResponseEntity<ApiResponse<Void>> deletePreference(
            @PathVariable UUID userId,
            @PathVariable String preferenceKey) {
        userPreferenceService.deletePreference(userId, preferenceKey);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}