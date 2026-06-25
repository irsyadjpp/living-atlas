package id.livingatlas.researchservice.exports.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.researchservice.exports.domain.Export;
import id.livingatlas.researchservice.exports.infrastructure.ExportRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ExportService {

    private final ExportRepository exportRepository;

    @Transactional
    public Export createExport(Export export) {
        export.setStatus("pending");
        export.setStartedAt(OffsetDateTime.now());
        Export saved = exportRepository.save(export);
        log.info("Export created: id={}, type={}, format={}", 
                saved.getId(), saved.getExportType(), saved.getFileFormat());
        return saved;
    }

    @Transactional(readOnly = true)
    public Export getExport(UUID id) {
        return exportRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Export not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Export> listExports(int page, int size, UUID tenantId) {
        if (tenantId != null) {
            return new org.springframework.data.domain.PageImpl<>(
                exportRepository.findByTenantId(tenantId),
                PageRequest.of(page, size),
                exportRepository.findByTenantId(tenantId).size()
            );
        }
        return exportRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Export completeExport(UUID id, String fileUrl, Long fileSize, Integer recordCount) {
        Export export = getExport(id);
        export.setStatus("completed");
        export.setFileUrl(fileUrl);
        export.setFileSize(fileSize);
        export.setRecordCount(recordCount);
        export.setCompletedAt(OffsetDateTime.now());
        Export updated = exportRepository.save(export);
        log.info("Export completed: id={}, fileUrl={}, recordCount={}", id, fileUrl, recordCount);
        return updated;
    }

    @Transactional
    public Export failExport(UUID id, String errorMessage) {
        Export export = getExport(id);
        export.setStatus("failed");
        export.setErrorMessage(errorMessage);
        export.setCompletedAt(OffsetDateTime.now());
        Export updated = exportRepository.save(export);
        log.info("Export failed: id={}, error={}", id, errorMessage);
        return updated;
    }
}