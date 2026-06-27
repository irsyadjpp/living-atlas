package id.livingatlas.knowledgeservice.traditions.api;

import id.livingatlas.knowledgeservice.traditions.application.TraditionService;
import id.livingatlas.knowledgeservice.traditions.domain.Tradition;
import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/knowledge/traditions")
@RequiredArgsConstructor
public class TraditionsController {

    private final TraditionService traditionService;

    @PostMapping
    public ResponseEntity<ApiResponse<Tradition>> createTradition(@RequestBody Tradition tradition) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.created(traditionService.createTradition(tradition)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Tradition>> getTradition(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(traditionService.getTradition(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Tradition>> listTraditions(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(PagedResponse.from(traditionService.listTraditions(page, size)));
    }

    @PutMapping("/{id}")
    public ResponseEntity<ApiResponse<Tradition>> updateTradition(@PathVariable UUID id, @RequestBody Tradition tradition) {
        return ResponseEntity.ok(ApiResponse.success(traditionService.updateTradition(id, tradition)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteTradition(@PathVariable UUID id) {
        traditionService.deleteTradition(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}