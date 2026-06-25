package id.livingatlas.identityservice.user.application.dto;

import id.livingatlas.identityservice.user.domain.model.UserStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserProfile {

    private UUID id;
    private String email;
    private String username;
    private String displayName;
    private String avatarUrl;
    private UserStatus status;
    private Boolean emailVerified;
    private List<String> roles;
    private OffsetDateTime createdAt;
}