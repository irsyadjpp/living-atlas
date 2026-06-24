package id.livingatlas.identityservice.governance.application;

import id.livingatlas.identityservice.governance.domain.AuditLog;
import id.livingatlas.identityservice.governance.domain.AuditLogRepository;
import id.livingatlas.identityservice.governance.domain.Lineage;
import id.livingatlas.identityservice.governance.domain.LineageRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class GovernanceService {

    private final AuditLogRepository auditLogRepository;
    private final LineageRepository lineageRepository;

    @Transactional
    public void recordAuditLog(UUID actorId, UUID tenantId, String action,
                                String resourceType, UUID resourceId,
                                String oldValue, String newValue,
                                String ipAddress, String userAgent) {
        AuditLog log = new AuditLog(actorId, tenantId, action, resourceType, resourceId);
        log.setOldValue(oldValue);
        log.setNewValue(newValue);
        log.setIpAddress(ipAddress);
        log.setUserAgent(userAgent);
        auditLogRepository.save(log);
    }

    @Transactional(readOnly = true)
    public Page<AuditLog> queryAuditLogs(UUID actorId, String resourceType,
                                          UUID resourceId,
                                          OffsetDateTime from, OffsetDateTime to,
                                          Pageable pageable) {
        if (actorId != null) {
            return auditLogRepository.findAllByActorId(actorId, pageable);
        }
        if (resourceType != null && resourceId != null) {
            return auditLogRepository.findAllByResourceTypeAndResourceId(resourceType, resourceId, pageable);
        }
        if (from != null && to != null) {
            return auditLogRepository.findAllByCreatedAtBetween(from, to, pageable);
        }
        return auditLogRepository.findAll(pageable);
    }

    @Transactional
    public void recordLineage(String sourceType, UUID sourceId,
                               String targetType, UUID targetId,
                               String relationshipType) {
        Lineage lineage = new Lineage(sourceType, sourceId, targetType, targetId, relationshipType);
        lineageRepository.save(lineage);
    }

    @Transactional(readOnly = true)
    public List<Lineage> getLineage(UUID targetId, String targetType) {
        return lineageRepository.findAllByTargetTypeAndTargetId(targetType, targetId);
    }

    @Transactional(readOnly = true)
    public List<Lineage> getLineageGraph(UUID targetId, String targetType) {
        return lineageRepository.findAllByTargetTypeAndTargetId(targetType, targetId);
    }
}