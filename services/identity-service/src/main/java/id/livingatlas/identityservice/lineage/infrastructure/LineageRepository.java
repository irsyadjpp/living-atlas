package id.livingatlas.identityservice.lineage.infrastructure;

import id.livingatlas.identityservice.lineage.domain.Lineage;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface LineageRepository extends JpaRepository<Lineage, UUID> {
    List<Lineage> findByObjectIdAndObjectType(UUID objectId, String objectType);
    List<Lineage> findByParentObjectId(UUID parentObjectId);
    List<Lineage> findByTenantId(UUID tenantId);
}