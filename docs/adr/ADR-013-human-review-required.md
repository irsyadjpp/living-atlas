# ADR-013: Human Review Required — AI Outputs Never Automatically Published

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture transforms unstructured cultural narratives into structured, verifiable, searchable knowledge. The AI Platform generates canonical stories, knowledge objects, claims, and articles from source transcripts. These AI-generated outputs form the foundation of the platform's knowledge base — they appear in knowledge graphs, search results, research exports, and published articles.

However, AI language models are known to hallucinate — to generate plausible-sounding but factually incorrect content. For a platform that preserves and structures cultural knowledge, hallucinations are not merely inconvenient — they are damaging. An invented entity, a fabricated claim, or a misattributed belief undermines the platform's trustworthiness with researchers, anthropologists, and cultural preservation bodies.

The platform serves researchers and anthropologists who depend on the accuracy and provenance of every knowledge artifact. A researcher citing a claim from the platform must be confident that the claim is grounded in source evidence, not invented by an AI.

The PRD explicitly states: "AI-generated outputs are never automatically published. Required review: Knowledge Objects, Claims, Articles." (Backend Platform PRD §3.6). The AI Platform PRD §3.7 reinforces: "AI generated outputs must not be automatically published. Review is required for: Claims, Knowledge Objects, Articles."

## Technical Context

The AI Platform produces outputs through a multi-stage pipeline:

1. **Canonical Story Extraction** — Transcript → structured canonical story JSON
2. **Knowledge Extraction** — Canonical story → entities, claims, themes, motifs, beliefs, rituals
3. **Knowledge Normalization** — Alias resolution, entity consolidation
4. **Knowledge Validation** — Confidence scoring, schema validation
5. **Article Generation** — Canonical story + knowledge → 4 article types

Each stage writes its output to PostgreSQL with a `REVIEW_REQUIRED` status. The state machines for Knowledge and Article entities have a `REVIEW_REQUIRED` state between extraction/generation and approval (Backend Platform PRD §9).

The workflow domain (workflow-service) manages review, approval, publishing, and moderation workflows. The RBAC model defines two review roles: Editor (reviews AI output, approves publication, merges knowledge) and Reviewer (validates claims, validates evidence, approves knowledge).

Projection workers (Neo4j graph, ADR-011; Weaviate vectors, ADR-012) only consume events for APPROVED or PUBLISHED content. REVIEW_REQUIRED content is never projected.

## Constraints

1. **No automatic publication**: AI-generated content must never transition to PUBLISHED status without human review. This is a hard architectural constraint.

2. **Review scope**: Three content types require review: Knowledge Objects, Claims, and Articles. Stories also require review (they pass through the workflow state machine: DRAFT → REVIEW → APPROVED → PUBLISHED).

3. **Review roles**: Two distinct reviewer roles — Editor (reviews AI output, approves publication, merges knowledge) and Reviewer (validates claims, validates evidence, approves knowledge). These roles have different permissions and review focuses.

4. **Provenance preservation**: Review actions (approve, reject, modify) must be recorded with reviewer identity, timestamp, and reason. All versions are preserved (immutable versioning, ADR-008).

5. **Projection gate**: Neo4j and Weaviate projections must never contain REVIEW_REQUIRED content. The projection gate is enforced at the event consumption level.

6. **Reprocessing on rejection**: When content is rejected, it must be reprocessable (typically with updated prompts or human corrections). The rejection creates a new version chain.

7. **Scalability**: At 100,000 stories and 1,000,000 knowledge objects, the review queue can grow large. The workflow must support prioritization, batching, and assignment.

8. **Audit trail**: Every review decision must be logged in the audit trail for compliance and research reproducibility.

## Problem Statement

AI-generated content (canonical stories, knowledge objects, claims, articles) must not be automatically published. Every AI output requires human review before it appears in the knowledge graph, search results, or published articles. The review process must support two reviewer roles (Editor and Reviewer), preserve provenance of review decisions, gate projections (Neo4j, Weaviate) from unreviewed content, and scale to 100,000+ stories and 1,000,000+ knowledge objects. How do we design a human review workflow that is architecturally enforced (not just a process), supports efficient review at scale, preserves complete audit trails, and integrates with the existing event-driven, state machine, and projection architectures?

# Decision

