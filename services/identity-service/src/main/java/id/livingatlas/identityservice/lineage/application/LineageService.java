package id.livingatlas.identityservice.lineage.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.identityservice.lineage.domain.Lineage;
import id.livingatlas.identityservice.lineage.infrastructure.LineageRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class LineageService {

    private final LineageRepository lineageRepository;

    @Transactional
    public Lineage createLineage(Lineage lineage) {
        Lineage saved = lineageRepository.save(lineage);
        log.info("Lineage created: id={}, objectId={}, parentObjectId={}", 
                saved.getId(), saved.getObjectId(), saved.getParentObjectId());
        return saved;
    }

    @Transactional(readOnly = true)
    public List<Lineage> getLineage(UUID objectId, String objectType) {
        return lineageRepository.findByObjectIdAndObjectType(objectId, objectType);
    }

    @Transactional(readOnly = true)
    public List<Lineage> getChildren(UUID parentObjectId) {
        return lineageRepository.findByParentObjectId(parentObjectId);
    }
}