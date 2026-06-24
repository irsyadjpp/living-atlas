package id.livingatlas.workflowservice.review.application;

import id.livingatlas.workflowservice.review.domain.Review;
import id.livingatlas.workflowservice.review.infrastructure.ReviewRepository;
import id.livingatlas.workflowservice.shared.event.WorkflowDomainEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ReviewService {

    private final ReviewRepository reviewRepository;

    @Transactional
    public Review requestReview(Review review) {
        review.setStatus("requested");
        Review saved = reviewRepository.save(review);
        log.info("Review requested: id={}, targetType={}, targetId={}", saved.getId(), saved.getTargetType(), saved.getTargetId());
        return saved;
    }

    @Transactional(readOnly = true)
    public Review getReview(UUID id) {
        return reviewRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Review not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Review> listReviews(int page, int size, String status, UUID reviewerId) {
        if (reviewerId != null) {
            return reviewRepository.findByReviewerId(reviewerId, PageRequest.of(page, size));
        }
        if (status != null) {
            return reviewRepository.findByStatus(status, PageRequest.of(page, size));
        }
        return reviewRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Review approveReview(UUID id, String notes) {
        Review review = getReview(id);
        review.setStatus("approved");
        review.setNotes(notes);
        review.setApprovedAt(OffsetDateTime.now());
        Review saved = reviewRepository.save(review);
        log.info("Review approved: id={}", id);
        return saved;
    }

    @Transactional
    public Review rejectReview(UUID id, String notes) {
        Review review = getReview(id);
        review.setStatus("rejected");
        review.setNotes(notes);
        review.setRejectedAt(OffsetDateTime.now());
        Review saved = reviewRepository.save(review);
        log.info("Review rejected: id={}", id);
        return saved;
    }

    @Transactional
    public Review assignReviewer(UUID id, UUID reviewerId) {
        Review review = getReview(id);
        review.setReviewerId(reviewerId);
        review.setStatus("in_review");
        return reviewRepository.save(review);
    }
}