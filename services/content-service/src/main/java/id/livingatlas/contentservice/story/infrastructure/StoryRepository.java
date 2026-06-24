package id.livingatlas.contentservice.story.infrastructure;

import id.livingatlas.contentservice.story.domain.Story;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface StoryRepository extends JpaRepository<Story, UUID> {
    Optional<Story> findBySlug(String slug);
    Page<Story> findByStatus(String status, Pageable pageable);
    Page<Story> findByTenantId(UUID tenantId, Pageable pageable);
}