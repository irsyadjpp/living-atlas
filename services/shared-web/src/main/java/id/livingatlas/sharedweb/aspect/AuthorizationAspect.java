package id.livingatlas.sharedweb.aspect;

import id.livingatlas.sharedweb.abac.AbacPolicyEngine;
import id.livingatlas.sharedweb.annotation.AuthorizationRequired;
import id.livingatlas.sharedweb.security.ResourceContext;
import id.livingatlas.sharedweb.security.UserContext;
import id.livingatlas.sharedweb.security.TenantContextHolder;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

/**
 * AOP aspect that enforces {@link AuthorizationRequired} on service methods.
 * <p>
 * Before the method executes, the aspect:
 * <ol>
 *   <li>Resolves the {@link UserContext} from {@link TenantContextHolder}</li>
 *   <li>Extracts the required permission from the annotation</li>
 *   <li>Searches method arguments for a {@link ResourceContext}</li>
 *   <li>Delegates to {@link AbacPolicyEngine#authorize} for evaluation</li>
 *   <li>Throws {@code AccessDeniedException} if authorization fails</li>
 * </ol>
 */
@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class AuthorizationAspect {

    private final AbacPolicyEngine policyEngine;

    @Around("@annotation(authRequired)")
    public Object checkAuthorization(ProceedingJoinPoint joinPoint, AuthorizationRequired authRequired) throws Throwable {
        UserContext user = TenantContextHolder.get().getUser();
        String action = authRequired.value();

        if (user == null) {
            log.warn("No user context found for @AuthorizationRequired on {}", joinPoint.getSignature());
            throw new SecurityException("Authentication required");
        }

        // Find ResourceContext in method arguments if resourceCheck is enabled
        ResourceContext resource = null;
        if (authRequired.resourceCheck()) {
            resource = findResourceContext(joinPoint.getArgs());
        }

        log.debug("Authorization check: user={}, action={}, resource={}",
                user.getUserId(), action, resource != null ? resource.getResourceId() : "none");

        AbacPolicyEngine.AuthorizationResult result = policyEngine.authorize(user, action, resource);

        if (result.isDenied()) {
            log.warn("Authorization denied: user={}, action={}, reason={}",
                    user.getUserId(), action, result.getReason());
            throw new SecurityException(result.getReason());
        }

        return joinPoint.proceed();
    }

    private ResourceContext findResourceContext(Object[] args) {
        if (args == null) return null;
        for (Object arg : args) {
            if (arg instanceof ResourceContext) {
                return (ResourceContext) arg;
            }
        }
        return null;
    }
}