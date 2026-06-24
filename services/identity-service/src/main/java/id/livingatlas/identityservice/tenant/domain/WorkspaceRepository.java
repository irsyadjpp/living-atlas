package id.livingatlas.identityservice.tenant.domain;

import id.livingatlas.identityservice.model.Workspace;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface WorkspaceRepository extends JpaRepository<Workspace, UUID> {

    Optional<Workspace> findByTenantIdAndSlug(UUID tenantId, String slug);

    List<Workspace> findAllByTenantId(UUID tenantId);
}