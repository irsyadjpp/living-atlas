package id.livingatlas.contentservice.transcript.infrastructure;

import id.livingatlas.contentservice.transcript.domain.Transcript;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface TranscriptRepository extends JpaRepository<Transcript, UUID> {
    List<Transcript> findBySourceId(UUID sourceId);
    Optional<Transcript> findBySourceIdAndLanguageCode(UUID sourceId, String languageCode);
    List<Transcript> findByTranscriptType(String transcriptType);
}