**AI-generated content is never automatically published. All AI outputs (canonical stories, knowledge objects, claims, and articles) are written to PostgreSQL in `REVIEW_REQUIRED` state. Human review is required to transition content to APPROVED status. Projection workers (Neo4j, Weaviate) only consume events for APPROVED or PUBLISHED content. Review decisions are logged with full audit trail. Rejected content can be reprocessed, creating new versions in the immutable version chain.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AI PLATFORM (Generates Content)                      │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │  Extraction   │───►│  Knowledge   │───►│  All outputs written     │  │
│  │  Service      │    │  Service     │    │  with status =           │  │
│  └──────────────┘    └──────────────┘    │  'REVIEW_REQUIRED'        │  │
│                                          └──────────────┬───────────┘  │
│  ┌──────────────┐    ┌──────────────┐                   │              │
│  │  Article     │───►│  Embedding   │                   │              │
│  │  Service     │    │  Service     │                   │              │
│  └──────────────┘    └──────────────┘                   │              │
└─────────────────────────────────────────────────────────┼──────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL (Source of Truth)                         │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  AI Output Tables (status = 'REVIEW_REQUIRED')                   │   │
│  │                                                                   │   │
│  │  ai_output_canonical_stories  │  status in ('REVIEW_REQUIRED',   │   │
│  │  ai_output_knowledge_objects  │      'APPROVED', 'REJECTED',     │   │
│  │  ai_output_claims             │      'PUBLISHED')                │   │
│  │  ai_output_articles           │                                   │   │
│  │                                                                   │   │
│  │  ┌───────────────────────────────────────────────────────────┐   │   │
│  │  │  Review Queue (workflow_review_tasks)                      │   │   │
│  │  │  Pending items across all content types,                   │   │   │
│  │  │  assignable to editors/reviewers,                          │   │   │
│  │  │  prioritizable by content type or tenant                   │   │   │
│  │  └───────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      WORKFLOW SERVICE (Review Management)                 │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Review Queue Manager                                           │   │
│  │  ─────────────────────                                          │   │
│  │  - Assigns review tasks to editors/reviewers                     │   │
│  │  - Supports priority queuing                                     │   │
│  │  - Tracks review SLA and escalations                             │   │
│  │  - Prevents duplicate assignments                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Review State Machine                                            │   │
│  │  ─────────────────────                                           │   │
│  │                                                                   │   │
│  │  REVIEW_REQUIRED ──→ IN_REVIEW ──→ APPROVED ──→ PUBLISHED        │   │
│  │       │                  │            │                           │   │
│  │       │                  ├──→ REJECTED│                           │   │
│  │       │                  │            │                           │   │
│  │       │                  └──→ FLAGGED │  (needs domain expert)    │   │
│  │       │                               │                           │   │
│  │       └────────────────────────────────┘                           │   │
│  │              (auto-reject if no review in SLA window)             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Approval Flow                                                   │   │
│  │  ──────────────                                                  │   │
│  │                                                                   │   │
│  │  1. Item enters REVIEW_REQUIRED state                             │   │
│  │  2. Workflow service detects new item (event or polling)          │   │
│  │  3. Review task created in queue                                  │   │
│  │  4. Editor/Reviewer assigned to task                              │   │
│  │  5. Reviewer reviews item through frontend UI                     │   │
│  │  6. Reviewer takes action:                                        │   │
│  │     a. Approve → status = APPROVED, event emitted                 │   │
│  │     b. Reject  → status = REJECTED, reason recorded               │   │
│  │     c. Flag    → status = FLAGGED, domain expert required         │   │
│  │  7. Projection workers consume APPROVED events                    │   │
│  │  8. Content becomes visible in graph and search                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EVENT EMISSION (On Review Decision)                  │
│                                                                          │
│  On APPROVAL → emits ReviewApproved event                                │
│  On REJECTION → emits ReviewRejected event                               │
│                                                                          │
│  ReviewApproved is consumed by:                                          │
│  - Graph Projection Worker (ADR-011) → projects to Neo4j                │
│  - Embedding Service (ADR-012) → generates vectors for Weaviate         │
│  - Content Service → updates story/article status to APPROVED           │
│                                                                          │
│  ReviewRejected is consumed by:                                          │
│  - AI Orchestration Service → triggers reprocessing with updated prompt │
│  - Content Service → records rejection reason for audit                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: All AI Outputs Start in REVIEW_REQUIRED State

Every AI-generated output is written to PostgreSQL with `status = 'REVIEW_REQUIRED'`. No AI output bypasses this state.

```python
# All AI workers write with REVIEW_REQUIRED status
async def process_extraction_job(job_id, transcript_id):
    # ... AI extraction logic ...
    
    # Write result — ALWAYS in REVIEW_REQUIRED state
    await db.execute("""
        INSERT INTO ai_output_canonical_stories 
            (id, job_id, transcript_id, story_data, confidence_score,
             prompt_version, provider, model, status, 
             tenant_id, workspace_id, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 
                'REVIEW_REQUIRED',  ← Always starts here
                $9, $10, NOW())
    """, story_id, job_id, transcript_id, json.dumps(result['story']),
         result['confidence'], prompt_version, result['provider'],
         result['model'], result['tenant_id'], result['workspace_id'])

# Exception: What is automatically published?
# - Embeddings themselves are not user-facing (they power search)
# - But the CONTENT that is embedded must be APPROVED
# - Normalization results (alias resolution) are SYSTEM-level, not AI-generated
# - Validation reports are internal, not published
```

**What requires review:**

| Content Type | AI-Generated? | Requires Human Review? | Rationale |
|-------------|---------------|----------------------|-----------|
| Canonical Story | Yes | Yes | Core knowledge artifact. Hallucinations directly affect knowledge graph. |
| Knowledge Objects | Yes | Yes | Entities, themes, motifs extracted by AI. Must be verified. |
| Claims | Yes | Yes | Evidence-grounded statements. Reviewer must validate evidence. |
| Articles (narrative, knowledge, news) | Yes | Yes | Published content visible to readers. Must be accurate. |
| Creative Articles | Yes | No* | Entertainment-only, not canonical. But still tagged as AI-generated. |
| Normalization results (aliases) | System | No | Deterministic rules, not AI-generated. |
| Embeddings | AI | No | Not user-facing. Power search ranking only. |
| Validation reports | System | No | Internal quality metrics, not published. |

*Creative articles are not canonical and not used by the graph. However, they are still tagged as AI-generated so readers know the source.

### Rule 2: Review State Machine

Each reviewable entity progresses through a state machine. Transitions are controlled by the workflow service.

