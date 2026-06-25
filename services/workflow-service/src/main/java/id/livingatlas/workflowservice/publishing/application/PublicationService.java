package id.livingatlas.workflowservice.publishing.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.workflowservice.publishing.domain.Publication;
import id.livingatlas.workflowservice.publishing.infrastructure.PublicationRepository;
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
public class PublicationService {

    private final PublicationRepository publicationRepository;

    @Transactional
    public Publication createPublication(Publication publication) {
        publication.setStatus("draft");
        Publication saved = publicationRepository.save(publication);
        log.info("Publication created: id={}, resourceType={}, resourceId={}", 
                saved.getId(), saved.getResourceType(), saved.getResourceId());
        return saved;
    }

    @Transactional(readOnly = true)
    public Publication getPublication(UUID id) {
        return publicationRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Publication not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Publication> listPublications(int page, int size, String status) {
        if (status != null && !status.isEmpty()) {
            return new org.springframework.data.domain.PageImpl<>(
                publicationRepository.findByStatus(status),
                PageRequest.of(page, size),
                publicationRepository.findByStatus(status).size()
            );
        }
        return publicationRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Publication publish(UUID id, UUID publishedBy) {
        Publication publication = getPublication(id);
        publication.setPublishedBy(publishedBy);
        publication.setStatus("published");
        publication.setPublishedAt(OffsetDateTime.now());
        Publication updated = publicationRepository.save(publication);
        log.info("Publication published: id={}, publishedBy={}", id, publishedBy);
        return updated;
    }

    @Transactional
    public Publication unpublish(UUID id) {
        Publication publication = getPublication(id);
        publication.setStatus("unpublished");
        Publication updated = publicationRepository.save(publication);
        log.info("Publication unpublished: id={}", id);
        return updated;
    }
}