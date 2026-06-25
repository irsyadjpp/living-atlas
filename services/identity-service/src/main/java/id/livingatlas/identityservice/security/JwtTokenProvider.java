package id.livingatlas.identityservice.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Component
public class JwtTokenProvider {

    private final SecretKey secretKey;
    private final long expiration;
    private final long refreshExpiration;

    public JwtTokenProvider(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.expiration}") long expiration,
            @Value("${jwt.refresh-expiration}") long refreshExpiration) {
        this.secretKey = Keys.hmacShaKeyFor(Decoders.BASE64.decode(secret));
        this.expiration = expiration;
        this.refreshExpiration = refreshExpiration;
    }

    /**
     * Generate minimal JWT access token (OWASP ASVS 3.2, UU PDP minimization).
     * Only stores userId - personal data (email, name) looked up from DB when needed.
     */
    public String generateAccessToken(UUID userId, List<String> roles, UUID tenantId, UUID workspaceId) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expiration);

        return Jwts.builder()
                .subject(userId.toString())
                .claim("roles", roles)
                .claim("tenant_id", tenantId != null ? tenantId.toString() : null)
                .claim("workspace_id", workspaceId != null ? workspaceId.toString() : null)
                .issuedAt(now)
                .expiration(expiryDate)
                .signWith(secretKey)
                .compact();
    }

    public String generateRefreshToken(UUID userId) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + refreshExpiration);

        return Jwts.builder()
                .subject(userId.toString())
                .claim("type", "refresh")
                .issuedAt(now)
                .expiration(expiryDate)
                .signWith(secretKey)
                .compact();
    }

    public UUID getUserIdFromToken(String token) {
        Claims claims = parseToken(token);
        return UUID.fromString(claims.getSubject());
    }

    @SuppressWarnings("unchecked")
    public List<String> getRolesFromToken(String token) {
        Claims claims = parseToken(token);
        return claims.get("roles", List.class);
    }

    public UUID getTenantIdFromToken(String token) {
        Claims claims = parseToken(token);
        String tenantId = claims.get("tenant_id", String.class);
        return tenantId != null ? UUID.fromString(tenantId) : null;
    }

    public UUID getWorkspaceIdFromToken(String token) {
        Claims claims = parseToken(token);
        String workspaceId = claims.get("workspace_id", String.class);
        return workspaceId != null ? UUID.fromString(workspaceId) : null;
    }

    public long getRefreshExpiration() {
        return refreshExpiration;
    }

    public boolean validateToken(String token) {
        try {
            parseToken(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    private Claims parseToken(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}