```
                    ┌──────────────────┐
                    │  REVIEW_REQUIRED │
                    │  (initial state) │
                    └────────┬─────────┘
                             │
                     ┌───────┴───────┐
                     │               │
                     ▼               ▼
              ┌────────────┐  ┌──────────────┐
              │ IN REVIEW   │  │ AUTO-REJECTED│
              │ (assigned)  │  │ (SLA expired)│
              └──────┬─────┘  └──────────────┘
                     │
            ┌────────┼────────┐
            │        │        │
            ▼        ▼        ▼
       ┌────────┐ ┌────────┐ ┌────────┐
       │APPROVED│ │REJECTED│ │ FLAGGED│
       └────┬───┘ └────┬───┘ └────┬───┘
            │          │          │
            ▼          │          ▼
       ┌────────┐      │    ┌──────────┐
       │PUBLISHED│     │    │DOMAIN    │
       │        │      │    │REVIEW    │
       └────────┘      │    └────┬─────┘
                       │         │
                       │    ┌────┴────┐
                       │    │         │
                       │    ▼         ▼
                       │ ┌────────┐ ┌────────┐
                       │ │APPROVED│ │REJECTED│
                       │ └────┬───┘ └────────┘
                       │      │
                       │      ▼
                       │ ┌────────┐
                       └─►PUBLISHED│
                         └────────┘
```

| State | Description | Can Be Viewed? | Can Be Edited? |
|-------|-------------|----------------|----------------|
| `REVIEW_REQUIRED` | AI output, awaiting review assignment | Reviewer only | No (AI output is immutable) |
| `IN_REVIEW` | Assigned to a reviewer, being actively reviewed | Reviewer + Assignee | Reviewer can edit metadata |
| `APPROVED` | Human review passed, awaiting publication | All authorized users | No (immutable version) |
| `PUBLISHED` | Content is live and visible | All authorized users | No (creates new version) |
| `REJECTED` | Human review failed, not accepted | Reviewer + Admin | No (must reprocess) |
| `FLAGGED` | Requires domain expert review | Admin + Domain Expert | No (awaiting expert) |
| `AUTO-REJECTED` | SLA expired without review | Admin only | No (must reprocess) |

**Transition rules:**

| From | To | Trigger | Required Role |
|------|----|---------|---------------|
| REVIEW_REQUIRED | IN_REVIEW | Assign reviewer | Workflow Manager or Admin |
| IN_REVIEW | APPROVED | Approve content | Editor or Reviewer |
| IN_REVIEW | REJECTED | Reject content with reason | Editor or Reviewer |
| IN_REVIEW | FLAGGED | Flag for domain expert | Editor or Reviewer |
| FLAGGED | APPROVED | Domain expert approves | Domain Expert |
| FLAGGED | REJECTED | Domain expert rejects | Domain Expert |
| APPROVED | PUBLISHED | Publish content | Editor or Admin |
| REVIEW_REQUIRED | AUTO-REJECTED | SLA timer expires (72 hours) | System |

### Rule 3: Dual Review Tracks — Editor and Reviewer

Two distinct review roles with different focus areas:

**Editor** — Reviews AI output quality, coherence, and completeness:
- Reviews canonical stories for narrative quality
- Reviews articles for readability and factual alignment with source
- Approves publication of stories and articles
- Can merge knowledge objects
- Focus: Is the AI output well-formed, useful, and publishable?

**Reviewer** — Validates factual accuracy and evidence:
- Validates claims against source evidence
- Validates knowledge objects for cultural accuracy
- Approves knowledge for inclusion in the knowledge graph
- Focus: Is every claim supported by evidence? Is the cultural context accurate?

```sql
-- Review task assignment
CREATE TABLE workflow_review_tasks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Content to review
    content_type        VARCHAR(50) NOT NULL,  -- 'canonical_story', 'knowledge_object', 'claim', 'article'
    content_id          UUID NOT NULL,
    content_version     BIGINT NOT NULL,
    
    -- Review tracking
    status              VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    -- 'PENDING' → 'ASSIGNED' → 'IN_REVIEW' → 'COMPLETED' or 'REJECTED'
    
    -- Assignment
    assigned_to         UUID REFERENCES identity_users(id),
    assigned_by         UUID REFERENCES identity_users(id),
    assigned_at         TIMESTAMPTZ,
    
    -- Review type determines who can be assigned
    review_type         VARCHAR(50) NOT NULL,
    -- 'editorial_review'  → requires EDITOR role
    -- 'factual_review'    → requires REVIEWER role
    -- 'domain_expert'     → requires DOMAIN_EXPERT role
    
    -- SLA
    sla_deadline        TIMESTAMPTZ NOT NULL,
    priority            VARCHAR(20) NOT NULL DEFAULT 'normal',
    -- 'low', 'normal', 'high', 'critical'
    
    -- Outcome
    decision            VARCHAR(50),  -- 'approved', 'rejected', 'flagged'
    decision_reason     TEXT,
    reviewed_at         TIMESTAMPTZ,
    
    -- Escalation
    escalated_to        UUID REFERENCES identity_users(id),
    escalation_reason   TEXT,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_content_review UNIQUE(content_type, content_id, review_type)
);
```

**Assignment logic**:
- Canonical stories → assigned to Editor (editorial review)
- Knowledge objects and claims → assigned to Reviewer (factual review)
- Articles → assigned to Editor (editorial review)
- Domain expert flag → assigned to Domain Expert (cultural accuracy review)

### Rule 4: Review Queue Management

The review queue must handle high volume efficiently. Items are prioritized and batched.

