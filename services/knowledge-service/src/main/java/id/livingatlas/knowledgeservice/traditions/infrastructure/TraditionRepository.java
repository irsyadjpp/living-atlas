package id.livingatlas.knowledgeservice.traditions.infrastructure;

import id.livingatlas.knowledgeservice.traditions.domain.Tradition;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface TraditionRepository extends JpaRepository<Tradition, UUID> {
    Optional<Tradition> findBySlug(String slug);

    Optional<Tradition> findByObjectId(UUID objectId);
}