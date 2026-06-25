package id.livingatlas.knowledgeservice.claims.domain;

public enum ClaimState {
    EXTRACTED,
    UNVERIFIED,
    VERIFIED,
    ACCEPTED,
    DISPUTED,
    REJECTED;

    public boolean canTransitionTo(ClaimState next) {
        return switch (this) {
            case EXTRACTED -> next == UNVERIFIED;
            case UNVERIFIED -> next == VERIFIED || next == DISPUTED || next == REJECTED;
            case VERIFIED -> next == ACCEPTED || next == DISPUTED;
            case DISPUTED -> next == VERIFIED || next == REJECTED;
            case ACCEPTED -> false; // Terminal state
            case REJECTED -> false; // Terminal state
        };
    }
}