```python
class ReviewQueueManager:
    """Manages the review queue for AI-generated content."""
    
    PRIORITY_WEIGHTS = {
        "critical": 100,   # Time-sensitive content (news articles)
        "high": 50,        # High-profile content
        "normal": 10,      # Standard content
        "low": 1,          # Low-priority content (batch processing)
    }
    
    async def get_next_task(
        self, reviewer_id: UUID, review_type: str
    ) -> Optional[ReviewTask]:
        """Get the highest-priority task for a reviewer."""
        reviewer = await self._get_reviewer_with_skills(reviewer_id)
        
        # Find tasks matching the reviewer's skills and type
        task = await db.fetch_one("""
            SELECT * FROM workflow_review_tasks
            WHERE status = 'PENDING'
              AND review_type = $1
              AND assigned_to IS NULL
            ORDER BY 
                CASE priority
                    WHEN 'critical' THEN 100
                    WHEN 'high' THEN 50
                    WHEN 'normal' THEN 10
                    ELSE 1
                END DESC,
                created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """, review_type)
        
        if task:
            # Assign to reviewer
            await db.execute("""
                UPDATE workflow_review_tasks
                SET status = 'ASSIGNED',
                    assigned_to = $1,
                    assigned_at = NOW()
                WHERE id = $2
            """, reviewer_id, task['id'])
            
            # Update content status
            await self._update_content_status(
                task['content_type'], task['content_id'], 'IN_REVIEW'
            )
        
        return task
    
    async def get_queue_depth(self, content_type: Optional[str] = None) -> dict:
        """Get queue statistics."""
        if content_type:
            result = await db.fetch_one("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'PENDING') AS pending,
                    COUNT(*) FILTER (WHERE status = 'ASSIGNED') AS in_review,
                    COUNT(*) FILTER (WHERE priority = 'critical') AS critical,
                    MIN(created_at) FILTER (WHERE status = 'PENDING') AS oldest_pending
                FROM workflow_review_tasks
                WHERE content_type = $1
            """, content_type)
        else:
            result = await db.fetch_one("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'PENDING') AS pending,
                    COUNT(*) FILTER (WHERE status = 'ASSIGNED') AS in_review,
                    COUNT(*) FILTER (WHERE priority = 'critical') AS critical,
                    MIN(created_at) FILTER (WHERE status = 'PENDING') AS oldest_pending
                FROM workflow_review_tasks
            """)
        
        return dict(result)
```

### Rule 5: Review UI Must Render Structured Content

The review UI must present AI-generated content in a human-readable format. Raw JSON is not acceptable for reviewers.

```json
// Review UI rendering (frontend):
// Canonical Story Review Screen:
// ┌─────────────────────────────────────────────┐
// │  Review: Canonical Story #42                 │
// │  Source: "Misteri Kuntilanak" podcast        │
// │                                              │
// │  Story Title: Penampakan Kuntilanak...       │
// │  Summary: Pak Sariman recounts...            │
// │  Narrative Type: First-person               │
// │  Language: Indonesian (id)                   │
// │  Cultural Context: Jawa Timur, Jawa, Kejawen│
// │                                              │
// │  ┌── Entities ───────────────────────────┐   │
// │  │  Kuntilanak (spirit) — Confidence: 95  │   │
// │  │    Evidence: segment 2, line 46-52     │   │
// │  │  Pak Sariman (person) — Confidence: 98 │   │
// │  │    Evidence: segment 0, line 0-3       │   │
// │  └────────────────────────────────────────┘   │
// │                                              │
// │  ┌── Claims ─────────────────────────────┐   │
// │  │  ☐ "Kuntilanak appeared at... 2019"   │   │
// │  │    Evidence matches transcript ✓       │   │
// │  │  ☐ "Entity has long black hair..."    │   │
// │  │    Evidence matches transcript ✓       │   │
// │  └────────────────────────────────────────┘   │
// │                                              │
// │  [Approve]  [Reject]  [Flag for Expert]      │
// └─────────────────────────────────────────────┘
```

**Review UI requirements**:
- Renders structured AI output (Canonical Story) as a readable form, not raw JSON
- Shows source evidence alongside each entity, claim, and belief
- Provides checkbox or toggle for confirming each AI-extracted item
- Includes a reason field for rejection and flagging
- Shows provenance chain: Source → Transcript → AI Extraction → Current Version
- Displays confidence scores and highlights low-confidence items
- Shows the exact prompt version used for the extraction

### Rule 6: Rejection and Reprocessing Flow

When content is rejected, it can be reprocessed. Reprocessing creates a new AI output and a new version in the immutable version chain.

```python
async def handle_review_rejected(event):
    """Handle content rejection — trigger reprocessing if applicable."""
    content_type = event.data['contentType']
    content_id = event.data['contentId']
    reason = event.data['reason']
    
    # Record rejection
    await db.execute("""
        UPDATE ai_output_canonical_stories
        SET status = 'REJECTED',
            reviewed_by = $1,
            reviewed_at = NOW(),
            review_notes = $2
        WHERE id = $3
    """, event.data['reviewedBy'], reason, content_id)
    
    # Check if auto-reprocess is configured
    should_reprocess = await self._should_reprocess(content_type, content_id, reason)
    
    if should_reprocess:
        # Trigger reprocessing with updated prompt if available
        reprocess_event = {
            "contentType": content_type,
            "originalContentId": content_id,
            "rejectionReason": reason,
            "promptVersion": event.data.get('suggestedPromptVersion'),
            "tenantId": event.metadata['tenantId'],
        }
        
        await redpanda.produce(
            topic="ai.internal",
            key=f"reprocess:{content_type}:{content_id}",
            value=reprocess_event
        )
        
        logger.info(f"Reprocessing triggered for {content_type} {content_id}: {reason}")
    else:
        logger.info(f"Content {content_type} {content_id} rejected and not reprocessed: {reason}")
```

**Reprocess decision logic**:

| Rejection Reason | Auto-Reprocess? | Action |
|-----------------|-----------------|--------|
| Hallucination (invented entity) | Yes | Reprocess with stricter prompt. Add to golden dataset as negative example. |
| Missing entity | Yes | Reprocess with updated prompt. Add to golden dataset. |
| Cultural inaccuracy | No | Flag for domain expert. Update prompt with cultural context. |
| Low quality | Yes | Reprocess with different provider/model (higher temperature or better model). |
| Schema non-compliance | Yes | Fix prompt output schema. Reprocess. |
| Irreparable | No | Requires human authoring. Not suitable for AI generation. |

