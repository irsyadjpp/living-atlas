package id.livingatlas.contentservice.story.domain;

public enum StoryState {
    DRAFT,
    REVIEW,
    APPROVED,
    REJECTED,
    PUBLISHED,
    ARCHIVED;

    public boolean canTransitionTo(StoryState next) {
        return switch (this) {
            case DRAFT -> next == REVIEW || next == ARCHIVED;
            case REVIEW -> next == APPROVED || next == REJECTED || next == DRAFT;
            case APPROVED -> next == PUBLISHED || next == ARCHIVED || next == DRAFT;
            case REJECTED -> next == DRAFT;
            case PUBLISHED -> next == ARCHIVED || next == DRAFT;
            case ARCHIVED -> next == DRAFT; // Restore
        };
    }
}