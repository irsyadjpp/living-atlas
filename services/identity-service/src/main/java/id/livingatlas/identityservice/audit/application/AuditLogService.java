package id.livingatlas.identityservice.audit.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.identityservice.audit.domain.AuditLog;
import id.livingatlas.identityservice.audit.infrastructure.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuditLogService {

    private final AuditLogRepository auditLogRepository;

    @Transactional(readOnly = true)
    public AuditLog getAuditLog(UUID id) {
        return auditLogRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Audit log not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<AuditLog> searchAuditLogs(int page, int size, UUID userId, UUID tenantId, String resourceType, UUID resourceId) {
        List<AuditLog> results = auditLogRepository.searchAuditLogs(userId, tenantId, resourceType, resourceId);
        int start = Math.min(page * size, results.size());
        int end = Math.min(start + size, results.size());
        return new org.springframework.data.domain.PageImpl<>(
            results.subList(start, end),
            PageRequest.of(page, size),
            results.size()
        );
    }
}