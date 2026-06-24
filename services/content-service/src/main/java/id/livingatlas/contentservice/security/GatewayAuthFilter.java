package id.livingatlas.contentservice.security;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Trusts authentication headers from the API Gateway.
 * Gateway validates JWT and forwards X-User-Id, X-User-Roles, X-Tenant-Id headers.
 */
@Configuration
@Slf4j
public class GatewayAuthFilter extends OncePerRequestFilter {

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.startsWith("/api-docs") || 
               path.startsWith("/v3/api-docs") || 
               path.startsWith("/swagger-ui") || 
               path.startsWith("/swagger-resources") ||
               path.equals("/swagger-ui.html") ||
               path.startsWith("/actuator/health");
    }

    @Override
    protected void doFilterInternal(
            jakarta.servlet.http.HttpServletRequest request,
            jakarta.servlet.http.HttpServletResponse response,
            jakarta.servlet.FilterChain chain) throws IOException, ServletException {

        String authenticated = request.getHeader("X-Authenticated");

        if ("true".equals(authenticated)) {
            String userId = request.getHeader("X-User-Id");
            String roles = request.getHeader("X-User-Roles");
            String tenantId = request.getHeader("X-Tenant-Id");

            // Parse roles from comma-separated string
            List<SimpleGrantedAuthority> authorities = List.of();
            if (roles != null && !roles.isEmpty()) {
                authorities = Arrays.stream(roles.split(","))
                    .map(String::trim)
                    .filter(r -> !r.isEmpty())
                    .map(r -> new SimpleGrantedAuthority("ROLE_" + r.toUpperCase()))
                    .collect(Collectors.toList());
            }

            // Create authentication token
            UsernamePasswordAuthenticationToken auth = 
                new UsernamePasswordAuthenticationToken(userId, null, authorities);
            
            // Store additional details
            auth.setDetails(java.util.Map.of(
                "userId", userId,
                "tenantId", tenantId != null ? tenantId : "",
                "authenticated", true
            ));

            SecurityContextHolder.getContext().setAuthentication(auth);
            log.debug("Gateway auth set: userId={}, roles={}", userId, roles);
        }

        chain.doFilter(request, response);
    }
}