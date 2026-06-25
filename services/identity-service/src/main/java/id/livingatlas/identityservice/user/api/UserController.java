package id.livingatlas.identityservice.user.api;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.identityservice.rbac.domain.model.Role;
import id.livingatlas.identityservice.rbac.domain.RoleRepository;
import id.livingatlas.identityservice.user.application.UserService;
import id.livingatlas.identityservice.user.application.dto.UserProfile;
import id.livingatlas.identityservice.user.application.dto.UpdateProfileRequest;
import id.livingatlas.identityservice.user.domain.model.User;
import id.livingatlas.identityservice.user.domain.UserRepository;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;
    private final UserRepository userRepository;
    private final RoleRepository roleRepository;

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

    @PostMapping
    public ResponseEntity<ApiResponse<User>> createUser(@RequestBody Map<String, Object> request) {
        String email = (String) request.get("email");
        String username = (String) request.get("username");
        String password = (String) request.get("password");
        String displayName = (String) request.get("displayName");

        User user = new User(email, username);
        user.setDisplayName(displayName);
        user.setPasswordHash(password); // In real implementation, encode password
        userRepository.save(user);

        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(user));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteUser(@PathVariable UUID id, @RequestHeader("X-User-Id") UUID adminId) {
        userService.deleteUser(id, adminId);
        return ResponseEntity.ok(ApiResponse.noContent());
    }

    @PatchMapping("/{id}/block")
    public ResponseEntity<ApiResponse<Void>> blockUser(@PathVariable UUID id, @RequestHeader("X-User-Id") UUID adminId) {
        userService.blockUser(id, adminId);
        return ResponseEntity.ok(ApiResponse.noContent());
    }

    @PostMapping("/{id}/roles")
    public ResponseEntity<ApiResponse<Void>> assignRole(@PathVariable UUID id, @RequestBody Map<String, String> request) {
        String roleCode = request.get("roleCode");
        Role role = roleRepository.findByCode(roleCode)
                .orElseThrow(() -> ApiException.notFound("Role not found: " + roleCode));

        User user = userRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("User not found"));

        // Create UserRole association (simplified - in real implementation, use UserRoleRepository)
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}
