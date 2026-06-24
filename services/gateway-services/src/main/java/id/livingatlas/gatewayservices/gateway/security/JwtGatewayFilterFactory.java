package id.livingatlas.gatewayservices.gateway.security;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
@RequiredArgsConstructor
public class JwtGatewayFilterFactory extends AbstractGatewayFilterFactory<Object> {

    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(JwtGatewayFilterFactory.class);

    private final JwtTokenProvider jwtTokenProvider;

    private static final List<String> PUBLIC_PATHS = List.of(
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/health",
        "/docs",
        "/scalar",
        "/api-docs"
    );

    @Override
    public GatewayFilter apply(Object config) {
        return (exchange, chain) -> {
            String path = exchange.getRequest().getURI().getPath();

            // Skip JWT validation for public paths
            if (isPublicPath(path)) {
                return chain.filter(exchange);
            }

            // Extract JWT from Authorization header
            String authHeader = exchange.getRequest().getHeaders()
                .getFirst(HttpHeaders.AUTHORIZATION);

            if (authHeader == null || !authHeader.startsWith("Bearer ")) {
                log.warn("Missing or invalid Authorization header for path: {}", path);
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                return exchange.getResponse().setComplete();
            }

            String token = authHeader.substring(7);

            // Validate JWT
            if (!jwtTokenProvider.validateToken(token)) {
                log.warn("Invalid or expired JWT token for path: {}", path);
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                return exchange.getResponse().setComplete();
            }

            // Extract claims and forward as headers to downstream services
            try {
                String userId = jwtTokenProvider.getUserIdFromToken(token).toString();
                List<String> roles = jwtTokenProvider.getRolesFromToken(token);
                String tenantId = jwtTokenProvider.getTenantIdFromToken(token);

                ServerHttpRequest modifiedRequest = exchange.getRequest().mutate()
                    .header("X-User-Id", userId)
                    .header("X-User-Roles", String.join(",", roles))
                    .header("X-Tenant-Id", tenantId != null ? tenantId : "")
                    .header("X-Authenticated", "true")
                    .build();

                log.debug("JWT validated: userId={}, roles={}, path={}", userId, roles, path);

                return chain.filter(exchange.mutate().request(modifiedRequest).build());

            } catch (Exception e) {
                log.error("Error processing JWT claims: {}", e.getMessage());
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                return exchange.getResponse().setComplete();
            }
        };
    }

    private boolean isPublicPath(String path) {
        return PUBLIC_PATHS.stream().anyMatch(path::startsWith);
    }
}