### Rule 7: Projection Gate — Unreviewed Content Never Projected

The projection gate is the architectural mechanism that prevents unverified AI outputs from appearing in the knowledge graph or search results. It is enforced at the event consumption level.

```python
# Graph Projection Worker (ADR-011) — only consumes APPROVED/PUBLISHED events:
# - Consumes: StoryPublished (not StoryCreated)
# - Consumes: ReviewApproved (not ReviewRequested)
# - Consumes: KnowledgeValidated (not KnowledgeExtracted)

# Embedding Service (ADR-012) — only consumes APPROVED/PUBLISHED events:
# - Consumes: StoryPublished (not StoryCreated)
# - Consumes: ArticlePublished (not ArticleGenerated)
# - Consumes: KnowledgeValidated (not KnowledgeExtracted)
# - Consumes: ReviewApproved (not ReviewRequested)

# Enforcement at the worker level:
async def handle_event(self, event):
    """Process event only if the content is APPROVED or PUBLISHED."""
    content_id = event.data.get('contentId') or event.data.get('storyId')
    content = await self._fetch_content(content_id)
    
    if content['status'] not in ('APPROVED', 'PUBLISHED'):
        logger.warning(
            f"Skipping projection for {content_id}: status is {content['status']}. "
            f"Only APPROVED or PUBLISHED content is projected."
        )
        return  # Silently skip — no error, no DLQ
    
    # Proceed with projection/embedding
    await self._project_content(content)
```

**Three layers of enforcement**:

1. **Event subscription level**: Workers only subscribe to topics that indicate approved content (`content.evt:StoryPublished`, `workflow.evt:ReviewApproved`)
2. **Event handler level**: Workers verify content status before processing, even for expected event types
3. **Database level**: RLS policies on projection state tables ensure only approved content is tracked

### Rule 8: Reviewer Assignment and Workload Management

Review tasks must be assigned efficiently to prevent bottlenecks.

```python
class ReviewerAssignmentStrategy:
    """Strategies for assigning review tasks to reviewers."""
    
    async def assign_task(self, task: ReviewTask) -> UUID:
        """Assign a review task to the most appropriate reviewer."""
        
        if task.review_type == 'domain_expert':
            return await self._assign_to_domain_expert(task)
        
        # Get available reviewers for this task type
        available = await self._get_available_reviewers(task.review_type)
        
        # Strategy: least-loaded reviewer with relevant experience
        best_reviewer = min(
            available,
            key=lambda r: (
                r['current_workload'],           # Fewest pending tasks
                -r['content_type_experience'],    # Most experience with this content type
                r['last_assignment_age']          # Longest time since last assignment
            )
        )
        
        return best_reviewer['id']
    
    async def _get_available_reviewers(self, review_type: str) -> list:
        """Get reviewers with capacity for new tasks."""
        return await db.fetch_all("""
            SELECT 
                u.id,
                COUNT(rt.id) FILTER (
                    WHERE rt.status IN ('ASSIGNED', 'IN_REVIEW')
                ) AS current_workload,
                COUNT(rt.id) FILTER (
                    WHERE rt.status = 'COMPLETED'
                      AND rt.content_type IN ('canonical_story', 'knowledge_object')
                ) AS content_type_experience,
                MAX(rt.assigned_at) AS last_assignment_age
            FROM identity_users u
            JOIN identity_user_roles ur ON u.id = ur.user_id
            LEFT JOIN workflow_review_tasks rt ON u.id = rt.assigned_to
            WHERE ur.role_code IN ('EDITOR', 'REVIEWER')
              AND u.is_active = true
            GROUP BY u.id
            HAVING COUNT(rt.id) FILTER (
                WHERE rt.status IN ('ASSIGNED', 'IN_REVIEW')
            ) < 20  -- Max concurrent tasks per reviewer
            ORDER BY current_workload ASC
        """)
```

**Workload limits**:

| Role | Max Concurrent Tasks | SLA Target |
|------|---------------------|------------|
| Editor | 20 | 24 hours |
| Reviewer | 20 | 24 hours |
| Domain Expert | 5 | 72 hours |

### Rule 9: Review SLA and Escalation

Review tasks have SLAs. When an SLA is breached, the task is escalated.

```python
async def check_sla_compliance():
    """Check for SLA breaches and escalate if needed."""
    breached = await db.fetch_all("""
        SELECT * FROM workflow_review_tasks
        WHERE status IN ('PENDING', 'ASSIGNED')
          AND sla_deadline < NOW()
          AND escalated_to IS NULL
        ORDER BY sla_deadline ASC
    """)
    
    for task in breached:
        # Find the next-level reviewer
        escalation_target = await self._find_escalation_target(task)
        
        await db.execute("""
            UPDATE workflow_review_tasks
            SET escalated_to = $1,
                escalation_reason = 'SLA breached: task pending since ' || created_at::text
            WHERE id = $2
        """, escalation_target, task['id'])
        
        # Notify escalation target
        await notification_service.send(
            user_id=escalation_target,
            title=f"SLA Breach: {task['content_type']} review overdue",
            body=f"A review task for {task['content_type']} {task['content_id']} "
                 f"has exceeded its SLA deadline.",
            priority='high'
        )
```

**SLA targets by priority**:

| Priority | Editorial Review | Factual Review | Domain Expert Review |
|----------|-----------------|----------------|---------------------|
| Critical | 4 hours | 8 hours | 24 hours |
| High | 8 hours | 24 hours | 48 hours |
| Normal | 24 hours | 48 hours | 72 hours |
| Low | 72 hours | 1 week | 2 weeks |

### Rule 10: Audit Trail for Every Review Decision

Every review decision is logged for compliance and research reproducibility.

