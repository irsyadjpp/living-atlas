package id.livingatlas.researchservice.exports.infrastructure;

import id.livingatlas.researchservice.exports.domain.Export;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ExportRepository extends JpaRepository<Export, UUID> {
    Optional<Export> findByTenantIdAndStatus(UUID tenantId, String status);
    java.util.List<Export> findByTenantId(UUID tenantId);
}