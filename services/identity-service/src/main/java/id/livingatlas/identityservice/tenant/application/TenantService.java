package id.livingatlas.identityservice.tenant.application;

import id.livingatlas.identityservice.model.Tenant;
import id.livingatlas.identityservice.model.TenantStatus;
import id.livingatlas.identityservice.model.Workspace;
import id.livingatlas.identityservice.tenant.domain.TenantRepository;
import id.livingatlas.identityservice.tenant.domain.WorkspaceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class TenantService {

    private final TenantRepository tenantRepository;
    private final WorkspaceRepository workspaceRepository;

    @Transactional
    public Tenant createTenant(String slug, String name, String tenantType, String description) {
        if (tenantRepository.findBySlug(slug).isPresent()) {
            throw new IllegalArgumentException("Tenant slug already exists: " + slug);
        }

        var type = id.livingatlas.identityservice.model.TenantType.valueOf(tenantType);
        Tenant tenant = new Tenant(slug, name, type);
        tenant.setDescription(description);
        return tenantRepository.save(tenant);
    }

    @Transactional(readOnly = true)
    public Tenant getTenantBySlug(String slug) {
        return tenantRepository.findBySlug(slug)
                .orElseThrow(() -> new IllegalArgumentException("Tenant not found: " + slug));
    }

    @Transactional(readOnly = true)
    public Tenant getTenantById(UUID tenantId) {
        return tenantRepository.findById(tenantId)
                .orElseThrow(() -> new IllegalArgumentException("Tenant not found: " + tenantId));
    }

    @Transactional
    public Tenant updateTenant(UUID tenantId, String name, String description, String subscriptionPlan) {
        Tenant tenant = getTenantById(tenantId);
        if (name != null) tenant.setName(name);
        if (description != null) tenant.setDescription(description);
        if (subscriptionPlan != null) tenant.setSubscriptionPlan(subscriptionPlan);
        return tenantRepository.save(tenant);
    }

    @Transactional
    public void suspendTenant(UUID tenantId) {
        Tenant tenant = getTenantById(tenantId);
        tenant.setStatus(TenantStatus.suspended);
        tenantRepository.save(tenant);
    }

    @Transactional
    public Workspace createWorkspace(UUID tenantId, String slug, String name, String workspaceType) {
        Tenant tenant = getTenantById(tenantId);
        Workspace workspace = new Workspace(tenant, slug, name, workspaceType);
        return workspaceRepository.save(workspace);
    }

    @Transactional(readOnly = true)
    public List<Workspace> getWorkspaces(UUID tenantId) {
        return workspaceRepository.findAllByTenantId(tenantId);
    }

    @Transactional(readOnly = true)
    public Workspace getWorkspace(UUID tenantId, UUID workspaceId) {
        return workspaceRepository.findById(workspaceId)
                .filter(w -> w.getTenant().getId().equals(tenantId))
                .orElseThrow(() -> new IllegalArgumentException("Workspace not found"));
    }

    @Transactional
    public Workspace updateWorkspace(UUID tenantId, UUID workspaceId, String name, String description) {
        Workspace workspace = getWorkspace(tenantId, workspaceId);
        if (name != null) workspace.setName(name);
        if (description != null) workspace.setDescription(description);
        return workspaceRepository.save(workspace);
    }

    @Transactional
    public void deleteWorkspace(UUID tenantId, UUID workspaceId) {
        Workspace workspace = getWorkspace(tenantId, workspaceId);
        workspaceRepository.delete(workspace);
    }
}