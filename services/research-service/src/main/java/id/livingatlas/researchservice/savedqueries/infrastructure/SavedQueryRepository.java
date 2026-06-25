package id.livingatlas.researchservice.savedqueries.infrastructure;

import id.livingatlas.researchservice.savedqueries.domain.SavedQuery;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface SavedQueryRepository extends JpaRepository<SavedQuery, UUID> {
    Optional<SavedQuery> findByName(String name);
    java.util.List<SavedQuery> findByTenantId(UUID tenantId);
}