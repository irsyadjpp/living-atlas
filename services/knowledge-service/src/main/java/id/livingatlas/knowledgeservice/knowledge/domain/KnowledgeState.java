package id.livingatlas.knowledgeservice.knowledge.domain;

public enum KnowledgeState {
    EXTRACTED,
    REVIEW_REQUIRED,
    VERIFIED,
    PUBLISHED,
    REJECTED,
    FLAGGED;

    public boolean canTransitionTo(KnowledgeState next) {
        return switch (this) {
            case EXTRACTED -> next == REVIEW_REQUIRED || next == VERIFIED || next == REJECTED;
            case REVIEW_REQUIRED -> next == VERIFIED || next == REJECTED || next == EXTRACTED;
            case VERIFIED -> next == PUBLISHED || next == FLAGGED;
            case PUBLISHED -> next == FLAGGED;
            case REJECTED -> next == EXTRACTED;
            case FLAGGED -> next == VERIFIED || next == REJECTED;
        };
    }
}