```sql
CREATE TABLE workflow_review_audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Content identification
    content_type        VARCHAR(50) NOT NULL,
    content_id          UUID NOT NULL,
    content_version     BIGINT NOT NULL,
    
    -- Review action
    action              VARCHAR(50) NOT NULL,
    -- 'assigned', 'approved', 'rejected', 'flagged',
    -- 'domain_expert_assigned', 'domain_expert_approved',
    -- 'domain_expert_rejected', 'escalated', 'auto_rejected'
    
    -- Actor
    actor_id            UUID NOT NULL,
    actor_role          VARCHAR(50) NOT NULL,
    
    -- Decision details
    from_status         VARCHAR(50) NOT NULL,
    to_status           VARCHAR(50) NOT NULL,
    reason              TEXT,
    
    -- Evidence of review (viewed transcript, checked evidence, etc.)
    review_metadata     JSONB,
    -- {
    --   "viewedTranscript": true,
    --   "checkedEvidence": true,
    --   "evidenceItemsChecked": 3,
    --   "durationSeconds": 245,
    --   "clientIp": "..."
    -- }
    
    -- Timing
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_review_audit_content 
    ON workflow_review_audit_log(content_type, content_id, content_version);
CREATE INDEX idx_review_audit_actor 
    ON workflow_review_audit_log(actor_id, created_at DESC);
CREATE INDEX idx_review_audit_timing 
    ON workflow_review_audit_log(created_at DESC);
```

# Alternatives Considered

## Alternative 1: Fully Automatic Publication (No Human Review)

**Description**: AI-generated content is automatically published without human review. The AI Platform's validation service provides automated quality checks, and these are considered sufficient for publication.

**Advantages**:
- Zero review latency — content is available immediately after AI generation
- No reviewer staffing costs
- No review queue backlog
- Simpler architecture — no workflow service, no review state machine
- Higher throughput — no human bottleneck

**Disadvantages**:
- **Hallucinations reach users**: AI-invented entities, claims, and cultural inaccuracies appear in the knowledge graph and search results. Users cannot distinguish AI-generated content from verified content.
- **No accountability**: When a hallucination is discovered, there is no review record showing who should have caught it.
- **Researcher trust destroyed**: Researchers and anthropologists cannot trust the platform if they cannot be confident that content is verified.
- **Cultural damage**: An AI-invented belief or ritual attributed to a real Indonesian community could cause real cultural harm.
- **Violates the PRD**: The PRD explicitly requires human review (§3.6). This alternative violates a core architecture principle.
- **No domain expert validation**: AI may misrepresent cultural nuances that only a human domain expert would catch.

**Rejection rationale**: Automatic publication violates the core "Human Review Required" principle, destroys researcher trust, and risks cultural harm from AI hallucinations. The review latency is a necessary cost for a platform that claims to be a trusted source of cultural knowledge.

## Alternative 2: Automated Validation Gates Only (No Human Review)

**Description**: Replace human review with an automated multi-stage validation pipeline: schema validation, evidence cross-checking, contradiction detection, confidence threshold gating. Content that passes all automated gates is automatically published.

**Advantages**:
- Fast — validation is seconds to minutes, not hours to days
- Consistent — automated checks are applied uniformly
- Scalable — no human bottleneck, validation pipeline can be scaled horizontally
- Lower operational cost — no reviewer staffing
- Combined with confidence scoring, provides a quality signal

**Disadvantages**:
- **Automated validation cannot detect subtle hallucinations**: An AI-invented entity that looks structurally valid (has a name, type, confidence score, and evidence reference) will pass schema validation even if the entity is completely fabricated.
- **Evidence cross-checking is limited**: Automated checks can verify that evidence references point to real transcript segments, but cannot verify that the evidence actually supports the claim.
- **Cultural nuance is not machine-detectable**: An AI may describe a ritual in a way that is technically correct but culturally insensitive or inaccurate. Only a domain expert would catch this.
- **Confidence thresholds are misleading**: A high-confidence hallucination is still a hallucination. Confidence scores reflect the AI's internal certainty, not factual accuracy.
- **No accountability for edge cases**: Automated validation gates inevitably have false positives and false negatives. Without human review, there is no mechanism to catch edge cases.
- **PRD violation**: The PRD explicitly requires human review. Automated validation is a complement to human review, not a replacement.

**Rejection rationale**: Automated validation is essential (the platform has a validation service), but it is not sufficient. The combination of automated validation + human review provides the best quality assurance. Automated gates catch structural issues; human review catches semantic, cultural, and factual issues. Removing human review would eliminate the safety net for the most dangerous AI failure mode: plausible-sounding but factually incorrect cultural content.

## Alternative 3: Post-Publication Review (Publish Then Review)

**Description**: Publish AI-generated content immediately, but tag it as "AI-generated — not yet reviewed." Users can see the content, but it is clearly marked as unverified. Reviewers then review the content at their own pace. If content is later rejected, it is removed or flagged.

**Advantages**:
- Content is immediately available for readers
- Review backlog does not block content availability
- Users can make their own trust decisions (some may accept AI-generated content)
- Researchers can still access raw material even if not yet reviewed
- Reviewer workload is less urgent — no publication dependency

**Disadvantages**:
- **Unreviewed AI content in the knowledge graph**: The projection gate exists precisely to prevent this. If unreviewed content is projected to Neo4j, it becomes part of the knowledge graph, connected to verified content. Users cannot distinguish verified from unverified relationships.
- **Trust erosion**: Users who encounter AI hallucinations in the knowledge graph will lose trust in the platform, even if the content is tagged as "unreviewed." The tag is an excuse, not a solution.
- **Research integrity compromised**: A researcher who unknowingly cites an AI hallucination is responsible for the error, regardless of the "unreviewed" tag.
- **Graph contamination**: Once an AI hallucination is projected to Neo4j (even temporarily), it creates relationships with verified content. Removing it later requires graph cleanup — DETACH DELETE on contaminated nodes.
- **Search quality degraded**: Unreviewed content in Weaviate affects search rankings. A hallucinated entity may rank higher than real entities due to embedding similarity.
- **Reversal complexity**: If content is rejected after publication, it must be removed from Neo4j, Weaviate, and all caches. This is more complex than never projecting it in the first place.

