package id.livingatlas.knowledgeservice.knowledge.application;

import id.livingatlas.knowledgeservice.knowledge.domain.KnowledgeObject;
import id.livingatlas.knowledgeservice.knowledge.infrastructure.KnowledgeObjectRepository;
import id.livingatlas.knowledgeservice.themes.domain.Theme;
import id.livingatlas.knowledgeservice.themes.infrastructure.ThemeRepository;
import id.livingatlas.sharedweb.exception.ApiException;
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
public class KnowledgeObjectService {

    private final KnowledgeObjectRepository knowledgeObjectRepository;
    private final ThemeRepository themeRepository;

    @Transactional
    public KnowledgeObject createKnowledgeObject(KnowledgeObject obj) {
        obj.setStatus("active");
        KnowledgeObject saved = knowledgeObjectRepository.save(obj);
        log.info("Knowledge object created: id={}, type={}, name={}", saved.getId(), saved.getObjectType(), saved.getCanonicalName());
        // Domain event would be published here
        return saved;
    }

    @Transactional(readOnly = true)
    public KnowledgeObject getKnowledgeObject(UUID id) {
        return knowledgeObjectRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Knowledge object not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<KnowledgeObject> listKnowledgeObjects(int page, int size, String type, String status) {
        return knowledgeObjectRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public KnowledgeObject updateKnowledgeObject(UUID id, KnowledgeObject updates) {
        KnowledgeObject obj = getKnowledgeObject(id);
        if (updates.getCanonicalName() != null) obj.setCanonicalName(updates.getCanonicalName());
        if (updates.getSummary() != null) obj.setSummary(updates.getSummary());
        if (updates.getConfidenceScore() != null) obj.setConfidenceScore(updates.getConfidenceScore());
        return knowledgeObjectRepository.save(obj);
    }

    @Transactional
    public void deleteKnowledgeObject(UUID id) {
        knowledgeObjectRepository.deleteById(id);
        log.info("Knowledge object soft-deleted: id={}", id);
    }

    // Alias methods for controller compatibility
    @Transactional(readOnly = true)
    public KnowledgeObject getObject(UUID id) {
        return getKnowledgeObject(id);
    }

    @Transactional
    public KnowledgeObject createObject(KnowledgeObject obj) {
        return createKnowledgeObject(obj);
    }

    @Transactional(readOnly = true)
    public Page<Theme> listThemes(int page, int size) {
        return themeRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional(readOnly = true)
    public Page<KnowledgeObject> search(String query, String type, int page, int size) {
        // TODO: Implement full-text search logic
        // For now, return all knowledge objects (in production, use PostgreSQL full-text search or Weaviate)
        if (query == null || query.isEmpty()) {
            return knowledgeObjectRepository.findAll(PageRequest.of(page, size));
        }

        // Simple LIKE search as placeholder
        // In production, this should use PostgreSQL tsvector or Weaviate vector search
        List<KnowledgeObject> results = knowledgeObjectRepository.findAll();
        List<KnowledgeObject> filtered = results.stream()
                .filter(obj -> obj.getCanonicalName().toLowerCase().contains(query.toLowerCase()) ||
                        (obj.getSummary() != null && obj.getSummary().toLowerCase().contains(query.toLowerCase())))
                .toList();

        int start = Math.min(page * size, filtered.size());
        int end = Math.min(start + size, filtered.size());

        return new org.springframework.data.domain.PageImpl<>(
                filtered.subList(start, end),
                PageRequest.of(page, size),
                filtered.size()
        );
    }
}
