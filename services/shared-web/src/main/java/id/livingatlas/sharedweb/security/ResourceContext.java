package id.livingatlas.sharedweb.security;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.util.Map;
import java.util.UUID;

/**
 * Resource context populated by the service layer for ABAC evaluation.
 * <p>
 * Contains the attributes of the resource being accessed, which are
 * evaluated against ABAC policies by the policy engine.
 *
 * @see UserContext
 * @see id.livingatlas.identityservice.abac.domain.AbacPolicyEngine
 */
@Data
@Builder
@AllArgsConstructor
public class ResourceContext {

    private String resourceType;
    private UUID resourceId;
    private UUID tenantId;
    private UUID workspaceId;
    private UUID createdBy;
    private String status;
    private String classification;
    private Map<String, JsonNode> attributes;

    public boolean isGlobalResource() {
        return tenantId == null;
    }

    @SuppressWarnings("unchecked")
    public <T> T getAttribute(String name) {
        if (attributes == null) return null;
        JsonNode node = attributes.get(name);
        if (node == null) return null;
        return (T) node;
    }
}