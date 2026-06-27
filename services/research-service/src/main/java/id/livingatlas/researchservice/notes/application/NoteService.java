package id.livingatlas.researchservice.notes.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.researchservice.notes.domain.Note;
import id.livingatlas.researchservice.notes.infrastructure.NoteRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class NoteService {

    private final NoteRepository noteRepository;

    @Transactional
    public Note createNote(Note note) {
        Note saved = noteRepository.save(note);
        log.info("Note created: id={}, targetType={}, targetId={}", 
                saved.getId(), saved.getTargetType(), saved.getTargetId());
        return saved;
    }

    @Transactional(readOnly = true)
    public Note getNote(UUID id) {
        return noteRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Note not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Note> listNotes(int page, int size, UUID collectionId) {
        if (collectionId != null) {
            return new PageImpl<>(
                noteRepository.findByCollectionId(collectionId).stream().toList(),
                PageRequest.of(page, size),
                noteRepository.findByCollectionId(collectionId).stream().count()
            );
        }
        return noteRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Note updateNote(UUID id, Note updates) {
        Note note = getNote(id);
        if (updates.getContent() != null) note.setContent(updates.getContent());
        return noteRepository.save(note);
    }

    @Transactional
    public void deleteNote(UUID id) {
        noteRepository.deleteById(id);
        log.info("Note deleted: id={}", id);
    }
}