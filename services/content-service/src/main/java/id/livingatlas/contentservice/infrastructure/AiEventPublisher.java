package id.livingatlas.contentservice.infrastructure;

import id.livingatlas.sharedevents.AiBridgeEvent;
import id.livingatlas.sharedevents.EventTopics;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class AiEventPublisher {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    /**
     * Notify AI platform that a new source has been submitted for processing.
     */
    public void publishSourceSubmitted(String sourceType, String platformSourceId, java.util.UUID channelId) {
        var aggregateId = channelId != null ? channelId : java.util.UUID.randomUUID();
        var channelIdStr = channelId != null ? channelId.toString() : "";
        var data = String.format(
            "{\"sourceType\":\"%s\",\"platformSourceId\":\"%s\",\"channelId\":\"%s\"}",
            sourceType, platformSourceId, channelIdStr
        );
        var event = new AiBridgeEvent(
            EventTopics.SOURCE_SUBMITTED, "content-service", aggregateId, data
        );
        kafkaTemplate.send(EventTopics.SOURCE_SUBMITTED, aggregateId.toString(), event);
        log.info("Published {}: sourceType={}, platformSourceId={}", 
            EventTopics.SOURCE_SUBMITTED, sourceType, platformSourceId);
    }

    /**
     * Notify AI platform and knowledge service that a story has been published.
     */
    public void publishStoryPublished(java.util.UUID storyId, String slug) {
        var data = String.format(
            "{\"storyId\":\"%s\",\"slug\":\"%s\",\"status\":\"published\"}",
            storyId, slug
        );
        var event = new AiBridgeEvent(
            EventTopics.STORY_PUBLISHED, "content-service", storyId, data
        );
        kafkaTemplate.send(EventTopics.STORY_PUBLISHED, storyId.toString(), event);
        log.info("Published {}: storyId={}", EventTopics.STORY_PUBLISHED, storyId);
    }

    /**
     * Notify AI platform and workflow service that an article has been generated.
     */
    public void publishArticleGenerated(java.util.UUID articleDraftId, String articleType, String title, double qualityScore) {
        var data = String.format(
            "{\"articleDraftId\":\"%s\",\"articleType\":\"%s\",\"title\":\"%s\",\"qualityScore\":%f}",
            articleDraftId, articleType, title, qualityScore
        );
        var event = new AiBridgeEvent(
            EventTopics.ARTICLE_GENERATED, "content-service", articleDraftId, data
        );
        kafkaTemplate.send(EventTopics.ARTICLE_GENERATED, articleDraftId.toString(), event);
        log.info("Published {}: articleDraftId={}", EventTopics.ARTICLE_GENERATED, articleDraftId);
    }

    /**
     * Notify AI platform that a human-approved article has been published.
     */
    public void publishArticlePublished(java.util.UUID articleId, java.util.UUID originalDraftId) {
        var data = String.format(
            "{\"articleId\":\"%s\",\"originalDraftId\":\"%s\",\"publishedAt\":\"%s\"}",
            articleId, originalDraftId, java.time.OffsetDateTime.now()
        );
        var event = new AiBridgeEvent(
            EventTopics.ARTICLE_PUBLISHED, "content-service", articleId, data
        );
        kafkaTemplate.send(EventTopics.ARTICLE_PUBLISHED, articleId.toString(), event);
        log.info("Published {}: articleId={}", EventTopics.ARTICLE_PUBLISHED, articleId);
    }
}