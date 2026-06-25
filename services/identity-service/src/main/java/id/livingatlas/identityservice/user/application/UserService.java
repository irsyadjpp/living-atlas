package id.livingatlas.identityservice.user.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.identityservice.rbac.domain.model.Role;
import id.livingatlas.identityservice.tenant.domain.model.Tenant;
import id.livingatlas.identityservice.tenant.domain.model.TenantType;
import id.livingatlas.identityservice.user.domain.model.User;
import id.livingatlas.identityservice.user.domain.model.UserRole;
import id.livingatlas.identityservice.user.domain.model.UserStatus;
import id.livingatlas.identityservice.tenant.domain.model.Workspace;
import id.livingatlas.identityservice.rbac.domain.RoleRepository;
import id.livingatlas.identityservice.rbac.domain.UserRoleRepository;
import id.livingatlas.identityservice.tenant.domain.TenantRepository;
import id.livingatlas.identityservice.tenant.domain.WorkspaceRepository;
import id.livingatlas.identityservice.user.domain.UserDomainEvent;
import id.livingatlas.identityservice.user.domain.UserRepository;
import id.livingatlas.identityservice.user.application.dto.*;
import id.livingatlas.identityservice.shared.event.DomainEventPublisher;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final UserRoleRepository userRoleRepository;
    private final TenantRepository tenantRepository;
    private final WorkspaceRepository workspaceRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final DomainEventPublisher eventPublisher;

    @Transactional
    public User register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw ApiException.badRequest("Registration failed");
        }
        if (userRepository.existsByUsername(request.getUsername())) {
            throw ApiException.badRequest("Registration failed");
        }

        User user = new User(request.getEmail(), request.getUsername());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user = userRepository.save(user);

        // Assign default researcher role (per ABAC design)
        Role defaultRole = roleRepository.findByCode("researcher")
                .orElseThrow(() -> new IllegalStateException("Default role 'researcher' not found"));

        // Create a default personal tenant for the user
        Tenant defaultTenant = new Tenant(
            user.getUsername().toLowerCase(),
            user.getUsername() + "'s Personal Space",
            TenantType.individual
        );
        defaultTenant = tenantRepository.save(defaultTenant);

        // Create a default personal workspace for the user
        Workspace defaultWorkspace = new Workspace(
            defaultTenant,
            user.getUsername().toLowerCase() + "-workspace",
            user.getUsername() + "'s Workspace",
            "personal"
        );
        defaultWorkspace = workspaceRepository.save(defaultWorkspace);

        UserRole userRole = new UserRole(user, defaultRole, defaultTenant, defaultWorkspace);
        userRoleRepository.save(userRole);

        // Publish domain event
        eventPublisher.publish(new id.livingatlas.identityservice.shared.event.DomainEvent(
            "UserRegistered") {
        });

        log.info("User registered: userId={}, email={}", user.getId(), user.getEmail());
        return user;
    }

    @Transactional(readOnly = true)
    public AuthResponse authenticate(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getEmailOrUsername(), request.getPassword())
        );

        User user = userRepository.findByEmail(request.getEmailOrUsername())
                .orElseGet(() -> userRepository.findByUsername(request.getEmailOrUsername())
                        .orElseThrow(() -> ApiException.unauthorized("Invalid credentials")));

        user.setLastLoginAt(java.time.OffsetDateTime.now());
        userRepository.save(user);

        List<UserRole> userRoles = userRoleRepository.findAllByUserId(user.getId());
        List<String> roleCodes = userRoles.stream()
                .map(ur -> ur.getRole().getCode())
                .collect(Collectors.toList());

        // Publish login audit event
        eventPublisher.publish(new id.livingatlas.identityservice.shared.event.DomainEvent(
            "UserLoggedIn") {
        });

        return AuthResponse.builder()
                .userId(user.getId())
                .email(user.getEmail())
                .username(user.getUsername())
                .displayName(user.getDisplayName())
                .roles(roleCodes)
                .build();
    }

    @Transactional(readOnly = true)
    public UserProfile getProfile(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> ApiException.notFound("User not found"));

        List<UserRole> userRoles = userRoleRepository.findAllByUserId(userId);
        List<String> roleCodes = userRoles.stream()
                .map(ur -> ur.getRole().getCode())
                .collect(Collectors.toList());

        return UserProfile.builder()
                .id(user.getId())
                .email(user.getEmail())
                .username(user.getUsername())
                .displayName(user.getDisplayName())
                .avatarUrl(user.getAvatarUrl())
                .status(user.getStatus())
                .emailVerified(user.getEmailVerified())
                .roles(roleCodes)
                .createdAt(user.getCreatedAt())
                .build();
    }

    @Transactional(readOnly = true)
    public Page<UserProfile> listUsers(int page, int size) {
        return userRepository.findAll(PageRequest.of(page, size))
                .map(user -> {
                    List<UserRole> userRoles = userRoleRepository.findAllByUserId(user.getId());
                    List<String> roleCodes = userRoles.stream()
                            .map(ur -> ur.getRole().getCode())
                            .collect(Collectors.toList());
                    return UserProfile.builder()
                            .id(user.getId())
                            .email(user.getEmail())
                            .username(user.getUsername())
                            .displayName(user.getDisplayName())
                            .avatarUrl(user.getAvatarUrl())
                            .status(user.getStatus())
                            .emailVerified(user.getEmailVerified())
                            .roles(roleCodes)
                            .createdAt(user.getCreatedAt())
                            .build();
                });
    }

    @Transactional
    public User updateProfile(UUID userId, UpdateProfileRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> ApiException.notFound("User not found"));

        if (request.getDisplayName() != null) {
            user.setDisplayName(request.getDisplayName());
        }
        if (request.getAvatarUrl() != null) {
            user.setAvatarUrl(request.getAvatarUrl());
        }

        return userRepository.save(user);
    }

    @Transactional
    public void changePassword(UUID userId, ChangePasswordRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> ApiException.notFound("User not found"));

        if (!passwordEncoder.matches(request.getOldPassword(), user.getPasswordHash())) {
            throw ApiException.badRequest("Current password is incorrect");
        }

        user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);
    }

    @Transactional
    public void blockUser(UUID userId, UUID adminId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> ApiException.notFound("User not found"));
        user.setStatus(UserStatus.blocked);
        user.setUpdatedBy(adminId);
        userRepository.save(user);

        eventPublisher.publish(new id.livingatlas.identityservice.shared.event.DomainEvent(
            "UserSuspended") {
        });
        log.info("User blocked: userId={}, adminId={}", userId, adminId);
    }

    @Transactional
    public void deleteUser(UUID userId, UUID adminId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> ApiException.notFound("User not found"));
        user.setUpdatedBy(adminId);
        user.setDeletedBy(adminId);
        user.setDeletedAt(java.time.OffsetDateTime.now());
        user.setIsDeleted(true);
        userRepository.save(user);

        eventPublisher.publish(new id.livingatlas.identityservice.shared.event.DomainEvent(
            "UserDeleted") {
        });
        log.info("User soft-deleted: userId={}, adminId={}", userId, adminId);
    }
}
