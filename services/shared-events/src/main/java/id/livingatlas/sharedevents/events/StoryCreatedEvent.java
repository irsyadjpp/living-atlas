package id.livingatlas.sharedevents.events;

import id.livingatlas.sharedevents.AbstractDomainEvent;
import id.livingatlas.sharedevents.EventMetadata;
import lombok.Getter;

import java.util.UUID;

/**
 * Published when a story is first created from an AI extraction.
 * <p>
 * Event version: 1
 * Producer: content-service
 * Consumers: knowledge-service, workflow-service, ai-platform (orchestration)
 * Topic: content.evt
 */
@Getter
public class StoryCreatedEvent extends AbstractDomainEvent {

    private static final String EVENT_TYPE = "StoryCreated";
    private static final int EVENT_VERSION = 1;
    private static final String PRODUCER = "content-service";
    private static final String AGGREGATE_TYPE = "Story";

    private final UUID storyId;
    private final String title;
    private final String slug;
    private final String storyType;
    private final UUID sourceId;
    private final UUID transcriptId;
    private final UUID createdBy;

    public StoryCreatedEvent(
            UUID storyId,
            String title,
            String slug,
            String storyType,
            UUID sourceId,
            UUID transcriptId,
            UUID createdBy,
            EventMetadata metadata
    ) {
        super(EVENT_TYPE, EVENT_VERSION, PRODUCER, AGGREGATE_TYPE, storyId, metadata);
        this.storyId = storyId;
        this.title = title;
        this.slug = slug;
        this.storyType = storyType;
        this.sourceId = sourceId;
        this.transcriptId = transcriptId;
        this.createdBy = createdBy;
    }

    @Override
    public Object getData() {
        return new Data(storyId, title, slug, storyType, sourceId, transcriptId, createdBy);
    }

    @Getter
    private static class Data {
        private final UUID storyId;
        private final String title;
        private final String slug;
        private final String storyType;
        private final UUID sourceId;
        private final UUID transcriptId;
        private final UUID createdBy;

        Data(UUID storyId, String title, String slug, String storyType,
             UUID sourceId, UUID transcriptId, UUID createdBy) {
            this.storyId = storyId;
            this.title = title;
            this.slug = slug;
            this.storyType = storyType;
            this.sourceId = sourceId;
            this.transcriptId = transcriptId;
            this.createdBy = createdBy;
        }
    }
}