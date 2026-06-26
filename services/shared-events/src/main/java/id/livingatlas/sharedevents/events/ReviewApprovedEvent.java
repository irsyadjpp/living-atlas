package id.livingatlas.sharedevents.events;

import id.livingatlas.sharedevents.AbstractDomainEvent;
import id.livingatlas.sharedevents.EventMetadata;
import lombok.Getter;

import java.util.UUID;

/**
 * Published when a human reviewer approves AI-generated content.
 * <p>
 * Event version: 1
 * Producer: workflow-service
 * Consumers: content-service, knowledge-service, ai-platform (orchestration)
 * Topic: workflow.evt
 */
@Getter
public class ReviewApprovedEvent extends AbstractDomainEvent {

    private static final String EVENT_TYPE = "ReviewApproved";
    private static final int EVENT_VERSION = 1;
    private static final String PRODUCER = "workflow-service";
    private static final String AGGREGATE_TYPE = "Review";

    private final UUID reviewId;
    private final String contentType;
    private final UUID contentId;
    private final UUID reviewedBy;
    private final String reviewNotes;

    public ReviewApprovedEvent(
            UUID reviewId,
            String contentType,
            UUID contentId,
            UUID reviewedBy,
            String reviewNotes,
            EventMetadata metadata
    ) {
        super(EVENT_TYPE, EVENT_VERSION, PRODUCER, AGGREGATE_TYPE, reviewId, metadata);
        this.reviewId = reviewId;
        this.contentType = contentType;
        this.contentId = contentId;
        this.reviewedBy = reviewedBy;
        this.reviewNotes = reviewNotes;
    }

    @Override
    public Object getData() {
        return new Data(reviewId, contentType, contentId, reviewedBy, reviewNotes);
    }

    @Getter
    private static class Data {
        private final UUID reviewId;
        private final String contentType;
        private final UUID contentId;
        private final UUID reviewedBy;
        private final String reviewNotes;

        Data(UUID reviewId, String contentType, UUID contentId,
             UUID reviewedBy, String reviewNotes) {
            this.reviewId = reviewId;
            this.contentType = contentType;
            this.contentId = contentId;
            this.reviewedBy = reviewedBy;
            this.reviewNotes = reviewNotes;
        }
    }
}