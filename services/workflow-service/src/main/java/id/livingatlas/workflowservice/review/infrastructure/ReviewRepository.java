package id.livingatlas.workflowservice.review.infrastructure;

import id.livingatlas.workflowservice.review.domain.Review;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ReviewRepository extends JpaRepository<Review, UUID> {
    Page<Review> findByStatus(String status, Pageable pageable);
    Page<Review> findByReviewerId(UUID reviewerId, Pageable pageable);
    Page<Review> findByTargetTypeAndTargetId(String targetType, UUID targetId, Pageable pageable);
}