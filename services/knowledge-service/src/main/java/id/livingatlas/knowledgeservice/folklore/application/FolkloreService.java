package id.livingatlas.knowledgeservice.folklore.application;

import id.livingatlas.knowledgeservice.folklore.domain.Folklore;
import id.livingatlas.knowledgeservice.folklore.infrastructure.FolkloreRepository;
import id.livingatlas.sharedweb.exception.ApiException;
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
public class FolkloreService {

    private final FolkloreRepository folkloreRepository;

    @Transactional
    public Folklore createFolklore(Folklore folklore) {
//        folklore.setStatus("active");
        Folklore saved = folkloreRepository.save(folklore);
        log.info("Folklore created: id={}, name={}", saved.getId(), saved.getName());
        return saved;
    }

    @Transactional(readOnly = true)
    public Folklore getFolklore(UUID id) {
        return folkloreRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Folklore not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Folklore> listFolklore(int page, int size) {
        return folkloreRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Folklore updateFolklore(UUID id, Folklore updates) {
        Folklore folklore = getFolklore(id);
        if (updates.getName() != null) folklore.setName(updates.getName());
        if (updates.getDescription() != null) folklore.setDescription(updates.getDescription());
        if (updates.getOriginRegion() != null) folklore.setOriginRegion(updates.getOriginRegion());
        if (updates.getCulturalContext() != null) folklore.setCulturalContext(updates.getCulturalContext());
        return folkloreRepository.save(folklore);
    }

    @Transactional
    public void deleteFolklore(UUID id) {
        folkloreRepository.deleteById(id);
        log.info("Folklore deleted: id={}", id);
    }
}