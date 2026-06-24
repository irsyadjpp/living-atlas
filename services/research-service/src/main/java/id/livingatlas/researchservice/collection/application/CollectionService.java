package id.livingatlas.researchservice.collection.application;

import id.livingatlas.researchservice.collection.domain.Collection;
import id.livingatlas.researchservice.collection.infrastructure.CollectionRepository;
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
public class CollectionService {

    private final CollectionRepository collectionRepository;

    @Transactional
    public Collection createCollection(Collection collection) {
        collection.setItemCount(0);
        Collection saved = collectionRepository.save(collection);
        log.info("Collection created: id={}, name={}", saved.getId(), saved.getName());
        return saved;
    }

    @Transactional(readOnly = true)
    public Collection getCollection(UUID id) {
        return collectionRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Collection not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Collection> listCollections(int page, int size, UUID tenantId) {
        return collectionRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Collection updateCollection(UUID id, Collection updates) {
        Collection collection = getCollection(id);
        if (updates.getName() != null) collection.setName(updates.getName());
        if (updates.getDescription() != null) collection.setDescription(updates.getDescription());
        if (updates.getVisibility() != null) collection.setVisibility(updates.getVisibility());
        return collectionRepository.save(collection);
    }

    @Transactional
    public void deleteCollection(UUID id) {
        collectionRepository.deleteById(id);
        log.info("Collection soft-deleted: id={}", id);
    }

    @Transactional
    public void addItem(UUID collectionId, Object request) {
        Collection collection = getCollection(collectionId);
        collection.setItemCount(collection.getItemCount() + 1);
        collectionRepository.save(collection);
        log.info("Item added to collection: collectionId={}, itemCount={}", collectionId, collection.getItemCount());
        // TODO: Implement proper item storage logic when item entity is defined
    }
}