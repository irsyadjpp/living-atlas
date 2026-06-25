package id.livingatlas.workflowservice.publishing.infrastructure;

import id.livingatlas.workflowservice.publishing.domain.Publication;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface PublicationRepository extends JpaRepository<Publication, UUID> {
    Optional<Publication> findByResourceTypeAndResourceId(String resourceType, UUID resourceId);
    java.util.List<Publication> findByStatus(String status);
}