package id.livingatlas.identityservice.governance.domain;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.UUID;

@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, UUID> {

    Page<AuditLog> findAllByActorId(UUID actorId, Pageable pageable);

    Page<AuditLog> findAllByResourceTypeAndResourceId(String resourceType, UUID resourceId, Pageable pageable);

    Page<AuditLog> findAllByCreatedAtBetween(OffsetDateTime from, OffsetDateTime to, Pageable pageable);
}