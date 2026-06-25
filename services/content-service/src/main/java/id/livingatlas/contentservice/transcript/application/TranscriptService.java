package id.livingatlas.contentservice.transcript.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.contentservice.transcript.domain.Transcript;
import id.livingatlas.contentservice.transcript.infrastructure.TranscriptRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class TranscriptService {

    private final TranscriptRepository transcriptRepository;

    @Transactional
    public Transcript createTranscript(Transcript transcript) {
        if (transcript.getContent() != null) {
            transcript.setTextLength(transcript.getContent().length());
        }
        Transcript saved = transcriptRepository.save(transcript);
        log.info("Transcript created: id={}, sourceId={}, type={}", saved.getId(), saved.getSourceId(), saved.getTranscriptType());
        return saved;
    }

    @Transactional(readOnly = true)
    public Transcript getTranscript(UUID id) {
        return transcriptRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Transcript not found: " + id));
    }

    @Transactional(readOnly = true)
    public List<Transcript> getTranscriptsBySource(UUID sourceId) {
        return transcriptRepository.findBySourceId(sourceId);
    }

    @Transactional(readOnly = true)
    public Page<Transcript> listTranscripts(int page, int size, UUID sourceId) {
        if (sourceId != null) {
            List<Transcript> results = transcriptRepository.findBySourceId(sourceId);
            int start = Math.min(page * size, results.size());
            int end = Math.min(start + size, results.size());
            return new org.springframework.data.domain.PageImpl<>(
                results.subList(start, end), PageRequest.of(page, size), results.size());
        }
        return transcriptRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Transcript updateTranscript(UUID id, String content, String languageCode) {
        Transcript transcript = getTranscript(id);
        if (content != null) {
            transcript.setContent(content);
            transcript.setTextLength(content.length());
        }
        if (languageCode != null) transcript.setLanguageCode(languageCode);
        Transcript saved = transcriptRepository.save(transcript);
        log.info("Transcript updated: id={}", id);
        return saved;
    }

    @Transactional
    public void deleteTranscript(UUID id) {
        transcriptRepository.deleteById(id);
        log.info("Transcript deleted: id={}", id);
    }
}