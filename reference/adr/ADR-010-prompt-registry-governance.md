# ADR-010: Prompt Registry and Governance — Prompts as Managed Assets

# Status

Accepted

# Context

## Business Context

Prompts are the single most important strategic asset in the AI Platform. A prompt defines how the AI interprets transcripts, extracts cultural knowledge, normalizes entities, validates quality, and generates articles. The difference between a well-crafted prompt and a poorly-crafted one can change extraction accuracy by 20–40%, hallucination rate by 5–15%, execution cost by 2–10x, and downstream article quality by 30–50%.

The platform has 15+ distinct prompt categories across 5 AI services (extraction, normalization, validation, article generation, embedding enrichment). Each prompt evolves independently as extraction quality improves, new entity types are discovered, and article formats are refined.

Without governance, the following failure modes occur:

1. **Reproducibility failure**: AI extractions change without notice. A story extracted on Monday with prompt version A produces different results than the same story extracted on Friday with prompt version B. Researchers cannot reproduce results.

2. **Quality regression**: A prompt "improvement" that degrades extraction quality goes undetected because no regression testing exists.

3. **Cost explosion**: A prompt change that increases token usage by 5x (e.g., adding "provide full context for every entity" without realizing it doubles output tokens) silently increases operational costs.

4. **Audit failure**: Cannot determine which prompt version produced a given knowledge artifact. When a downstream consumer finds an error, there is no way to trace it back to the prompt that caused it.

5. **Rollback impossibility**: A prompt change causes quality degradation, but there is no versioning — the team cannot revert to a known-good prompt.

## Technical Context

The AI Platform PRD §15 states: "Prompts are managed assets. Required Components: Prompt Registry, Prompt Versioning, Prompt Approval Workflow, Prompt Rollback, Prompt Audit Trail. Prompts must never be hardcoded."

The existing `docs/ai-platform/prompt-registry-governance-specification.md` defines a comprehensive prompt governance framework including:

- 15 prompt categories (story_canonicalization, theme_extraction, entity_extraction, claim_extraction, motif_extraction, relationship_extraction, archetype_extraction, story_boundary, knowledge_normalization, knowledge_validation, narrative_article, knowledge_article, news_article, creative_article, embedding_enrichment)
- PostgreSQL schema (`ai.prompt_versions`) with full metadata (version, content hash, status, owner, author, reviewer, change reason)
- Lifecycle state machine (DRAFT → REVIEW → APPROVED → ACTIVE → DEPRECATED → ARCHIVED)
- Git-as-source-of-truth with PostgreSQL as runtime registry
- Golden dataset testing with 6 quality metrics (accuracy, completeness, hallucination rate, consistency, cost efficiency, latency)
- 4-phase rollout strategy (shadow → 5% canary → ramp 25/50/100% → full rollout)
- 5 role-based responsibilities (Prompt Author, Prompt Reviewer, Platform Engineer, Domain Expert, ML Engineer)

The prompts are consumed by AI workers that run as Python 3.14 services. Workers fetch prompts from the registry at runtime by name and version. Prompts are never hardcoded in business logic.

## Constraints

1. **Prompts must never be hardcoded**: No prompt text in business logic code. All prompts are stored in the registry and fetched at runtime.

2. **Version → output traceability**: Every AI extraction must record the exact prompt version used. Downstream artifacts must be traceable to the prompt version that produced them.

3. **Rollback must be possible**: If a prompt change causes quality degradation, operators must be able to revert to a previous version without code changes.

4. **Testing before deployment**: Every prompt change must pass automated testing against a golden dataset before reaching production. Changes must not degrade quality metrics.

5. **Approval workflow**: Prompt changes require human review before deployment. Automated testing is necessary but not sufficient — domain expertise is required for cultural sensitivity validation.

6. **Cost governance**: Prompt changes that significantly increase token usage must be flagged before deployment. Cost efficiency is a deployment gate metric.

7. **In-flight job compatibility**: When a new prompt version is deployed, in-flight jobs using the old prompt must complete without changes. The old version remains available in DEPRECATED state for 90 days.

8. **Multi-service consistency**: 5 AI services (extraction, normalization, validation, article, embedding) use prompts. All must use the same registry and governance framework.

## Problem Statement

Prompts define the behavior of every AI operation in the platform. Without governance, prompt changes cause reproducibility failures, quality regressions, cost explosions, and audit failures. Prompts must be versioned, testable, deployable, auditable, and traceable to every AI output. How do we implement a prompt governance framework that treats prompts as managed assets with versioning, testing, approval workflows, rollback capability, and full audit trails — across all 5 AI services and 15+ prompt categories?

# Decision

