package id.livingatlas.identityservice.user.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.exception.ApiException;
import id.livingatlas.identityservice.security.JwtTokenProvider;
import id.livingatlas.identityservice.security.TokenBlacklistService;
import id.livingatlas.identityservice.user.application.UserService;
import id.livingatlas.identityservice.user.application.dto.AuthResponse;
import id.livingatlas.identityservice.user.application.dto.LoginRequest;
import id.livingatlas.identityservice.user.application.dto.RegisterRequest;
import io.github.bucket4j.Bucket;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {
    private final UserService userService;
    private final JwtTokenProvider jwtTokenProvider;
    private final TokenBlacklistService tokenBlacklistService;
    private final Bucket loginBucket;
    private final Bucket registerBucket;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<AuthResponse>> register(@Valid @RequestBody RegisterRequest request) {
        if (!registerBucket.tryConsume(1)) throw ApiException.rateLimited("Too many registration attempts");
        var user = userService.register(request);
        var userRoles = List.of("viewer");
        String accessToken = jwtTokenProvider.generateAccessToken(user.getId(), userRoles, null);
        String refreshToken = jwtTokenProvider.generateRefreshToken(user.getId());
        var response = AuthResponse.builder().userId(user.getId()).email(user.getEmail()).username(user.getUsername()).roles(userRoles).accessToken(accessToken).refreshToken(refreshToken).tokenType("Bearer").build();
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(response));
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponse>> login(@Valid @RequestBody LoginRequest request) {
        if (!loginBucket.tryConsume(1)) throw ApiException.rateLimited("Too many login attempts");
        var auth = userService.authenticate(request);
        List<String> roles = auth.getRoles();
        String accessToken = jwtTokenProvider.generateAccessToken(auth.getUserId(), roles, null);
        String refreshToken = jwtTokenProvider.generateRefreshToken(auth.getUserId());
        var response = AuthResponse.builder().userId(auth.getUserId()).email(auth.getEmail()).username(auth.getUsername()).displayName(auth.getDisplayName()).roles(roles).accessToken(accessToken).refreshToken(refreshToken).tokenType("Bearer").build();
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<AuthResponse>> refreshToken(@RequestBody Map<String, String> body) {
        String token = body.get("refreshToken");
        if (token == null || tokenBlacklistService.isBlacklisted(token)) throw ApiException.unauthorized("Invalid refresh token");
        if (!jwtTokenProvider.validateToken(token)) throw ApiException.unauthorized("Invalid refresh token");
        UUID userId = jwtTokenProvider.getUserIdFromToken(token);
        List<String> roles = jwtTokenProvider.getRolesFromToken(token);
        tokenBlacklistService.blacklist(token, jwtTokenProvider.getRefreshExpiration());
        String newAccessToken = jwtTokenProvider.generateAccessToken(userId, roles, null);
        String newRefreshToken = jwtTokenProvider.generateRefreshToken(userId);
        var profile = userService.getProfile(userId);
        var response = AuthResponse.builder().userId(userId).email(profile.getEmail()).username(profile.getUsername()).roles(roles).accessToken(newAccessToken).refreshToken(newRefreshToken).tokenType("Bearer").build();
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Void>> logout(@RequestHeader("Authorization") String authHeader) {
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            tokenBlacklistService.blacklist(authHeader.substring(7), jwtTokenProvider.getRefreshExpiration());
        }
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}
