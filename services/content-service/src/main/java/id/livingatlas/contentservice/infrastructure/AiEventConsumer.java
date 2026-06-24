package id.livingatlas.contentservice.infrastructure;

import id.livingatlas.sharedevents.EventTopics;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

/**
 * Consumes events from AI Platform (ai-platform/ Python services).
 * Updates content-service state based on AI pipeline results.
 * 
 * Listens on cross-boundary topics: AI Platform → Backend
 * Reference: docs/ai-platform/queue-contract-specification.md
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class AiEventConsumer {

    @KafkaListener(topics = EventTopics.SOURCE_METADATA_IMPORTED, groupId = "content-source")
    public void onSourceMetadataImported(String message) {
        log.info("Received SOURCE_METADATA_IMPORTED: {}", message);
        // AI platform has imported source metadata. Update source record in content-service.
        // message contains: sourceId, sourceType, title, description, durationSeconds, tags
    }

    @KafkaListener(topics = EventTopics.TRANSCRIPT_IMPORTED, groupId = "content-transcript")
    public void onTranscriptImported(String message) {
        log.info("Received TRANSCRIPT_IMPORTED: {}", message);
        // AI platform has imported a transcript. content-service can link transcript to source.
        // message contains: sourceId, transcriptId, language, transcriptType, textLength
    }

    @KafkaListener(topics = EventTopics.STORY_EXTRACTED, groupId = "content-story")
    public void onStoryExtracted(String message) {
        log.info("Received STORY_EXTRACTED: {}", message);
        // AI pipeline extracted a canonical story. content-service can link story to source.
        // message contains: canonicalStoryId, sourceId, storyTitle, qualityScore
    }

    @KafkaListener(topics = EventTopics.ARTICLE_GENERATED, groupId = "content-article")
    public void onArticleGenerated(String message) {
        log.info("Received ARTICLE_GENERATED: {}", message);
        // AI pipeline generated an article draft. content-service can store the draft reference.
        // message contains: articleDraftId, articleType, title, wordCount, qualityScore
    }

    @KafkaListener(topics = EventTopics.REVIEW_APPROVED, groupId = "content-review")
    public void onReviewApproved(String message) {
        log.info("Received REVIEW_APPROVED: {}", message);
        // Content approved by human reviewer. content-service can update story/article status.
        // message contains: reviewId, targetType, targetId, approvedBy
    }

    @KafkaListener(topics = EventTopics.REVIEW_REJECTED, groupId = "content-review")
    public void onReviewRejected(String message) {
        log.info("Received REVIEW_REJECTED: {}", message);
        // Content rejected by human reviewer. content-service can return to draft status.
        // message contains: reviewId, targetType, targetId, rejectionReason
    }
}