**Rejection rationale**: Post-publication review is appropriate for platforms where content is subjective or low-stakes (social media comments, product reviews). For a cultural knowledge platform where accuracy is paramount and the knowledge graph interconnects verified and unverified data, pre-publication review is essential. The projection gate makes the architecture "review-first" by design.

## Alternative 4: Confidence-Based Auto-Approval with Sampling

**Description**: AI outputs with confidence scores above a high threshold (e.g., > 0.95) are automatically approved. Lower-confidence outputs require human review. A statistical sampling of auto-approved outputs is reviewed periodically to validate the threshold.

**Advantages**:
- Reduces review workload for high-confidence outputs
- Review queue focuses on borderline or low-confidence content
- Sampling provides ongoing validation of the confidence threshold
- Can be tuned over time as AI quality improves
- Some platforms use this pattern successfully (e.g., content moderation)

**Disadvantages**:
- **Confidence scores are not reliable indicators of factual accuracy**: AI models are poorly calibrated — a model may assign 0.95 confidence to a hallucinated entity. Confidence reflects the model's internal certainty, not ground truth.
- **No cultural accuracy signal**: Confidence scores do not reflect cultural nuance, sensitivity, or accuracy. A 0.99 confidence extraction may still be culturally inappropriate.
- **Threshold gaming**: If AI providers know that high-confidence outputs bypass review, they may become overconfident (assigning high confidence to everything).
- **Audit/compliance risk**: Auto-approved content that turns out to be hallucinated creates a compliance issue — "why was this not reviewed?"
- **False sense of security**: Auto-approval with sampling creates a false sense that high-confidence = accurate. When a hallucination slips through, the response is "but it had 0.95 confidence" rather than "we should have reviewed this."
- **Complex to implement correctly**: Determining the right threshold, managing the sampling rate, and handling confidence drift require ongoing ML engineering effort.

**Rejection rationale**: Confidence-based auto-approval is not appropriate for a cultural knowledge platform where accuracy is paramount. AI confidence scores are not reliable indicators of factual or cultural accuracy. The cost of a hallucination slipping through auto-approval (damaged researcher trust, cultural harm, graph contamination) far outweighs the benefit of reduced review workload. Human review is required for 100% of AI-generated outputs.

# Consequences

## Positive

1. **Researcher trust**: Every published knowledge artifact has been reviewed by a human. Researchers and anthropologists can trust that published content is accurate and evidence-grounded.

2. **Hallucination containment**: AI hallucinations are caught before they reach the knowledge graph, search results, or published articles. The review gate is the last line of defense against AI errors.

3. **Cultural accuracy**: Domain experts review content for cultural sensitivity and accuracy. An AI that describes a ritual incorrectly will be caught by a reviewer who understands the culture.

4. **Complete audit trail**: Every review decision is logged with reviewer identity, timestamp, reason, and evidence of review. This provides accountability and supports research reproducibility.

5. **Projection gate ensures architectural enforcement**: The projection gate is not a process or policy — it is hard-coded into the projection workers. Unreviewed content cannot appear in Neo4j or Weaviate because the workers do not consume events for it.

6. **SLA management prevents review bottlenecks**: SLAs and escalation ensure that content does not languish in the review queue indefinitely. Priority levels allow time-sensitive content (news articles) to be fast-tracked.

7. **Dual review tracks provide complementary expertise**: Editors review narrative quality and completeness. Reviewers validate factual accuracy. Domain experts validate cultural nuance. Each track catches different types of errors.

8. **Reprocessing on rejection enables iterative improvement**: Rejected content can be reprocessed with updated prompts, creating a feedback loop that improves AI quality over time.

## Negative

1. **Review latency**: Content is not available until reviewed. For high-priority content with a 4-hour SLA, this means a minimum 4-hour delay between AI generation and publication.

2. **Reviewer staffing cost**: Reviewers (Editors, Reviewers, Domain Experts) must be staffed and trained. This is a significant operational cost, especially for domain experts who are scarce.

3. **Review queue backlog**: At 100,000 stories and 1,000,000 knowledge objects, the review queue can grow large. Even with efficient assignment, backlog management is an ongoing challenge.

4. **Reviewer bias**: Different reviewers may apply different standards. One reviewer may approve content that another would reject. Consistent review guidelines and calibration are essential.

5. **Reprocessing cost**: Rejected content that is reprocessed consumes additional AI provider costs. Each rejection and reprocess cycle doubles the AI cost for that content.

6. **False positives in automated gates trigger unnecessary review**: If automated validation gates flag content that is actually correct, reviewers waste time on false positives. Tuning validation gates to minimize false positives is an ongoing effort.

