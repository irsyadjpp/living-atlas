package id.livingatlas.workflowservice.infrastructure;

import com.fasterxml.jackson.databind.ObjectMapper;
import id.livingatlas.sharedevents.EventTopics;
import id.livingatlas.workflowservice.review.application.ReviewService;
import id.livingatlas.workflowservice.review.domain.Review;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;

/**
 * Consumes events from AI Platform article-service.
 * When AI generates an article draft, workflow-service creates a review task.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class AiEventConsumer {

    private final ReviewService reviewService;
    private final ObjectMapper objectMapper;

    @KafkaListener(topics = EventTopics.ARTICLE_GENERATED, groupId = "workflow-article")
    public void onArticleGenerated(String message) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> data = objectMapper.readValue(message, Map.class);
            
            String articleDraftId = (String) data.get("articleDraftId");
            String articleType = (String) data.getOrDefault("articleType", "unknown");
            String title = (String) data.getOrDefault("title", "Untitled");
            Number qualityScore = (Number) data.getOrDefault("qualityScore", 0.0);
            
            log.info("Received ARTICLE_GENERATED: title={}, type={}, draftId={}, quality={}", 
                title, articleType, articleDraftId, qualityScore);

            // Create a review task for the AI-generated article draft
            Review review = new Review();
            review.setTargetType("article_draft");
            review.setTargetId(UUID.fromString(articleDraftId));
            review.setStatus("requested");
            review.setPriority(qualityScore.doubleValue() >= 0.7 ? "normal" : "high");
            review.setNotes("AI-generated " + articleType + " article: " + title);
            
            reviewService.requestReview(review);
            log.info("Review created for AI article draft: draftId={}, reviewId={}", 
                articleDraftId, review.getId());
            
        } catch (Exception e) {
            log.error("Error processing ARTICLE_GENERATED event: {}", e.getMessage(), e);
        }
    }
}