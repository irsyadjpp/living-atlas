package id.livingatlas.workflowservice.approval.domain;

public enum ApprovalState {
    PENDING,
    APPROVED,
    REJECTED;

    public boolean canTransitionTo(ApprovalState next) {
        return switch (this) {
            case PENDING -> next == APPROVED || next == REJECTED;
            case APPROVED -> false; // Terminal state
            case REJECTED -> false; // Terminal state
        };
    }
}