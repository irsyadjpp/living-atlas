package id.livingatlas.identityservice.user.api;
import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.user.application.UserService;
import id.livingatlas.identityservice.user.application.dto.UserProfile;
import id.livingatlas.identityservice.user.application.dto.UpdateProfileRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;
    @GetMapping("/me")
    public ResponseEntity<ApiResponse<UserProfile>> getProfile(@RequestHeader("X-User-Id") UUID userId) {
        return ResponseEntity.ok(ApiResponse.success(userService.getProfile(userId)));
    }
    @PatchMapping("/me")
    public ResponseEntity<ApiResponse<UserProfile>> updateProfile(@RequestHeader("X-User-Id") UUID userId, @Valid @RequestBody UpdateProfileRequest request) {
        return ResponseEntity.ok(ApiResponse.success(userService.getProfile(userService.updateProfile(userId, request).getId())));
    }
    @GetMapping
    public ResponseEntity<PagedResponse<UserProfile>> listUsers(@RequestParam(defaultValue="0") int page, @RequestParam(defaultValue="20") int size) {
        return ResponseEntity.ok(PagedResponse.from(userService.listUsers(page, size)));
    }
}
