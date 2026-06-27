package id.livingatlas.knowledgeservice.beliefs.infrastructure;

import id.livingatlas.knowledgeservice.beliefs.domain.Belief;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface BeliefRepository extends JpaRepository<Belief, UUID> {
    Optional<Belief> findBySlug(String slug);

    Optional<Belief> findByObjectId(UUID objectId);
}