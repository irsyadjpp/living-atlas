package id.livingatlas.researchservice.annotation.infrastructure;

import id.livingatlas.researchservice.annotation.domain.Annotation;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface AnnotationRepository extends JpaRepository<Annotation, UUID> {
    Page<Annotation> findByTargetTypeAndTargetId(String targetType, UUID targetId, Pageable pageable);
    Page<Annotation> findByTenantId(UUID tenantId, Pageable pageable);
    Page<Annotation> findByOwnerId(UUID ownerId, Pageable pageable);
}