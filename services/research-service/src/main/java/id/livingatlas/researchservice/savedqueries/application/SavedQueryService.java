package id.livingatlas.researchservice.savedqueries.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.researchservice.savedqueries.domain.SavedQuery;
import id.livingatlas.researchservice.savedqueries.infrastructure.SavedQueryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class SavedQueryService {

    private final SavedQueryRepository savedQueryRepository;

    @Transactional
    public SavedQuery createSavedQuery(SavedQuery savedQuery) {
        SavedQuery saved = savedQueryRepository.save(savedQuery);
        log.info("SavedQuery created: id={}, name={}", saved.getId(), saved.getName());
        return saved;
    }

    @Transactional(readOnly = true)
    public SavedQuery getSavedQuery(UUID id) {
        return savedQueryRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("SavedQuery not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<SavedQuery> listSavedQueries(int page, int size, UUID tenantId) {
        if (tenantId != null) {
            return new org.springframework.data.domain.PageImpl<>(
                savedQueryRepository.findByTenantId(tenantId),
                PageRequest.of(page, size),
                savedQueryRepository.findByTenantId(tenantId).size()
            );
        }
        return savedQueryRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public SavedQuery updateSavedQuery(UUID id, SavedQuery updates) {
        SavedQuery savedQuery = getSavedQuery(id);
        if (updates.getName() != null) savedQuery.setName(updates.getName());
        if (updates.getDescription() != null) savedQuery.setDescription(updates.getDescription());
        if (updates.getQueryText() != null) savedQuery.setQueryText(updates.getQueryText());
        if (updates.getParameters() != null) savedQuery.setParameters(updates.getParameters());
        return savedQueryRepository.save(savedQuery);
    }

    @Transactional
    public void deleteSavedQuery(UUID id) {
        savedQueryRepository.deleteById(id);
        log.info("SavedQuery deleted: id={}", id);
    }
}