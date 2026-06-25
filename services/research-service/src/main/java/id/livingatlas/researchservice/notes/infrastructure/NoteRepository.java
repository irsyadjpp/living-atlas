package id.livingatlas.researchservice.notes.infrastructure;

import id.livingatlas.researchservice.notes.domain.Note;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface NoteRepository extends JpaRepository<Note, UUID> {
    Optional<Note> findByCollectionId(UUID collectionId);
    java.util.List<Note> findByTargetTypeAndTargetId(String targetType, UUID targetId);
}