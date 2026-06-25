package id.livingatlas.contentservice.article.domain;

public enum ArticleState {
    GENERATING,
    DRAFT,
    REVIEW,
    PUBLISHED,
    ARCHIVED;

    public boolean canTransitionTo(ArticleState next) {
        return switch (this) {
            case GENERATING -> next == DRAFT;
            case DRAFT -> next == REVIEW || next == ARCHIVED;
            case REVIEW -> next == PUBLISHED || next == DRAFT;
            case PUBLISHED -> next == ARCHIVED || next == DRAFT;
            case ARCHIVED -> next == DRAFT; // Restore
        };
    }
}