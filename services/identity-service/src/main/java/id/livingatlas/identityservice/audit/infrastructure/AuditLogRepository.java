package id.livingatlas.identityservice.audit.infrastructure;

import id.livingatlas.identityservice.audit.domain.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface AuditLogRepository extends JpaRepository<AuditLog, UUID> {
    List<AuditLog> findByUserId(UUID userId);
    List<AuditLog> findByTenantId(UUID tenantId);
    List<AuditLog> findByResourceTypeAndResourceId(String resourceType, UUID resourceId);
    
    @Query("SELECT a FROM AuditLog a WHERE " +
           "(:userId IS NULL OR a.userId = :userId) AND " +
           "(:tenantId IS NULL OR a.tenantId = :tenantId) AND " +
           "(:resourceType IS NULL OR a.resourceType = :resourceType) AND " +
           "(:resourceId IS NULL OR a.resourceId = :resourceId)")
    List<AuditLog> searchAuditLogs(
            @Param("userId") UUID userId,
            @Param("tenantId") UUID tenantId,
            @Param("resourceType") String resourceType,
            @Param("resourceId") UUID resourceId);
}