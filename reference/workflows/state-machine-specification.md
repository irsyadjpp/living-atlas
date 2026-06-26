# State Machine Specification

## Version 1.0
## Status: Draft

---

# Overview

This document defines all state machines in The Living Atlas platform. State machines govern the lifecycle of domain entities: stories, articles, knowledge objects, claims, sources, and AI pipeline jobs.

All state machines follow these principles:
1. **Validated transitions**: Only defined transitions are allowed
2. **Audited moves**: Every transition is logged in audit_logs
3. **Event emitting**: Each transition emits a domain event
4. **Side effects**: Transitions may trigger workflows, notifications, or pipeline jobs

---

# 1. Story State Machine

## States
```
DRAFT → REVIEW → APPROVED → PUBLISHED → ARCHIVED
                      ↓
                  REJECTED (→ DRAFT)
```

## State Definitions

| State | Description | Visibility | Editable |
|-------|-------------|-----------|----------|
| DRAFT | Initial state, being written | Creator only | Yes |
| REVIEW | Submitted for editorial review | Creator + Reviewers | No |
| APPROVED | Passed review, ready to publish | Creator + Reviewers | Limited |
| PUBLISHED | Publicly available | Everyone | No (new version) |
| REJECTED | Failed review, returned for revision | Creator + Reviewers | Yes |
| ARCHIVED | Removed from publication | Admins only | No |

## Transitions

| From | To | Trigger | Required Role | Side Effects |
|------|----|---------|---------------|-------------|
| DRAFT | REVIEW | Story submitted | Creator | Emits StorySubmittedForReview |
| REVIEW | APPROVED | Review passed | Reviewer | Emits StoryApproved |
| REVIEW | REJECTED | Review failed | Reviewer | Emits StoryRejected |
| APPROVED | PUBLISHED | Publish action | Editor | Emits StoryPublished |
| APPROVED | DRAFT | Unapprove | Admin | Reverts to draft |
| REJECTED | DRAFT | Resubmit | Creator | Clears rejection reason |
| PUBLISHED | ARCHIVED | Archive action | Admin | Emits StoryArchived |
| PUBLISHED | DRAFT | Unpublish | Admin | Emits StoryArchived |
| ARCHIVED | DRAFT | Restore | Admin | Reverts to draft |

## Transition Validation Rules
1. Story must have at least one evidence link before REVIEW
2. Story must have at least one entity association before REVIEW
3. Reviewer must not be the same as creator
4. Published story cannot be edited; create new version instead

---

# 2. Knowledge Object State Machine

## States
```
EXTRACTED → REVIEW_REQUIRED → VERIFIED → PUBLISHED
               ↓                  ↓
           REJECTED           FLAGGED
```

## State Definitions

| State | Description | Editable | Confidence |
|-------|-------------|----------|-----------|
| EXTRACTED | AI-generated, not reviewed | Yes | < 0.7 |
| REVIEW_REQUIRED | Flagged for human review | No | 0.7–0.9 |
| VERIFIED | Human-reviewed and confirmed | Limited | 0.9+ |
| PUBLISHED | Public knowledge object | No | 0.95+ |
| REJECTED | AI extraction rejected | Yes | < 0.5 |
| FLAGGED | Contradiction or issue found | No | Varies |

## Transitions

| From | To | Trigger | Required Role | Side Effects |
|------|----|---------|---------------|-------------|
| EXTRACTED | REVIEW_REQUIRED | AI confidence > 0.7 | System | Notification to reviewers |
| EXTRACTED | VERIFIED | Auto-verify (confidence > 0.9) | System | Emit KnowledgeObjectCreated |
| EXTRACTED | REJECTED | AI confidence < 0.5 | System | Logged for retraining |
| REVIEW_REQUIRED | VERIFIED | Human review passes | Reviewer | Emit KnowledgeObjectCreated |
| REVIEW_REQUIRED | REJECTED | Human review fails | Reviewer | Logged |
| VERIFIED | PUBLISHED | Editorial approval | Editor | Emit KnowledgeObjectPublished |
| VERIFIED | FLAGGED | Contradiction detected | System/Reviewer | Emit ContradictionDetected |
| FLAGGED | VERIFIED | Contradiction resolved | Reviewer | Clear flag |
| FLAGGED | REJECTED | Unresolvable | Admin | Archive |
| PUBLISHED | FLAGGED | New contradiction found | System | Emit ContradictionDetected |

---

# 3. Article State Machine

## States
```
GENERATING → DRAFT → REVIEW → PUBLISHED → ARCHIVED
```

## State Definitions

| State | Description | Editable |
|-------|-------------|----------|
| GENERATING | AI is creating the article | No |
| DRAFT | Article generated, ready for editing | Yes |
| REVIEW | Under editorial review | No |
| PUBLISHED | Publicly available | No |
| ARCHIVED | Removed from publication | No |

## Transitions

| From | To | Trigger | Side Effects |
|------|----|---------|-------------|
| GENERATING | DRAFT | AI generation complete | Notification to editor |
| DRAFT | REVIEW | Editor submits | Emit ArticleSubmittedForReview |
| REVIEW | PUBLISHED | Review approved | Emit ArticlePublished |
| REVIEW | DRAFT | Review rejected | Return to editing |
| PUBLISHED | ARCHIVED | Archive action | Emit ArticleArchived |
| ARCHIVED | DRAFT | Restore | Revert |

---

# 4. Claim State Machine

## States
```
EXTRACTED → UNVERIFIED → VERIFIED → ACCEPTED
                 ↓           ↓
             DISPUTED    REJECTED
```

## State Definitions

