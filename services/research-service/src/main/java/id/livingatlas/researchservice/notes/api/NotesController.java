package id.livingatlas.researchservice.notes.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.researchservice.notes.application.NoteService;
import id.livingatlas.researchservice.notes.domain.Note;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/research/notes")
@RequiredArgsConstructor
public class NotesController {

    private final NoteService noteService;

    @PostMapping
    public ResponseEntity<ApiResponse<Note>> createNote(@RequestBody Note note) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(noteService.createNote(note)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Note>> getNote(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(noteService.getNote(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Note>> listNotes(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID collectionId) {
        return ResponseEntity.ok(PagedResponse.from(noteService.listNotes(page, size, collectionId)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Note>> updateNote(@PathVariable UUID id, @RequestBody Note note) {
        return ResponseEntity.ok(ApiResponse.success(noteService.updateNote(id, note)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteNote(@PathVariable UUID id) {
        noteService.deleteNote(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}