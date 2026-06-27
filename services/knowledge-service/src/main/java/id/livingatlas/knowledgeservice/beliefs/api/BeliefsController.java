package id.livingatlas.knowledgeservice.beliefs.api;

import id.livingatlas.knowledgeservice.beliefs.application.BeliefService;
import id.livingatlas.knowledgeservice.beliefs.domain.Belief;
import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/knowledge/beliefs")
@RequiredArgsConstructor
public class BeliefsController {

    private final BeliefService beliefService;

    @PostMapping
    public ResponseEntity<ApiResponse<Belief>> createBelief(@RequestBody Belief belief) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(beliefService.createBelief(belief)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Belief>> getBelief(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(beliefService.getBelief(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Belief>> listBeliefs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(beliefService.listBeliefs(page, size)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Belief>> updateBelief(@PathVariable UUID id, @RequestBody Belief belief) {
        return ResponseEntity.ok(ApiResponse.success(beliefService.updateBelief(id, belief)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteBelief(@PathVariable UUID id) {
        beliefService.deleteBelief(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}