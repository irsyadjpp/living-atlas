package id.livingatlas.researchservice.collections.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.researchservice.collections.domain.Collection;
import id.livingatlas.researchservice.collections.infrastructure.CollectionRepository;
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
public class CollectionService {

    private final CollectionRepository collectionRepository;

    @Transactional
    public Collection createCollection(Collection collection) {
        Collection saved = collectionRepository.save(collection);
        log.info("Collection created: id={}, name={}, ownerId={}", saved.getId(), saved.getName(), saved.getOwnerId());
        return saved;
    }

    @Transactional(readOnly = true)
    public Collection getCollection(UUID id) {
        return collectionRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Collection not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Collection> listCollections(int page, int size, UUID ownerId) {
        if (ownerId != null) {
            List<Collection> results = collectionRepository.findByOwnerId(ownerId);
            return new org.springframework.data.domain.PageImpl<>(results, PageRequest.of(page, size), results.size());
        }
        return collectionRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional(readOnly = true)
    public List<Collection> getSharedCollections() {
        return collectionRepository.findByIsSharedTrue();
    }

    @Transactional
    public Collection updateCollection(UUID id, String name, String description) {
        Collection collection = getCollection(id);
        if (name != null) collection.setName(name);
        if (description != null) collection.setDescription(description);
        Collection saved = collectionRepository.save(collection);
        log.info("Collection updated: id={}", id);
        return saved;
    }

    @Transactional
    public void shareCollection(UUID id, boolean share) {
        Collection collection = getCollection(id);
        collection.setIsShared(share);
        collectionRepository.save(collection);
        log.info("Collection share status updated: id={}, shared={}", id, share);
    }

    @Transactional
    public void deleteCollection(UUID id) {
        collectionRepository.deleteById(id);
        log.info("Collection deleted: id={}", id);
    }
}