package id.livingatlas.knowledgeservice.folklore.infrastructure;

import id.livingatlas.knowledgeservice.folklore.domain.Folklore;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface FolkloreRepository extends JpaRepository<Folklore, UUID> {
    Optional<Folklore> findBySlug(String slug);

    Optional<Folklore> findByObjectId(UUID objectId);
}