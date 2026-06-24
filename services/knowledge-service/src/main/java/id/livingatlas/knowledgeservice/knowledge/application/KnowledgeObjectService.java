package id.livingatlas.knowledgeservice.knowledge.application;

import id.livingatlas.knowledgeservice.knowledge.domain.KnowledgeObject;
import id.livingatlas.knowledgeservice.knowledge.infrastructure.KnowledgeObjectRepository;
import id.livingatlas.knowledgeservice.shared.event.KnowledgeDomainEvent;
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
public class KnowledgeObjectService {

    private final KnowledgeObjectRepository knowledgeObjectRepository;

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
                .orElseThrow(() -> new IllegalArgumentException("Knowledge object not found: " + id));
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
    public Page<Object> listThemes(int page, int size) {
        // TODO: Implement theme listing logic
        // For now, return empty page to fix compilation
        return Page.empty();
    }

    @Transactional(readOnly = true)
    public Page<Object> search(String query, String type, int page, int size) {
        // TODO: Implement search logic
        // For now, return empty page to fix compilation
        return Page.empty();
    }
}