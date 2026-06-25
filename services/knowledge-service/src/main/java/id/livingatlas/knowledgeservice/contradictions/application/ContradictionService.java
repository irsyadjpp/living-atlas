package id.livingatlas.knowledgeservice.contradictions.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.knowledgeservice.contradictions.domain.Contradiction;
import id.livingatlas.knowledgeservice.contradictions.infrastructure.ContradictionRepository;
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
public class ContradictionService {

    private final ContradictionRepository contradictionRepository;

    @Transactional
    public Contradiction createContradiction(Contradiction contradiction) {
        contradiction.setStatus("active");
        Contradiction saved = contradictionRepository.save(contradiction);
        log.info("Contradiction created: id={}, title={}", saved.getId(), saved.getTitle());
        return saved;
    }

    @Transactional(readOnly = true)
    public Contradiction getContradiction(UUID id) {
        return contradictionRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Contradiction not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Contradiction> listContradictions(int page, int size) {
        return contradictionRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Contradiction updateContradiction(UUID id, Contradiction updates) {
        Contradiction contradiction = getContradiction(id);
        if (updates.getTitle() != null) contradiction.setTitle(updates.getTitle());
        if (updates.getDescription() != null) contradiction.setDescription(updates.getDescription());
        if (updates.getResolutionStatus() != null) contradiction.setResolutionStatus(updates.getResolutionStatus());
        return contradictionRepository.save(contradiction);
    }

    @Transactional
    public void deleteContradiction(UUID id) {
        contradictionRepository.deleteById(id);
        log.info("Contradiction deleted: id={}", id);
    }
}