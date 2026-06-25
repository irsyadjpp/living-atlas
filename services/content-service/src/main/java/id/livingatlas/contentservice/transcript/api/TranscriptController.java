package id.livingatlas.contentservice.transcript.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.contentservice.transcript.application.TranscriptService;
import id.livingatlas.contentservice.transcript.domain.Transcript;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/transcripts")
@RequiredArgsConstructor
public class TranscriptController {

    private final TranscriptService transcriptService;

    @PostMapping
    public ResponseEntity<ApiResponse<Transcript>> createTranscript(@RequestBody Transcript transcript) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(transcriptService.createTranscript(transcript)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Transcript>> getTranscript(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(transcriptService.getTranscript(id)));
    }

    @GetMapping("/by-source/{sourceId}")
    public ResponseEntity<ApiResponse<List<Transcript>>> getTranscriptsBySource(@PathVariable UUID sourceId) {
        return ResponseEntity.ok(ApiResponse.success(transcriptService.getTranscriptsBySource(sourceId)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Transcript>> listTranscripts(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID sourceId) {
        return ResponseEntity.ok(PagedResponse.from(transcriptService.listTranscripts(page, size, sourceId)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Transcript>> updateTranscript(
            @PathVariable UUID id,
            @RequestBody Map<String, String> request) {
        return ResponseEntity.ok(ApiResponse.success(
            transcriptService.updateTranscript(id, request.get("content"), request.get("languageCode"))));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteTranscript(@PathVariable UUID id) {
        transcriptService.deleteTranscript(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}