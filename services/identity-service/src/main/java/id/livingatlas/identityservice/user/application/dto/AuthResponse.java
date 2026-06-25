package id.livingatlas.identityservice.user.application.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthResponse {

    private UUID userId;
    private String email;
    private String username;
    private String displayName;
    private List<String> roles;
    private UUID tenantId;
    private UUID workspaceId;
    private String accessToken;
    private String refreshToken;
    private String tokenType;
}
