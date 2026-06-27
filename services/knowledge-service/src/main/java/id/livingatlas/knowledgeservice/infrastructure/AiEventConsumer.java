package id.livingatlas.knowledgeservice.infrastructure;

import com.fasterxml.jackson.databind.ObjectMapper;
import id.livingatlas.knowledgeservice.knowledge.application.KnowledgeObjectService;
import id.livingatlas.knowledgeservice.knowledge.domain.KnowledgeObject;
import id.livingatlas.sharedevents.EventTopics;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * Consumes events from AI Platform enrichment pipeline.
 * When a story is extracted by AI, knowledge-service creates a KnowledgeObject.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class AiEventConsumer {

    private final KnowledgeObjectService knowledgeObjectService;
    private final ObjectMapper objectMapper;

    @KafkaListener(topics = EventTopics.STORY_EXTRACTED, groupId = "knowledge-extracted")
    public void onStoryExtracted(String message) {
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> data = objectMapper.readValue(message, Map.class);

            String storyTitle = (String) data.getOrDefault("storyTitle", "Unknown Story");
            String canonicalStoryId = (String) data.get("canonicalStoryId");
            Number qualityScore = (Number) data.getOrDefault("qualityScore", 0.0);

            log.info("Received STORY_EXTRACTED: title={}, storyId={}, quality={}",
                    storyTitle, canonicalStoryId, qualityScore);

            // Create a knowledge object for the extracted story
            KnowledgeObject obj = new KnowledgeObject();
            obj.setObjectType("story");
            obj.setCanonicalName(storyTitle);
            obj.setSummary("AI-extracted story from video pipeline");
            if (canonicalStoryId != null) {
                obj.setSlug(storyTitle.toLowerCase().replaceAll("[^a-z0-9]+", "-") + "-" + canonicalStoryId.substring(0, 8));
            }
            if (qualityScore != null) {
                obj.setConfidenceScore(new java.math.BigDecimal(qualityScore.doubleValue()));
            }

            knowledgeObjectService.createKnowledgeObject(obj);
            log.info("KnowledgeObject created from AI story: {}", obj.getId());

        } catch (Exception e) {
            log.error("Error processing STORY_EXTRACTED event: {}", e.getMessage(), e);
        }
    }

    @KafkaListener(topics = EventTopics.STORY_PUBLISHED, groupId = "knowledge-service")
    public void onStoryPublished(String message) {
        log.info("Received STORY_PUBLISHED: {}", message);
        // Story has been human-approved and published. Update knowledge object status.
    }
}