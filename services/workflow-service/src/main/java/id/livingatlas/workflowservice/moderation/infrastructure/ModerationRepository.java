package id.livingatlas.workflowservice.moderation.infrastructure;

import id.livingatlas.workflowservice.moderation.domain.Moderation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ModerationRepository extends JpaRepository<Moderation, UUID> {
    Optional<Moderation> findByResourceTypeAndResourceId(String resourceType, UUID resourceId);
    java.util.List<Moderation> findByStatus(String status);
}