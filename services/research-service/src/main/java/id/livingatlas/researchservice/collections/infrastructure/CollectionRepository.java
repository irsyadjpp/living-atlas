package id.livingatlas.researchservice.collections.infrastructure;

import id.livingatlas.researchservice.collections.domain.Collection;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface CollectionRepository extends JpaRepository<Collection, UUID> {
    List<Collection> findByOwnerId(UUID ownerId);
    List<Collection> findByIsSharedTrue();
    List<Collection> findByTenantId(UUID tenantId);
}