| State | Description |
|-------|-------------|
| EXTRACTED | AI-identified claim |
| UNVERIFIED | Awaiting human review |
| VERIFIED | Confirmed by human reviewer |
| ACCEPTED | Integrated into knowledge base |
| DISPUTED | Contradicting evidence found |
| REJECTED | Determined to be false/inaccurate |

## Transitions

| From | To | Trigger | Side Effects |
|------|----|---------|-------------|
| EXTRACTED | UNVERIFIED | Automatic | Added to review queue |
| UNVERIFIED | VERIFIED | Human confirms | Update assertion confidence |
| UNVERIFIED | DISPUTED | Contradiction found | Emit ContradictionDetected |
| UNVERIFIED | REJECTED | Human rejects | Logged |
| VERIFIED | ACCEPTED | Editorial approval | Used in knowledge graph |
| VERIFIED | DISPUTED | New evidence contradicts | Downgrade status |
| DISPUTED | VERIFIED | Contradiction resolved | Re-elevate |
| DISPUTED | REJECTED | Contradiction confirmed | Final reject |

---

# 5. Source (Video) State Machine

## States
```
REGISTERED → CRAWLING → INGESTED → PROCESSING → COMPLETED → FAILED
```

## State Definitions

| State | Description |
|-------|-------------|
| REGISTERED | Channel/video added to system |
| CRAWLING | YT-DLP is downloading |
| INGESTED | Raw data stored in payload_versions |
| PROCESSING | Transcription/extraction running |
| COMPLETED | Full processing pipeline done |
| FAILED | Processing error, retryable |

## Transitions
| From | To | Trigger | Side Effects |
|------|----|---------|-------------|
| REGISTERED | CRAWLING | Ingestion job starts | Emit IngestionJobStarted |
| CRAWLING | INGESTED | Download complete | Emit VideoIngested |
| CRAWLING | FAILED | Download error | Retry up to 3 times |
| INGESTED | PROCESSING | Extraction job starts | Emit ExtractionJobStarted |
| PROCESSING | COMPLETED | All processing done | Emit SourceRegistered |
| PROCESSING | FAILED | Processing error | Retry with backoff |
| FAILED | CRAWLING | Retry | Increment retry count |
| FAILED | INGESTED | Manual recovery | Admin action |

---

# 6. AI Pipeline State Machine

## States
```
PENDING → RUNNING → COMPLETED → FAILED → CANCELLED
```

## State Definitions

| State | Description |
|-------|-------------|
| PENDING | Waiting for resources |
| RUNNING | Active processing |
| COMPLETED | Successfully finished |
| FAILED | Error occurred |
| CANCELLED | Manual cancellation |

## Transitions
| From | To | Trigger | Side Effects |
|------|----|---------|-------------|
| PENDING | RUNNING | Resources allocated | Update job status |
| RUNNING | COMPLETED | Processing done | Emit PipelineCompleted |
| RUNNING | FAILED | Error | Log error, notify |
| RUNNING | CANCELLED | Manual stop | Cleanup resources |
| PENDING | CANCELLED | Manual stop | Remove from queue |
| FAILED | PENDING | Retry | Increment attempt |
| FAILED | COMPLETED | Manual override | Admin action |

---

# 7. Workflow Review State Machine

## States
```
REQUESTED → IN_REVIEW → APPROVED → COMPLETED
                ↓
            REJECTED
```

## State Definitions

| State | Description |
|-------|-------------|
| REQUESTED | Review requested, awaiting assignment |
| IN_REVIEW | Reviewer actively working |
| APPROVED | Content approved |
| REJECTED | Content rejected with feedback |
| COMPLETED | Final state, all actions taken |

## Transitions
| From | To | Trigger | Required Role |
|------|----|---------|---------------|
| REQUESTED | IN_REVIEW | Reviewer assigned | Admin/System |
| IN_REVIEW | APPROVED | Approve action | Reviewer |
| IN_REVIEW | REJECTED | Reject action | Reviewer |
| IN_REVIEW | REQUESTED | Unassign | Admin |
| APPROVED | COMPLETED | Follow-up actions done | System |
| REJECTED | COMPLETED | Notify creator | System |

---

# Implementation

## State Machine Pattern

All state machines follow this interface:

```java
public interface StateMachine<S, T> {
    S getCurrentState();
    boolean canTransition(T trigger);
    S transition(T trigger, Map<String, Object> context);
    List<S> getValidTransitions();
}
```

## PostgreSQL State Storage

```sql
CREATE TABLE workflow.state_machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    current_state VARCHAR(100) NOT NULL,
    previous_state VARCHAR(100),
    metadata JSONB NOT NULL DEFAULT '{}',
    version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    CONSTRAINT uq_state_machine_entity 
        UNIQUE(entity_type, entity_id)
);

CREATE TABLE workflow.state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    from_state VARCHAR(100) NOT NULL,
    to_state VARCHAR(100) NOT NULL,
    trigger VARCHAR(100) NOT NULL,
    triggered_by UUID,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

# State Machine Summary

| Entity | States | Managed By | AI Involved |
|--------|--------|-----------|-------------|
| Story | 6 states | workflow-service | No |
| Knowledge Object | 6 states | knowledge-service | Yes |
| Article | 5 states | workflow-service | No |
| Claim | 6 states | knowledge-service | Yes |
| Source/Video | 6 states | content-service | Yes |
| AI Pipeline | 5 states | orchestration-service | Yes |
| Workflow Review | 5 states | workflow-service | No |

---

# References

- ADR-004: Event-Driven Architecture
- ADR-008: Provenance and Data Lineage
- BACKEND-PRD.md §3 Workflow Domain, §State Machine
- ddl.md - State Machine Tables