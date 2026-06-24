package id.livingatlas.workflowservice.review.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.sharedweb.exception.ApiException;
import id.livingatlas.workflowservice.review.application.ReviewService;
import id.livingatlas.workflowservice.review.domain.Review;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/workflow/reviews")
@RequiredArgsConstructor
public class ReviewController {

    private final ReviewService reviewService;

    @PostMapping
    public ResponseEntity<ApiResponse<Review>> requestReview(@RequestBody Review review) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(reviewService.requestReview(review)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Review>> getReview(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(reviewService.getReview(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Review>> listReviews(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) UUID reviewerId) {
        return ResponseEntity.ok(PagedResponse.from(reviewService.listReviews(page, size, status, reviewerId)));
    }

    @PostMapping("/{id}/approve")
    public ResponseEntity<ApiResponse<Review>> approveReview(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(ApiResponse.success(reviewService.approveReview(id, body.getOrDefault("notes", ""))));
    }

    @PostMapping("/{id}/reject")
    public ResponseEntity<ApiResponse<Review>> rejectReview(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(ApiResponse.success(reviewService.rejectReview(id, body.getOrDefault("notes", ""))));
    }

    @PostMapping("/{id}/assign")
    public ResponseEntity<ApiResponse<Review>> assignReviewer(@PathVariable UUID id, @RequestBody Map<String, UUID> body) {
        return ResponseEntity.ok(ApiResponse.success(reviewService.assignReviewer(id, body.get("reviewerId"))));
    }
}
