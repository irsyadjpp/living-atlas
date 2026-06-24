package id.livingatlas.researchservice.collection.infrastructure;

import id.livingatlas.researchservice.collection.domain.Collection;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface CollectionRepository extends JpaRepository<Collection, UUID> {
    Page<Collection> findByTenantId(UUID tenantId, Pageable pageable);
    Page<Collection> findByWorkspaceId(UUID workspaceId, Pageable pageable);
    Page<Collection> findByOwnerId(UUID ownerId, Pageable pageable);
}