7. **No auto-approval for content from trusted sources**: Human review is required for all AI-generated content, regardless of source quality or AI confidence. There is no mechanism to bypass review for content from "trusted" pipelines.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Content accuracy** | Every artifact is human-verified | Review latency (hours to days) |
| **Hallucination control** | AI errors caught before publication | Reviewer staffing cost |
| **Cultural sensitivity** | Domain expert validation | Domain expert scarcity |
| **Accountability** | Complete audit trail for every decision | Audit log storage growth |
| **Scalability** | Clear SLA and escalation process | Review queue backlog management |
| **AI improvement** | Rejection provides feedback loop | Reprocessing doubles AI costs |
| **Researcher trust** | High confidence in published content | Content is not available immediately |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Review queue grows faster than reviewers can process** | Medium | High — content publication stalls | Auto-scale reviewer assignments. Implement priority queuing. Use batch review for low-priority content. Alert on queue depth > 1000. |
| **SLA consistently breached** | Medium | Medium — content delayed | Add more reviewers. Adjust SLA targets. Implement auto-escalation. Reduce content generation rate. |
| **Reviewer makes incorrect approval** | Medium | High — hallucination published despite review | Dual review for high-risk content (Editor + Reviewer both approve). Automated validation as safety net. Post-publication monitoring. |
| **Domain expert unavailable** | Medium | Medium — culturally sensitive content stuck | Train backup domain experts. Document cultural review checklist. Implement temporary hold with SLA for expert review. |
| **Reprocessing loop: content repeatedly rejected** | Low | Medium — infinite reprocess cycle | Limit reprocessing to 3 attempts. After 3 rejections, require human authoring. Log repeated rejections for prompt improvement. |
| **Review UI does not render complex content correctly** | Medium | Medium — reviewer cannot assess content effectively | Test review UI with representative content samples. Support side-by-side comparison (AI output vs transcript). Provide evidence highlighting. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Reviewer availability during holidays/weekends** | High | High — review queue grows | Schedule reviewer shifts. Implement auto-approve for low-priority content during low coverage periods. Alert on queue depth. |
| **Review guidelines not followed consistently** | Medium | Medium — inconsistent review quality | Document and train on review guidelines. Calibrate reviewers regularly. Sample reviewed content for quality assurance. |
| **False rejection of culturally nuanced content** | Medium | Medium — content incorrectly rejected | Domain expert review for culturally sensitive content. Appeal process for rejected content. |
| **Review audit log storage growth** | Low | Low — increased storage cost | Archive audit logs after 90 days. Implement log retention policy. Sampling for low-priority items. |
| **Reprocessing consumes unexpected AI budget** | Medium | Medium — AI cost overrun | Set reprocessing budget per content type. Alert on reprocessing rate > 10%. Limit reprocessing attempts. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **AI quality improves to near-human level** | Human review may become unnecessary for some content types | Re-evaluate review requirements per content type. Consider reduced sampling for specific types. Keep human review for culturally sensitive content. |
| **Regulatory requirement for AI-generated content labeling** | Must clearly label AI-generated content in UI | Already tracked via provenance. Extend UI to show "AI-generated — reviewed by [name]" for every artifact. |
| **Reviewer fatigue leads to reduced quality** | Review quality degrades over time | Limit daily review tasks per reviewer. Implement review quality metrics. Rotate reviewers between types. |
| **Content volume exceeds reviewer capacity by 10x** | Fundamental scaling challenge | Implement triage: automated validation gates + human review for borderline cases only. This is a significant architectural change — requires ADR revision. |
| **Community-sourced reviews** | External experts contribute reviews | Implement reviewer credentialing. Separate track for community reviewers with limited scope. Maintain domain expert track for high-sensitivity content. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **AI quality demonstrably exceeds human accuracy for specific tasks**: If rigorous evaluation shows that AI-generated content for a specific type (e.g., entity extraction from well-structured transcripts) is consistently more accurate than human reviewers, consider reduced review requirements for that type. This requires a formal evaluation framework and ongoing monitoring.

2. **Review volume exceeds reviewer capacity by 10x**: At 1M+ knowledge objects annually, the review queue may need automated triage. Consider a three-tier system: (1) automated validation only → auto-approve, (2) automated validation + sampling review, (3) full human review for high-sensitivity content.

3. **Community-sourced review program established**: If the platform engages community experts (e.g., Indonesian folklore researchers, cultural preservation organizations) to contribute reviews, the review workflow must support credentialing, scope limitation, and quality monitoring.

4. **Regulatory requirements for AI content labeling**: If regulations require explicit labeling of AI-generated content, the review workflow must track and display "AI-generated, human-reviewed" status for every artifact.

5. **Review quality metrics and feedback loop established**: If the platform implements systematic review quality measurement (e.g., sampling approved content for post-publication review), the review workflow can be optimized based on quality data.

# References

- **Backend Platform PRD §3.6** — "Human Review Required" — AI-generated outputs are never automatically published.
- **Backend Platform PRD §5** — "User Types" — Editor and Reviewer roles and capabilities.
- **Backend Platform PRD §9** — "State Machines" — Knowledge: EXTRACTED → REVIEW_REQUIRED → VERIFIED → PUBLISHED. Article: DRAFT → REVIEW → APPROVED → PUBLISHED.
- **AI Platform PRD §3.7** — "Human Review Required" — Claims, Knowledge Objects, Articles require review.
- **AI Platform PRD §19** — "Human Review Workflow" — AI Output → Review Required → Approved or Rejected → Reprocess if Rejected.
- **ADR-004: Queue-Driven AI Platform** — AI workers write REVIEW_REQUIRED results to PostgreSQL.
- **ADR-006: ABAC Authorization Model** — Editor and Reviewer roles with specific permissions.
- **ADR-008: Immutable Versioning** — Review decisions create new versions in the version chain.
- **ADR-011: Knowledge Graph Projection** — Only projects APPROVED/PUBLISHED content (projection gate).
- **ADR-012: Vector Search Architecture** — Only embeds APPROVED/PUBLISHED content (projection gate).
- **NIST AI Risk Management Framework** — https://www.nist.gov/itl/ai-risk-management-framework — Human oversight of AI outputs.
- **EU AI Act** — https://artificialintelligenceact.eu/ — Human review requirements for high-risk AI systems (relevant for cultural knowledge platforms).