package id.livingatlas.sharedweb.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Declarative authorization annotation for service methods.
 * <p>
 * Usage:
 * <pre>{@code
 * @AuthorizationRequired("story:write")
 * public Story updateStory(UUID storyId, StoryUpdate update) { ... }
 * }</pre>
 * <p>
 * The annotation triggers ABAC policy evaluation via {@code AuthorizationAspect}.
 * If the user lacks the required permission or fails ABAC attribute checks,
 * an {@code AccessDeniedException} is thrown.
 *
 * @see id.livingatlas.sharedweb.aspect.AuthorizationAspect
 * @see id.livingatlas.identityservice.abac.domain.AbacPolicyEngine
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface AuthorizationRequired {

    /**
     * The required permission string (e.g., "story:write", "knowledge:read").
     */
    String value();

    /**
     * Whether to perform ABAC resource-level attribute checks.
     * Set to false for non-resource-specific actions (e.g., "create new story").
     */
    boolean resourceCheck() default true;
}