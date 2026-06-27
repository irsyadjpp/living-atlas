package id.livingatlas.knowledgeservice.knowledge.infrastructure;

import id.livingatlas.knowledgeservice.knowledge.domain.KnowledgeObject;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface KnowledgeObjectRepository extends JpaRepository<KnowledgeObject, UUID> {
    Optional<KnowledgeObject> findBySlug(String slug);

    Page<KnowledgeObject> findByObjectType(String objectType, Pageable pageable);

    Page<KnowledgeObject> findByStatus(String status, Pageable pageable);

    Page<KnowledgeObject> findByTenantId(UUID tenantId, Pageable pageable);
}