**Prompts are managed assets. Prompts are versioned, deployable, auditable, and stored in a Prompt Registry. Git is the source of truth for prompt content; PostgreSQL is the runtime registry. Every prompt change requires golden dataset testing, human review, and a phased rollout. Every AI extraction records the exact prompt version used. Rollback is a registry operation (not a code deployment).**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROMPT GOVERNANCE FRAMEWORK                           │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │               GIT REPOSITORY (Source of Truth)                     │   │
│  │                                                                   │   │
│  │  ai-platform/shared/src/ai_shared/prompts.py                      │   │
│  │    → All prompt templates as Python strings/constants             │   │
│  │    → system_prompt + user_prompt_template per category            │   │
│  │                                                                   │   │
│  │  ai-platform/prompt-registry/tests/golden-dataset/                │   │
│  │    → story-extraction/test-case-*.json                            │   │
│  │    → knowledge-extraction/test-case-*.json                        │   │
│  │    → article-generation/test-case-*.json                          │   │
│  │    → expected/*.json (known-correct outputs)                      │   │
│  │                                                                   │   │
│  │  ai-platform/prompt-registry/migrations/                          │   │
│  │    → SQL migrations for prompt database tables                    │   │
│  └─────────────────────┬─────────────────────────────────────────────┘   │
│                        │                                                 │
│                        │ CI/CD: lint → test golden →                     │
│                        │ evaluate → human review → deploy                │
│                        ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │               POSTGRESQL (Runtime Registry)                        │   │
│  │                                                                   │   │
│  │  ai.prompt_versions     → All prompt versions with full metadata  │   │
│  │  ai.prompt_evaluations  → Golden dataset test results             │   │
│  │  ai.prompt_audit_log    → Every status change with who/why        │   │
│  │                                                                   │   │
│  │  Workers fetch at runtime:                                        │   │
│  │    SELECT * FROM ai.prompt_versions                               │   │
│  │    WHERE prompt_name = 'story_canonicalization'                   │   │
│  │      AND is_active = true;                                        │   │
│  └─────────────────────────┬─────────────────────────────────────────┘   │
│                            │                                             │
│                            ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │               AI WORKERS (Runtime Consumption)                    │   │
│  │                                                                   │   │
│  │  extraction_service.py:                                           │   │
│  │    prompt = PromptRegistry.get("story_canonicalization", "1.2.3") │   │
│  │    result = await provider.extract_canonical_story(               │   │
│  │        transcript, metadata, prompt                               │   │
│  │    )                                                              │   │
│  │                                                                   │   │
│  │  Every extraction records:                                        │   │
│  │    { "prompt_version": "1.2.3", "prompt_name": "story_canon..." } │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Git Is Source of Truth, PostgreSQL Is Runtime Registry

Prompt content is authored and versioned in Git. CI/CD syncs prompt content from Git to PostgreSQL. Workers fetch prompts from PostgreSQL at runtime.

**Rationale**: Git provides code review, change history, branching, and tagging for prompts. PostgreSQL provides fast runtime lookups and supports active/deprecated/archived lifecycle management.

```python
# Git (prompts.py) — source of truth for prompt content
PROMPT_CANONICAL_STORY_V1 = """
You are a cultural knowledge extraction assistant...

TRANSCRIPT:
{transcript}

METADATA:
{metadata}

OUTPUT FORMAT:
Respond with a JSON object...
"""

# PostgreSQL registration — CI/CD syncs from Git
def sync_prompts_to_registry():
    for prompt_name, prompt_data in PROMPT_REGISTRY.items():
        content_hash = sha256(prompt_data['system_prompt'] + 
                              prompt_data['user_prompt_template'])
        
        # Skip if content already registered
        existing = db.fetchone(
            "SELECT id FROM ai.prompt_versions "
            "WHERE prompt_name = $1 AND content_hash = $2",
            prompt_name, content_hash
        )
        if existing:
            continue
        
        # Auto-determine version from git history
        new_version = determine_version(prompt_name)
        
        # Insert new version as DRAFT
        db.execute("""
            INSERT INTO ai.prompt_versions
            (prompt_name, version, system_prompt, user_prompt_template,
             output_schema, content_hash, status, author, change_reason)
            VALUES ($1, $2, $3, $4, $5, $6, 'draft', $7, $8)
        """, prompt_name, new_version, prompt_data['system_prompt'],
            prompt_data['user_prompt_template'], prompt_data['output_schema'],
            content_hash, prompt_data['author'], prompt_data['change_reason'])
```

### Rule 2: Semantic Versioning with Content Hash

Prompt versions follow semantic versioning (MAJOR.MINOR.PATCH). Version is determined by content hash — if the content changes, the version changes.

| Level | Increment When | Example Commit Message |
|-------|---------------|----------------------|
| **MAJOR** | Breaking output schema change | `BREAKING: Restructure extraction output from flat to nested entities` |
| **MINOR** | Non-breaking addition | `feat: Add ritual extraction to canonical story prompt` |
| **PATCH** | Fixes, clarifications | `fix: Clarify hallucination rule for ambiguous witness statements` |

```python
def determine_version(prompt_name: str) -> str:
    """Auto-determine version based on git commit message prefix."""
    current = db.fetch_one(
        "SELECT version FROM ai.prompt_versions "
        "WHERE prompt_name = $1 AND is_active = true",
        prompt_name
    )
    
    if not current:
        return "1.0.0"
    
    last_commit_msg = get_last_git_commit_msg(prompt_name)
    
    if last_commit_msg.startswith(("BREAKING", "schema:")):
        return increment_major(current.version)  # 1.2.3 → 2.0.0
    elif last_commit_msg.startswith(("feat", "add:")):
        return increment_minor(current.version)  # 1.2.3 → 1.3.0
    else:
        return increment_patch(current.version)  # 1.2.3 → 1.2.4
```

### Rule 3: Lifecycle State Machine

Every prompt version progresses through a defined lifecycle. Only ACTIVE prompts are used for production processing.

```
DRAFT ──→ REVIEW ──→ APPROVED ──→ ACTIVE ──→ DEPRECATED ──→ ARCHIVED
  │                    │                          │
  └────────────────────┘                          │
         (revision)                               │
                                                  ▼
                                             ARCHIVED
```

| State | Description | Can Execute? | Can Edit? |
|-------|-------------|-------------|-----------|
| **DRAFT** | Being authored | No | Yes |
| **REVIEW** | Submitted for review | No | No |
| **APPROVED** | Human review passed | No | No |
| **ACTIVE** | Deployed to production | Yes | No |
| **DEPRECATED** | Replaced, available for pinned jobs | Yes (pinned only) | No |
| **ARCHIVED** | Removed from runtime | No | No |

**Transition rules**:

| From | To | Required Conditions |
|------|----|---------------------|
| DRAFT → REVIEW | Golden dataset tests pass |
| REVIEW → APPROVED | All metrics meet thresholds + human reviewer approves |
| REVIEW → DRAFT | Reviewer requests changes |
| APPROVED → ACTIVE | Canary test passes (5% traffic, 4hr minimum) |
| ACTIVE → DEPRECATED | Newer version promoted to ACTIVE (automatic) |
| ACTIVE → ARCHIVED | Emergency removal (admin only) |
| DEPRECATED → ARCHIVED | 90 days since deprecation (automatic) |

```python
class PromptLifecycle:
    VALID_TRANSITIONS = {
        'draft': ['review'],
        'review': ['approved', 'draft'],
        'approved': ['active', 'draft'],
        'active': ['deprecated', 'archived'],
        'deprecated': ['archived'],
        'archived': [],
    }
    
    @classmethod
    def transition(cls, prompt_id, to_status, actor, reason):
        current = get_prompt_status(prompt_id)
        
        if to_status not in cls.VALID_TRANSITIONS.get(current, []):
            raise InvalidTransitionError(
                f"Cannot transition from {current} to {to_status}"
            )
        
        update_prompt_status(prompt_id, to_status)
        
        # When activating, deprecate the previous active version
        if to_status == 'active':
            deactivate_current_active(prompt_id)
        
        # Log audit
        log_audit(action='prompt_status_change', prompt_id=prompt_id,
                  from_status=current, to_status=to_status,
                  actor=actor, reason=reason)
```

### Rule 4: Golden Dataset Testing Before Review

Every prompt must pass golden dataset testing before it can move from DRAFT to REVIEW. The golden dataset is a curated collection of test cases with known-correct expected outputs.

```python
def run_golden_dataset_test(prompt_name: str, new_version: str) -> TestReport:
    test_cases = load_golden_dataset(prompt_name)
    
    results = []
    for test_case in test_cases:
        output = execute_prompt_with_version(new_version, test_case.input)
        metrics = calculate_metrics(output, test_case.expected_output)
        
        results.append({
            'test_case': test_case.id,
            'accuracy': metrics.accuracy,
            'hallucination_rate': metrics.hallucination_rate,
            'completeness': metrics.completeness,
            'passed': metrics.accuracy >= test_case.min_accuracy
                and metrics.hallucination_rate <= test_case.max_hallucination
        })
    
    # Regression check against previous active version
    current_active = get_active_version(prompt_name)
    old_results = run_golden_dataset_test(prompt_name, current_active.version)
    
    regression_detected = False
    for new_r, old_r in zip(results, old_results.results):
        if new_r['accuracy'] < old_r['accuracy'] - 0.05:  # 5% drop
            regression_detected = True
            break
    
    return TestReport(
        prompt_name=prompt_name,
        new_version=new_version,
        results=results,
        all_passed=all(r['passed'] for r in results),
        regression_detected=regression_detected
    )
```

**Quality metrics used as deployment gates**:

| Metric | Target | Weight | Calculation |
|--------|--------|--------|-------------|
| Accuracy | ≥ 0.85 | 40% | Exact match + semantic similarity (cosine > 0.9) on golden dataset |
| Completeness | ≥ 0.90 | 20% | Required fields populated / total required fields |
| Hallucination Rate | ≤ 0.05 | 20% | Extracted claims not supported by input evidence |
| Consistency | ≤ 0.10 | 10% | Std dev of quality scores across 3 runs of same input |
| Cost Efficiency | ≥ 0.80 | 5% | Baseline tokens / actual tokens |
| Latency P95 | ≤ 30s | 5% | 95th percentile execution time |

**Quality score formula**:
```
quality_score = accuracy × 0.40
             + completeness × 0.20
             + (1.0 - hallucination_rate) × 0.20
             + (1.0 - consistency) × 0.10
             + cost_efficiency × 0.05
             + (1.0 - latency_regression) × 0.05
```

### Rule 5: Phased Rollout with Shadow Mode

Deployment of an APPROVED prompt to ACTIVE follows a 4-phase rollout strategy.

```
Phase 1: Shadow Mode (0% traffic, 24hr minimum)
  - New prompt processes inputs in parallel with current ACTIVE
  - Only current ACTIVE output is used (no user impact)
  - Comparison metrics collected
  - If quality_score difference > 5%, block progression

Phase 2: Canary (5% traffic, 4hr minimum, 24hr recommended)
  - 5% of new jobs use the new prompt
  - Compare quality_score, hallucination_rate, cost, latency
  - Auto-rollback if any metric degrades > 5%

Phase 3: Ramp (25% → 50% → 100%, 2hr minimum per step)
  - Gradual traffic increase with metric verification at each step
  - Each step requires explicit go/no-go decision

Phase 4: Full Rollout (100% traffic, 7-day monitoring)
  - All new jobs use the new prompt
  - Continuous monitoring for quality drift
  - Old version in DEPRECATED state for 90 days
```

```python
def deploy_prompt(prompt_name: str, version: str):
    """Execute phased rollout for a prompt version."""
    with Phase("shadow", duration_hours=24) as phase:
        shadow_results = run_shadow_comparison(prompt_name, version)
        if shadow_results.quality_drop > 0.05:
            raise RolloutBlockedError("Quality drop > 5% in shadow mode")
    
    with Phase("canary", traffic_pct=5, duration_hours=4) as phase:
        canary_results = monitor_canary(prompt_name, version)
        if canary_results.any_metric_degraded:
            auto_rollback(prompt_name, version)
            raise RolloutBlockedError("Canary metrics degraded")
    
    for traffic_pct in [25, 50, 100]:
        with Phase("ramp", traffic_pct=traffic_pct, duration_hours=2) as phase:
            ramp_results = monitor_ramp(prompt_name, version, traffic_pct)
            if ramp_results.any_metric_degraded:
                auto_rollback(prompt_name, version)
                raise RolloutBlockedError(f"Ramp to {traffic_pct}% failed")
    
    set_prompt_active(prompt_name, version)
    log_deployment(prompt_name, version, "full_rollout")
```

### Rule 6: Prompt Rollback Without Code Deployment

Rollback is a registry operation, not a code deployment. Setting a different version as ACTIVE takes effect immediately for new jobs. In-flight jobs using the old version continue unaffected.

```python
def rollback_prompt(prompt_name: str, target_version: str, reason: str, actor: str):
    """Rollback to a previous version. No code deployment needed."""
    # Verify target version exists and is valid
    target = db.fetch_one(
        "SELECT id, version, status FROM ai.prompt_versions "
        "WHERE prompt_name = $1 AND version = $2",
        prompt_name, target_version
    )
    if not target:
        raise VersionNotFoundError(f"Version {target_version} not found")
    if target['status'] == 'archived':
        raise VersionArchivedError(f"Cannot rollback to archived version")
    
    # Get current active version
    current = db.fetch_one(
        "SELECT id, version FROM ai.prompt_versions "
        "WHERE prompt_name = $1 AND is_active = true",
        prompt_name
    )
    
    # Deprecate current
    update_prompt_status(current['id'], 'deprecated')
    
    # Activate target
    if target['status'] == 'deprecated':
        # Reactivating a deprecated version — set to active directly
        update_prompt_status(target['id'], 'active')
    else:
        # Version was never active — may need special handling
        approve_and_activate(target['id'])
    
    log_audit(action='rollback', prompt_name=prompt_name,
              from_version=current['version'], to_version=target['version'],
              reason=reason, actor=actor)
```

**Rollback triggers**:

| Trigger | Action | Time to Effect |
|---------|--------|----------------|
| Quality score drops > 5% in production | Automatic rollback to previous version | < 1 minute |
| Hallucination rate exceeds 10% in 1-hour window | Automatic rollback | < 1 minute |
| Average token usage increases > 50% | Operator-initiated rollback | < 5 minutes |
| Domain expert identifies cultural inaccuracy | Operator-initiated rollback | < 5 minutes |
| All providers fail (no prompt can execute) | No rollback needed (jobs queue) | N/A |

### Rule 7: Prompt Version Traceability in Every AI Output

Every AI extraction must record the exact prompt version used. This enables tracing any artifact back to the prompt that produced it.

```json
{
  "extractionMetadata": {
    "modelUsed": "gemini-2.5-pro",
    "promptVersion": "1.2.3",
    "promptName": "story_canonicalization",
    "inputTokens": 4502,
    "outputTokens": 1280,
    "executionCost": 0.0032
  },
  "provenance": {
    "sourceId": "b1c2d3e4-...",
    "transcriptId": "d4c3b2a1-...",
    "extractionJobId": "e5f6a7b8-...",
    "promptVersion": "1.2.3",
    "payloadHash": "sha256-..."  // Hash of prompt content used
  }
}
```

**Query for traceability**:
```sql
-- Find all artifacts produced by a specific prompt version
SELECT a.* FROM ai_output_canonical_stories a
WHERE a.provenance->>'promptVersion' = '1.2.3';

-- Compare quality across prompt versions
SELECT 
    provenance->>'promptVersion' AS prompt_version,
    COUNT(*) AS total_extractions,
    AVG(confidence_score) AS avg_confidence,
    AVG((extraction_metadata->>'executionCost')::numeric) AS avg_cost
FROM ai_output_canonical_stories
GROUP BY provenance->>'promptVersion'
ORDER BY prompt_version;
```

### Rule 8: Audit Trail for Every Prompt Change

Every prompt lifecycle transition is logged with who, what, when, and why.

```sql
CREATE TABLE ai.prompt_audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_name         VARCHAR(100) NOT NULL,
    prompt_version      VARCHAR(50) NOT NULL,
    action              VARCHAR(50) NOT NULL,
    -- 'created', 'status_change:review', 'status_change:approved',
    -- 'status_change:active', 'status_change:deprecated',
    -- 'status_change:archived', 'rollback', 'content_update',
    -- 'test_executed', 'deployment_started', 'deployment_completed',
    -- 'deployment_rolled_back'
    
    from_status         VARCHAR(50),
    to_status           VARCHAR(50),
    from_version        VARCHAR(50),    -- For rollbacks
    to_version          VARCHAR(50),    -- For rollbacks
    
    actor               VARCHAR(100) NOT NULL,
    reason              TEXT NOT NULL,
    metadata            JSONB,          -- Test results, evaluation scores, etc.
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_prompt_audit_name ON ai.prompt_audit_log(prompt_name, created_at DESC);
CREATE INDEX idx_prompt_audit_actor ON ai.prompt_audit_log(actor, created_at DESC);
```

### Rule 9: Prompt Consumption in AI Workers

AI workers fetch prompts from the registry at runtime. Prompts are never hardcoded in business logic.

```python
class PromptRegistry:
    """Runtime prompt registry client used by AI workers."""
    
    RESOLUTION_PRIORITY = [
        "explicit_version",   # Job specifies prompt_version in config
        "active_version",     # is_active = true in database
        "latest_version",     # Most recent created_at (fallback)
    ]
    
    @classmethod
    async def get(cls, prompt_name: str, version: Optional[str] = None) -> Prompt:
        """Fetch a prompt from the registry.
        
        Resolution order:
        1. If version specified, fetch that exact version
        2. If no version, fetch the active version
        3. If no active version, fetch the latest version
        """
        if version:
            row = await db.fetch_one(
                "SELECT * FROM ai.prompt_versions "
                "WHERE prompt_name = $1 AND version = $2",
                prompt_name, version
            )
        else:
            row = await db.fetch_one(
                "SELECT * FROM ai.prompt_versions "
                "WHERE prompt_name = $1 AND is_active = true",
                prompt_name
            )
        
        if not row:
            # Fallback to latest version
            row = await db.fetch_one(
                "SELECT * FROM ai.prompt_versions "
                "WHERE prompt_name = $1 "
                "ORDER BY created_at DESC LIMIT 1",
                prompt_name
            )
        
        if not row:
            raise PromptNotFoundError(f"No prompt found: {prompt_name}")
        
        return Prompt(
            system_prompt=row['system_prompt'],
            user_prompt_template=row['user_prompt_template'],
            version=row['version'],
            model=row['default_model'],
            temperature=row['default_temperature'],
            max_tokens=row['default_max_tokens']
        )

# Usage in AI worker — prompt is fetched dynamically, never hardcoded
class ExtractionWorker:
    async def process_job(self, job: ExtractionJob):
        prompt = await PromptRegistry.get(
            "story_canonicalization",
            version=job.prompt_version  # Optional: pin to specific version
        )
        
        provider = await AIProviderFactory.get_provider("canonical_story")
        result = await provider.extract_canonical_story(
            transcript=job.transcript,
            metadata=job.metadata,
            prompt=prompt  # Prompt object, not raw string
        )
        
        # Record prompt version in output for traceability
        result.metadata['prompt_version'] = prompt.version
        result.metadata['prompt_name'] = "story_canonicalization"
```

### Rule 10: Human Review with Domain Expert Sign-Off

In addition to automated golden dataset testing, every prompt change requires human review. For stories involving Indonesian folklore, a domain expert must sign off on cultural accuracy.

**Human review checklist**:
```
□ Output schema is valid and complete
□ No hallucination-inducing language in instructions
□ Cultural nuance preserved (domain expert sign-off required for folklore prompts)
□ Instructions are unambiguous and deterministic
□ Few-shot examples are representative and correct
□ Temperature setting is appropriate for the task type
  - Extraction/normalization/validation: 0.1–0.2 (deterministic)
  - Article generation: 0.3–0.8 (creative range)
□ No prompt injection vulnerabilities
□ No PII or sensitive data in few-shot examples
□ Edge cases considered (empty input, non-Indonesian, multiple speakers)
```

**Review failure modes**:

| Failure | Action |
|---------|--------|
| Automated golden dataset fails | Cannot proceed to REVIEW. Fix prompt content. |
| Human reviewer rejects | Return to DRAFT with review notes. |
| Domain expert flags cultural inaccuracy | Return to DRAFT. Consult with cultural advisory board. |
| Cost efficiency below threshold | Optimize prompt for token usage. Re-submit. |

# Alternatives Considered

## Alternative 1: Hardcoded Prompts in Business Logic

**Description**: Prompts are written directly in Python code as string constants. Each AI worker has its prompts embedded in the service code. To change a prompt, developers modify the code, create a PR, run tests, and deploy a new version of the service.

**Advantages**:
- Simplest possible implementation — prompts are just string variables
- No prompt registry infrastructure to build and maintain
- No database dependency for prompt storage
- Prompts are versioned as part of the codebase (Git handles versioning)
- No additional deployment process — prompts are deployed with the service

**Disadvantages**:
- **Prompt change = code deployment**: Every prompt change requires a full CI/CD pipeline run, service rebuild, and deployment. For 15 prompt categories with frequent iterations, this means 15× the deployment frequency.
- **No prompt-specific testing**: Prompts are tested as part of service integration tests. There is no golden dataset, no regression testing, no quality metrics specific to prompts.
- **No phased rollout**: A prompt change is deployed with the service — 100% of traffic hits the new prompt immediately. No shadow mode, no canary, no ramp.
- **No rollback without code revert**: Rolling back a prompt requires reverting the code change and redeploying. This takes 15–60 minutes versus < 1 minute with registry-based rollback.
- **No traceability**: The system records which service version ran, but not which prompt version was used. A service deployment may include multiple prompt changes, making it impossible to isolate the cause of quality changes.
- **Cross-service prompt sharing is complex**: Multiple services may use the same prompt template. Hardcoded prompts require duplicating the prompt across services or extracting to a shared library — which again requires a deployment to change.
- **No lifecycle management**: DRAFT, REVIEW, APPROVED, ACTIVE, DEPRECATED, ARCHIVED states do not exist. A prompt is either in the codebase (ready to deploy) or not. There is no staging or approval flow.

**Rejection rationale**: Hardcoded prompts violate the PRD requirement (§15: "Prompts must never be hardcoded"), couple prompt changes to service deployments, eliminate prompt-specific testing and rollout, and provide no traceability from prompt version to AI output. The registry approach is essential for decoupling prompt iteration velocity from service deployment velocity.

## Alternative 2: External Prompt Management Service (Separate Microservice)

**Description**: Deploy the Prompt Registry as a standalone microservice with its own API, database, and deployment pipeline. All AI workers call this service via REST/gRPC to fetch prompts. The service provides prompt authoring, versioning, testing, approval workflows, and deployment management through a web UI.

**Advantages**:
- Dedicated service with focused functionality
- Web UI for non-technical prompt authors (editors, domain experts)
- Independent scaling — prompt lookups don't affect AI worker resources
- Centralized prompt management across all services
- Can be used by future services beyond the AI Platform
- Built-in API documentation and client SDKs

**Disadvantages**:
- **Additional network latency**: Every AI operation requires an HTTP call to the prompt service before calling the AI provider. At 10–120 seconds of AI provider latency, 5–50ms of prompt lookup latency is negligible, but it adds a failure point.
- **Infrastructure overhead**: A separate service requires its own deployment pipeline, monitoring, scaling, and backup procedures. For a modular monolith with a small team, this is significant overhead.
- **Caching complexity**: To avoid the latency of synchronous calls, workers would cache prompts locally. Cache invalidation when a prompt is rolled back adds complexity.
- **Operational burden**: The prompt service must be available for AI workers to function. A prompt service outage blocks all AI processing. With the Git + PostgreSQL approach, workers read prompts directly from the shared database, which is already highly available.
- **Overkill for current scale**: With 15 prompt categories and a small team, a full microservice with web UI is premature. The Git + PostgreSQL approach provides the same functionality with less complexity.
- **Security surface area**: A prompt service with a web UI introduces authentication, authorization, and API security concerns that the database-only approach avoids.

**Rejection rationale**: A dedicated prompt management microservice adds infrastructure overhead, latency, and operational complexity that is not justified for the current scale. The Git + PostgreSQL approach (Git for authoring/review, PostgreSQL for runtime lookups) provides the same governance capabilities with significantly less infrastructure. If the platform grows to require a web UI for non-technical prompt authors, the prompt registry can be extracted to a service at that time.

## Alternative 3: Configuration File-Based Prompts (YAML/JSON Files Mounted in Containers)

**Description**: Store prompts as YAML or JSON configuration files that are mounted into AI worker containers at runtime. Configuration management tools (Ansible, Helm, Kubernetes ConfigMaps) manage prompt versions. Changing a prompt requires updating the config file and redeploying the configuration (not the service code).

**Advantages**:
- Prompts are externalized from code (not hardcoded)
- Configuration management tools provide versioning and rollback
- No prompt registry database to build and maintain
- Kubernetes ConfigMaps are well-understood by the team
- No additional API or service for prompt lookup
- Prompts can be managed by non-developers through config file PRs

**Disadvantages**:
- **ConfigMap update = container restart**: Changing a ConfigMap requires restarting the pods to pick up the new configuration. For Kubernetes, this means a rolling update of all AI worker pods.
- **No phased rollout**: ConfigMap changes apply to all pods in the deployment. There is no 5% canary or gradual ramp for prompt changes.
- **No shadow mode**: Cannot run old and new prompts in parallel for comparison.
- **No per-version traceability**: The system records which ConfigMap version was mounted, but not which specific prompt version was used. If a ConfigMap contains multiple prompts, it is impossible to isolate changes.
- **ConfigMap size limits**: Kubernetes ConfigMaps are limited to 1MB. With 15+ prompt templates, few-shot examples, and output schemas, this limit may be reached.
- **No lifecycle management**: DRAFT, REVIEW, APPROVED states do not exist in ConfigMaps. A prompt is either in the ConfigMap (deployed) or not.
- **No prompt-specific testing**: ConfigMaps contain configuration, not test cases. There is no golden dataset execution, no regression testing, no quality metrics.
- **Rollback is a Kubernetes operation**: Rolling back requires `kubectl rollout undo`, which reverts ALL configuration changes, not just the prompt change.

**Rejection rationale**: ConfigMap-based prompts are better than hardcoded prompts but lack the governance features required by the PRD: golden dataset testing, phased rollout, shadow mode, canary deployment, and per-version traceability. The registry database approach provides these features without the operational overhead of container restarts for every prompt change.

## Alternative 4: Prompt Versioning via Git Tags Only (No Registry Database)

**Description**: Use Git tags for prompt versioning. Each prompt version is a Git tag pointing to the commit that contains the prompt content. Workers clone the repository and check out the required tag at startup. No PostgreSQL registry, no runtime database lookups.

**Advantages**:
- Git is already used for version control — no new infrastructure
- Git tags provide immutable version references
- Full git history for every prompt change
- No database dependency for prompt storage
- Prompts can be reviewed using standard Git workflows (PRs, code review)

**Disadvantages**:
- **Worker startup requires git clone**: Every worker pod must clone the entire prompt repository or fetch specific files. This adds 10–60 seconds to pod startup time.
- **No dynamic version resolution**: Workers cannot resolve "give me the active version of story_canonicalization" without a runtime registry. They must know the exact version at startup. Changing the active version requires redeploying workers.
- **No lifecycle states**: DRAFT, REVIEW, APPROVED, ACTIVE, DEPRECATED, ARCHIVED states do not exist in Git tags. A tag is either created (exists) or not.
- **No runtime traceability**: The system can record which Git tag was used, but cannot query "which prompt version was active on June 1?" without external tracking.
- **No phased rollout**: Cannot do shadow mode or canary with Git tags. A tag is either active or not — there is no traffic splitting.
- **Rollback requires redeployment**: Changing the active prompt version requires updating the worker configuration and redeploying. This takes 5–15 minutes versus < 1 minute with registry-based rollback.
- **Repository size growth**: 15 prompt categories × frequent versions × few-shot examples = large repository. Cloning this repository for every worker startup is wasteful.

**Rejection rationale**: Git tags provide immutable versioning but lack the runtime features required for prompt governance: dynamic version resolution, lifecycle states, phased rollout, and instant rollback. The registry database complements Git by providing runtime capabilities while Git remains the source of truth for content.

# Consequences

## Positive

1. **Prompt changes decoupled from code deployments**: A prompt change goes from DRAFT → REVIEW → APPROVED → ACTIVE without any service code change. Rollback is a < 1 minute registry operation, not a 15–60 minute code revert and redeploy.

2. **Version-to-output traceability**: Every AI extraction records `promptVersion` and `promptName`. Downstream artifacts are traceable to the exact prompt version that produced them. Quality regression can be isolated to a specific prompt change.

3. **Quality gates prevent regressions**: Golden dataset testing catches quality regressions before deployment. The regression checker compares new prompt accuracy against the current ACTIVE version. A 5% accuracy drop blocks the change.

4. **Phased rollout reduces risk**: Shadow mode detects quality differences without user impact. Canary deployment limits blast radius to 5% of traffic. Gradual ramp enables metric monitoring at each step. Auto-rollback triggers if metrics degrade.

5. **Audit trail for every change**: Every prompt lifecycle transition is logged with who, what, when, and why. Compliance and debugging are supported by complete historical records.

6. **Cost efficiency as a deployment gate**: Cost efficiency (token usage relative to baseline) is a weighted metric in the quality score. A prompt change that doubles token usage is flagged before deployment.

7. **Domain expert validation**: Human review with domain expert sign-off ensures cultural accuracy for Indonesian folklore prompts. Automated testing validates structure; human review validates cultural nuance.

8. **Multi-service consistency**: All 5 AI services (extraction, normalization, validation, article, embedding) use the same prompt registry, the same lifecycle, the same testing framework, and the same rollout strategy.

## Negative

1. **Infrastructure complexity**: The prompt registry requires a database table (`ai.prompt_versions`), a CI/CD sync process (Git → PostgreSQL), and runtime lookup logic in AI workers. This is more complex than hardcoded prompts.

2. **Golden dataset maintenance**: The golden dataset must be maintained and expanded as new prompt categories are added. Each test case requires manual creation of expected outputs. Dataset maintenance is ongoing effort.

3. **Prompt testing adds pipeline latency**: Golden dataset testing adds 5–30 minutes to the prompt deployment pipeline. For urgent prompt changes (e.g., fixing a hallucination issue), this delay may be frustrating.

4. **Two sources of truth to maintain**: Git is the source of truth for content. PostgreSQL is the source of truth for runtime state. Keeping them in sync requires CI/CD automation. A sync failure means the database may have stale prompts.

5. **Domain expert availability bottleneck**: Human review with domain expert sign-off is a required gate. If the domain expert is unavailable, prompt changes are blocked. This creates a dependency on a potentially scarce resource.

6. **Shadow mode doubles AI costs**: During shadow mode, every input is processed twice (current ACTIVE + new prompt). For a high-volume prompt category, this doubles AI provider costs during the shadow period (24 hours minimum).

7. **Rollback reactivation complexity**: Reactivating a DEPRECATED version (for rollback) requires careful handling. The old version may not be compatible with current output expectations or downstream consumers. Rollback is a registry operation but may require downstream coordination.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Deployment velocity** | Prompt changes deployed without code deploy | CI/CD pipeline for Git → DB sync |
| **Quality assurance** | Golden dataset + regression testing | Dataset maintenance overhead |
| **Risk management** | Shadow mode + canary + ramp | Shadow mode doubles AI costs |
| **Traceability** | Every output traces to prompt version | Must record version in every extraction |
| **Rollback speed** | < 1 minute registry operation | May need to reactivate deprecated versions |
| **Cultural accuracy** | Domain expert sign-off required | Domain expert availability bottleneck |
| **Infrastructure** | Decoupled from codebase | Registry DB + sync process + runtime client |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Git → PostgreSQL sync fails** | Low | Medium — workers use stale prompts | Workers fall back to cached prompt version. Sync retry with exponential backoff. Alert on sync failure. |
| **Runtime prompt lookup failure** | Low | High — worker cannot fetch prompt | Worker caches most recently used prompts. Falls back to cached version if DB unavailable. Logs warning. |
| **Golden dataset becomes outdated** | Medium | Medium — tests pass but real-world quality degrades | Monthly golden dataset review. Add new test cases from real production issues. Rotate cases quarterly. |
| **Content hash collision** | Very Low | Critical — version mismatch | SHA-256 collision probability is negligible. Monitor for duplicates as defense-in-depth. |
| **Shadow mode cost overrun** | Medium | Medium — unexpected AI costs | Limit shadow mode to 24 hours. Use cost budget alerts. Skip shadow mode for low-risk PATCH changes. |
| **Rollback breaks downstream consumers** | Low | Medium — downstream expects new format | MAJOR version changes should not be rolled back without downstream coordination. Rollback is for PATCH/MINOR regressions. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Domain expert unavailable for review** | Medium | High — prompt changes blocked | Train backup domain experts. Document cultural review checklist. Implement temporary override for urgent changes (post-hoc review). |
| **Prompt author bypasses review process** | Low | High — prompt deployed without review | CI/CD enforces golden dataset test pass + human review status check. Direct database modification is blocked by RLS policies. |
| **Golden dataset test flakiness** | Medium | Low — test passes intermittently | Use semantic similarity thresholds (not exact match). Pin AI provider model version during testing. Set consistency threshold (3 runs). |
| **Prompt version number conflicts** | Low | Medium — two changes get same version | Content hash ensures version uniqueness. CI/CD rejects duplicate hashes. Manual version override requires explicit approval. |
| **Deprecated prompt still used after 90-day window** | Low | Low — pinned jobs fail after archive | Notify job owners 30 days before deprecation. Auto-archive after 90 days. Failed jobs can be reprocessed with active prompt version. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **A/B testing of prompts required** | Shadow mode + canary may not be sufficient | Extend canary to support multi-version A/B testing. Random assignment of prompt versions with metric comparison. |
| **Prompt fine-tuning replaces prompt engineering** | Registry governance model may not fit fine-tuned models | Extend registry to store fine-tuned model metadata (base model, training data, hyperparameters). Apply similar lifecycle and testing. |
| **Automated prompt optimization (prompt tuning)** | Manual prompt authoring may be partially automated | AI-generated prompt suggestions go through the same governance process. The registry supports auto-generated prompt versions with a `source: auto_tuned` tag. |
| **Multi-language prompt variants** | Single prompt per category may not suffice for all languages | Extend registry with `language` field. Workers fetch prompt by name + language. Golden dataset includes language-specific test cases. |
| **Regulatory requirements for AI transparency** | Must document prompt changes that affect user-facing outputs | Already covered by audit log. Extend with prompt change impact assessment for regulatory review. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Prompt count exceeds 30 categories**: At this scale, prompt organization and discovery become complex. Consider categorizing prompts by domain (story, knowledge, article, embedding) with separate lifecycle management per category.

2. **Non-technical prompt authors need web UI**: If editors or domain experts need to author prompts without Git, implement a prompt management UI. The UI should generate Git commits behind the scenes to maintain Git as source of truth.

3. **Prompt A/B testing becomes standard practice**: If the team regularly runs multi-version experiments, extend the registry to support simultaneous ACTIVE versions with traffic splitting. The rollout strategy should support arbitrary percentage distributions.

4. **Fine-tuned models replace prompt-based extraction**: If the platform fine-tunes models for extraction tasks, the registry must be extended to store model metadata alongside prompts. The governance framework (versioning, testing, rollout) remains applicable.

5. **Cross-team prompt ownership**: If multiple teams own different prompt categories (e.g., AI Team owns extraction prompts, Editorial Team owns article generation prompts), implement per-category access control and independent lifecycle management.

6. **Prompt marketplace or community contributions**: If the platform allows community-contributed prompts (e.g., researchers can submit experimental extraction prompts), implement a separate review track for community contributions with additional validation gates.

# References

- **AI Platform PRD §15** — "Prompt Architecture" — Prompts are managed assets with registry, versioning, approval workflow, rollback, and audit trail.
- **AI Platform PRD §16** — "Prompt Categories" — 9 prompt categories defined.
- **ADR-004: Queue-Driven AI Platform** — AI workers consume prompts from registry.
- **ADR-007: Canonical Story Core Contract** — Prompt output must conform to Canonical Story schema.
- **ADR-009: AI Provider Abstraction** — Prompts are fed to the provider abstraction layer, not directly to SDKs.
- **Prompt Registry & Governance Specification** — `docs/ai-platform/prompt-registry-governance-specification.md` — Full specification document.
- **Semantic Versioning** — https://semver.org/ — MAJOR.MINOR.PATCH versioning for prompt changes.
- **Kubernetes ConfigMaps** — https://kubernetes.io/docs/concepts/configuration/configmap/ — Alternative considered for prompt storage.
- **Feature Flags (Canary Releases)** — https://martinfowler.com/bliki/CanaryRelease.html — Pattern for phased rollout of prompt changes.