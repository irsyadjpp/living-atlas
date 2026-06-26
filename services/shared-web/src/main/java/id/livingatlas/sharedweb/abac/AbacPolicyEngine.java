package id.livingatlas.sharedweb.abac;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import id.livingatlas.sharedweb.abac.model.Policy;
import id.livingatlas.sharedweb.abac.model.PolicyRule;
import id.livingatlas.sharedweb.security.ResourceContext;
import id.livingatlas.sharedweb.security.UserContext;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Central ABAC policy evaluation engine.
 * <p>
 * Evaluates authorization decisions in two layers:
 * <ol>
 *   <li><b>RBAC check</b>: Does the user's role grant the required base permission?</li>
 *   <li><b>ABAC check</b>: Do the resource attributes satisfy the policy conditions?</li>
 * </ol>
 * <p>
 * Both layers must pass for access to be granted. If RBAC denies, ABAC is not evaluated.
 * <p>
 * Per ADR-006: RBAC + ABAC Authorization Model — ABAC Extends RBAC.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AbacPolicyEngine {

    private final PolicyRepository policyRepository;
    private final PolicyRuleRepository policyRuleRepository;
    private final ObjectMapper objectMapper;

    /**
     * Authorize a user action on a resource.
     *
     * @param user     the authenticated user with roles and permissions
     * @param action   the requested action (e.g., "story:write")
     * @param resource the target resource with its attributes (may be null for non-resource actions)
     * @return AuthorizationResult with decision and reason
     */
    public AuthorizationResult authorize(UserContext user, String action, ResourceContext resource) {
        // Step 1: RBAC check — does the user have the base permission?
        Set<String> userPermissions = resolveUserPermissions(user);
        if (!hasBasePermission(userPermissions, action)) {
            log.debug("RBAC DENIED: user {} lacks permission {}", user.getUserId(), action);
            return AuthorizationResult.denied("RBAC_DENIED",
                    "User role does not grant permission: " + action);
        }

        // Step 2: If no resource context (e.g., create new story), RBAC is sufficient
        if (resource == null) {
            return AuthorizationResult.allowed();
        }

        // Step 3: Resolve active ABAC policies matching this action
        List<Policy> policies = policyRepository.findAllByEnabledTrue();

        // Step 4: Evaluate policies in insertion order
        for (Policy policy : policies) {
            List<PolicyRule> rules = policyRuleRepository.findAllByPolicyIdOrderByRuleOrder(policy.getId());

            if (rules.isEmpty()) continue;

            boolean allRulesMatch = rules.stream().allMatch(rule ->
                    evaluateRule(rule, user, resource, action));

            if (allRulesMatch) {
                if ("deny".equalsIgnoreCase(policy.getEffect())) {
                    log.debug("ABAC DENIED by policy {}: {}", policy.getCode(), policy.getDescription());
                    return AuthorizationResult.denied("ABAC_DENIED",
                            "Denied by policy: " + policy.getDescription());
                }
                // ALLOW policy matched — continue evaluating other policies
                log.trace("ABAC ALLOW matched policy: {}", policy.getCode());
            }
        }

        // Default: allow (if no DENY policy matched)
        return AuthorizationResult.allowed();
    }

    private boolean hasBasePermission(Set<String> permissions, String action) {
        if (permissions.contains("*:*")) return true; // Super admin

        // Exact match
        if (permissions.contains(action)) return true;

        // Wildcard match: "story:*" covers "story:write"
        String resourceType = action.split(":")[0];
        if (permissions.contains(resourceType + ":*")) return true;

        return false;
    }

    private boolean evaluateRule(PolicyRule rule, UserContext user, ResourceContext resource, String action) {
        try {
            Map<String, Object> conditions = objectMapper.readValue(
                    rule.getRuleExpression(),
                    new com.fasterxml.jackson.core.type.TypeReference<Map<String, Object>>() {}
            );

            for (Map.Entry<String, Object> condition : conditions.entrySet()) {
                String key = condition.getKey();
                Object expectedValue = condition.getValue();
                Object actualValue = resolveAttribute(key, user, resource, action);

                if (actualValue == null || !matches(actualValue, expectedValue)) {
                    return false;
                }
            }
            return true;
        } catch (Exception e) {
            log.warn("Error evaluating rule {}: {}", rule.getId(), e.getMessage());
            return false;
        }
    }

    private Object resolveAttribute(String key, UserContext user, ResourceContext resource, String action) {
        return switch (key) {
            // User attributes
            case "subject.id" -> user.getUserId().toString();
            case "subject.tenantId" -> user.getTenantId().toString();
            case "subject.roles" -> user.getRoles();
            case "subject.isSystemAdmin" -> user.isSystemAdmin();

            // Resource attributes
            case "resource.type" -> resource.getResourceType();
            case "resource.id" -> resource.getResourceId().toString();
            case "resource.tenantId" -> resource.getTenantId() != null ? resource.getTenantId().toString() : null;
            case "resource.workspaceId" -> resource.getWorkspaceId() != null ? resource.getWorkspaceId().toString() : null;
            case "resource.createdBy" -> resource.getCreatedBy() != null ? resource.getCreatedBy().toString() : null;
            case "resource.status" -> resource.getStatus();
            case "resource.classification" -> resource.getClassification();

            // Action
            case "action" -> action;

            // Fallback to custom attributes
            default -> {
                if (key.startsWith("subject.")) {
                    yield user.getAttributes() != null ? user.getAttributes().get(key.substring(8)) : null;
                } else if (key.startsWith("resource.")) {
                    yield resource.getAttribute(key.substring(9));
                }
                yield null;
            }
        };
    }

    private boolean matches(Object actual, Object expected) {
        if (actual instanceof Collection) {
            return ((Collection<?>) actual).contains(expected.toString());
        }
        if (expected instanceof Collection) {
            return ((Collection<?>) expected).contains(actual.toString());
        }
        return actual.toString().equalsIgnoreCase(expected.toString());
    }

    private Set<String> resolveUserPermissions(UserContext user) {
        // Return cached permissions from UserContext
        // (populated at login/JWT creation time with 5-minute TTL)
        if (user.getPermissions() != null && !user.getPermissions().isEmpty()) {
            return user.getPermissions();
        }
        // System admin gets all permissions
        if (user.isSystemAdmin()) {
            return Set.of("*:*");
        }
        return Collections.emptySet();
    }

    /**
     * Result of an authorization decision.
     */
    @Getter
    @AllArgsConstructor
    public static class AuthorizationResult {
        private final boolean allowed;
        private final String decision;
        private final String reason;

        public static AuthorizationResult allowed() {
            return new AuthorizationResult(true, "ALLOWED", "Access granted");
        }

        public static AuthorizationResult denied(String decision, String reason) {
            return new AuthorizationResult(false, decision, reason);
        }

        public boolean isDenied() {
            return !allowed;
        }
    }
}