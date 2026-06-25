package id.livingatlas.knowledgeservice.contradictions.infrastructure;

import id.livingatlas.knowledgeservice.contradictions.domain.Contradiction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ContradictionRepository extends JpaRepository<Contradiction, UUID> {
    Optional<Contradiction> findBySlug(String slug);
    Optional<Contradiction> findByClaimId1OrClaimId2(UUID claimId1, UUID claimId2);
}