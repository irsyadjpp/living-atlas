package id.livingatlas.workflowservice.publishing.domain;

public enum PublicationState {
    DRAFT,
    PUBLISHED,
    UNPUBLISHED;

    public boolean canTransitionTo(PublicationState next) {
        return switch (this) {
            case DRAFT -> next == PUBLISHED;
            case PUBLISHED -> next == UNPUBLISHED;
            case UNPUBLISHED -> false; // Terminal state
        };
    }
}