# Prompt Registry & Governance Specification

## The Living Atlas of Indonesian Mystery Culture

**Version:** 1.0  
**Status:** Draft  
**Owner:** AI Platform Team  
**Classification:** LLMOps Architecture Document

---

# Table of Contents

1. [Purpose](#1-purpose)
2. [Prompt Architecture](#2-prompt-architecture)
3. [Prompt Categories](#3-prompt-categories)
4. [Prompt Metadata Model](#4-prompt-metadata-model)
5. [Prompt Lifecycle](#5-prompt-lifecycle)
6. [Prompt Storage Strategy](#6-prompt-storage-strategy)
7. [Prompt Testing Framework](#7-prompt-testing-framework)
8. [Prompt Evaluation Metrics](#8-prompt-evaluation-metrics)
9. [Prompt Deployment Strategy](#9-prompt-deployment-strategy)
10. [Audit Requirements](#10-audit-requirements)
11. [Future Compatibility](#11-future-compatibility)

---

# 1. Purpose

## 1.1 Why Prompts Require Governance

Prompts are the single most important strategic asset in the AI Platform. A prompt defines how the AI interprets transcripts, extracts cultural knowledge, normalizes entities, validates quality, and generates articles. The difference between a well-crafted prompt and a poorly-crafted one can change:
- Extraction accuracy by 20–40%
- Hallucination rate by 5–15%
- Execution cost by 2–10x
- Downstream article quality by 30–50%

**Consequences of ungoverned prompts:**
- **Reproducibility failure:** Extractions change without notice, breaking downstream systems and research reproducibility.
- **Quality regression:** A prompt "improvement" that degrades extraction quality goes undetected without regression testing.
- **Cost explosion:** Prompt changes that increase token usage by 5x without improving quality.
- **Audit failure:** Cannot determine which prompt version produced a given knowledge artifact.
- **Rollback impossibility:** Cannot revert to a known-good prompt without versioning.

**Governance principles:**
1. Every prompt is a versioned, immutable asset.
2. Every extraction is traceable to a specific prompt version.
3. Every prompt change requires testing, approval, and audit.
4. Prompts are stored separately from code — no hardcoded prompts.
5. Prompts are language-agnostic and model-agnostic.

## 1.2 Governance Scope

This specification governs all prompts used in AI-driven pipeline stages:

| Pipeline Stage | Prompts Governed |
|---------------|------------------|
| Canonical Story Extraction | System prompt, user prompt template |
| Knowledge Extraction (Themes) | System prompt, user prompt template |
| Knowledge Extraction (Entities) | System prompt, user prompt template |
| Knowledge Extraction (Claims) | System prompt, user prompt template |
| Knowledge Extraction (Motifs) | System prompt, user prompt template |
| Knowledge Normalization | System prompt, user prompt template |
| Knowledge Validation | System prompt, user prompt template |
| Narrative Article Generation | System prompt, user prompt template |
| Knowledge Article Generation | System prompt, user prompt template |
| News Article Generation | System prompt, user prompt template |
| Creative Article Generation | System prompt, user prompt template |
| Embedding Enrichment | Text preprocessing prompt |

---

# 2. Prompt Architecture

## 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PROMPT REGISTRY SERVICE                         │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                    PostgreSQL (ai.prompt_versions)           │     │
│  │  prompt_id │ name │ version │ status │ system_prompt │ ... │     │
│  └────────────────────────────────────────────────────────────┘     │
│                          ▲                                           │
│                          │ REST API / SDK                            │
│                          ▼                                           │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                  Git Repository (source of truth)             │     │
│  │  ai-platform/shared/src/ai_shared/prompts.py                 │     │
│  │  ai-platform/extraction-service/schemas/prompts/             │     │
│  │  ai-platform/article-service/schemas/prompts/                │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
           │                                      │
           │ deploy                              │ fetch at runtime
           ▼                                      ▼
┌──────────────────────┐          ┌──────────────────────────────────┐
│  CI/CD Pipeline      │          │  AI WORKERS (runtime)             │
│                      │          │                                  │
│  lint → test →       │          │  extractors.py                   │
│  evaluate → approve  │          │  generators.py                   │
│  → deploy            │          │  canonical_pipeline.py           │
│                      │          │                                  │
│                      │          │  prompt_version = "v1.2.3"       │
│                      │          │  prompt = registry.fetch(name)   │
└──────────────────────┘          └──────────────────────────────────┘
```

## 2.2 Prompt Registry

The Prompt Registry is the central database of all prompt versions. It provides:
- **Storage:** Persists all prompt versions with full metadata.
- **Retrieval:** Workers fetch prompts by name + version at runtime.
- **Lifecycle:** Manages transitions through draft → review → active → deprecated → archived.
- **Audit:** Logs every change with who, when, and why.
- **Testing:** Stores test results and evaluation scores per version.

## 2.3 Prompt Versions

Versions follow strict semantic versioning: `MAJOR.MINOR.PATCH`

| Level | Increment When | Example |
|-------|---------------|---------|
| **MAJOR** | Breaking change in output schema, format, or semantics | Output structure changes from flat to nested |
| **MINOR** | Non-breaking addition (new extraction fields, new instructions) | Add "rituals" to extraction types |
| **PATCH** | Fixes, clarifications, wording improvements | Fix typo, clarify ambiguity rule |

**Version is determined by content hash** — not by developer assignment. If the prompt content changes, the version changes.

## 2.4 Prompt Deployments

Deployment associates a prompt version with a runtime environment:

| Environment | Purpose | Deployment Model |
|-------------|---------|-----------------|
| **development** | Local testing, prompt authoring | Direct database update |
| **staging** | Integration testing, golden dataset evaluation | Automated CI/CD |
| **production** | Live pipeline processing | Canary rollout |

## 2.5 Prompt Rollback

Rollback reverts the active prompt to a previous version:

```
Trigger: Production metric degradation detected (quality score drop > 5%)
Process:
  1. Identify the problematic prompt version
  2. Set active version to previous known-good version
  3. All new jobs use the reverted prompt
  4. Existing in-flight jobs continue with their pinned version
  5. Post-mortem on the failed prompt change
```

## 2.6 Prompt Testing

Every prompt version must pass through the testing framework before reaching production (see Section 7).

---

# 3. Prompt Categories

## 3.1 Category Overview

| Category | Prompt Name | Service | AI Call Type | Temperature |
|----------|-------------|---------|-------------|-------------|
| Story Extraction | `story_canonicalization` | extraction-service | Structured JSON | 0.2 |
| Theme Extraction | `theme_extraction` | extraction-service | Structured JSON | 0.2 |
| Entity Extraction | `entity_extraction` | extraction-service | Structured JSON | 0.2 |
| Claim Extraction | `claim_extraction` | extraction-service | Structured JSON | 0.2 |
| Motif Extraction | `motif_extraction` | extraction-service | Structured JSON | 0.2 |
| Relationship Extraction | `relationship_extraction` | extraction-service | Structured JSON | 0.2 |
| Archetype Extraction | `archetype_extraction` | extraction-service | Structured JSON | 0.2 |
| Story Boundary Detection | `story_boundary` | extraction-service | Structured JSON | 0.1 |
| Knowledge Normalization | `knowledge_normalization` | normalization-service | Structured JSON | 0.1 |
| Knowledge Validation | `knowledge_validation` | validation-service | Structured JSON | 0.1 |
| Narrative Article | `narrative_article` | article-service | Markdown | 0.3 |
| Knowledge Article | `knowledge_article` | article-service | Markdown | 0.2 |
| News Article | `news_article` | article-service | Markdown | 0.3 |
| Creative Article | `creative_article` | article-service | Markdown | 0.8 |
| Embedding Enrichment | `embedding_enrichment` | embedding-service | Text | 0.0 |

## 3.2 Story Extraction Prompts

### story_canonicalization

**Purpose:** Transform a raw transcript into a structured canonical story record. This is the most critical prompt in the system — it defines the fundamental data model for all downstream processing.

**System Prompt Role:** Defines the AI's identity as the Canonical Story Extraction Engine. Establishes the 10 governing rules: never invent, preserve uncertainty, preserve contradictions, distinguish claims from facts, respect cultural nuance.

**User Prompt Template:** Accepts the raw transcript text and metadata. Instructs the AI to extract story title, summary, narrative structure, and provenance information.

**Output Schema:**
```json
{
  "storyTitle": "string",
  "storySummary": "string",
  "language": "string",
  "narrativeStructure": {
    "type": "first_person | third_person | interview | mixed",
    "tone": "factual | legendary | personal | instructional"
  },
  "witnesses": [{"name": "string", "role": "string"}],
  "keyEvents": [{"description": "string", "timestamp": "string"}],
  "provenance": {"source": "string", "reliability": "high | medium | low"}
}
```

### theme_extraction

**Purpose:** Extract cultural themes from the canonical story.

**Output Schema:** List of themes with name, description, confidence, and evidence segments.

### entity_extraction

**Purpose:** Extract named entities — spirits, locations, people, creatures, objects.

**Output Schema:** List of entities with type classification, aliases, and confidence.

### claim_extraction

**Purpose:** Extract factual claims with supporting evidence from the transcript.

**Output Schema:** Each claim has statement, confidence, evidence segments, and status.

### motif_extraction

**Purpose:** Identify narrative motifs (recurring patterns in folklore).

**Output Schema:** Motif type (setting, character, plot), name, cultural region, confidence.

## 3.3 Normalization Prompt

### knowledge_normalization

**Purpose:** Resolve ambiguities, detect aliases, and merge duplicate entities across extracted knowledge.

**System Prompt Role:** Defines normalization rules specific to Indonesian folklore: regional name variants (Kuntilanak ↔ Pontianak), entity classification resolution, and cultural context preservation.

**Temperature:** 0.1 (highly deterministic — normalization should be conservative).

## 3.4 Validation Prompt

### knowledge_validation

**Purpose:** Assess quality, completeness, consistency, and confidence of extracted knowledge.

**System Prompt Role:** Acts as a quality auditor. Evaluates against: schema completeness, evidence sufficiency, confidence calibration, cross-entity consistency, contradiction detection.

## 3.5 Article Generation Prompts

**Shared System Prompt Base:** All article prompts share common instructions for maintaining factual accuracy, provenance tracking, and cultural sensitivity.

### narrative_article

**Temperature:** 0.3  
**Purpose:** Journalistic narrative article — storytelling with factual grounding. Suitable for general readership.

### knowledge_article

**Temperature:** 0.2  
**Purpose:** Academic-styled reference article — comprehensive, structured, citation-heavy. Suitable for researchers.

### news_article

**Temperature:** 0.3  
**Purpose:** News-style article — concise, hook-driven, timestamped. Suitable for current events.

### creative_article

**Temperature:** 0.8  
**Purpose:** Creative retelling — literary style, atmospheric, engaging. Suitable for feature content. Highest temperature — allows creative interpretation while maintaining factual constraints.

## 3.6 Embedding Enrichment Prompt

### embedding_enrichment

**Purpose:** Preprocess text for embedding generation — normalize, chunk, and add context for better vector representations.

**Temperature:** 0.0 (deterministic).

---

# 4. Prompt Metadata Model

## 4.1 Database Schema

```sql
CREATE TABLE ai.prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_name VARCHAR(100) NOT NULL,        -- e.g., "story_canonicalization"
    version VARCHAR(50) NOT NULL,              -- e.g., "1.2.3"
    title VARCHAR(200),                        -- Human-readable title
    
    -- Prompt content
    system_prompt TEXT,                        -- System/role prompt (may be NULL)
    user_prompt_template TEXT NOT NULL,         -- Jinja2 template for user prompt
    prompt_type VARCHAR(50) NOT NULL DEFAULT 'jinja2',  -- jinja2, f_string, plain
    output_schema JSONB,                       -- Expected JSON schema for structured outputs
    few_shot_examples JSONB NOT NULL DEFAULT '[]',
    
    -- Configuration defaults
    default_model VARCHAR(100) NOT NULL DEFAULT 'gemini-2.5-pro',
    default_temperature DECIMAL(4,2) NOT NULL DEFAULT 0.2,
    default_max_tokens INTEGER NOT NULL DEFAULT 4096,
    
    -- Lifecycle
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
        -- draft, review, approved, active, deprecated, archived
    is_active BOOLEAN NOT NULL DEFAULT false,
    parent_version VARCHAR(50),                -- version this was derived from
    
    -- Ownership
    owner VARCHAR(100) NOT NULL,               -- team or individual responsible
    author VARCHAR(100) NOT NULL,              -- person who created this version
    reviewer VARCHAR(100),                     -- person who approved this version
    
    -- Metadata
    change_reason TEXT NOT NULL,               -- why this version was created
    release_notes TEXT,
    tags JSONB NOT NULL DEFAULT '[]',           -- ["story", "extraction", "v2-migration"]
    content_hash VARCHAR(64) NOT NULL,          -- SHA-256 of canonical content
    
    -- Timing
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at TIMESTAMPTZ,
    activated_at TIMESTAMPTZ,
    deprecated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    
    CONSTRAINT uq_prompt_name_version UNIQUE(prompt_name, version)
);

-- Index for active prompt lookup
CREATE INDEX idx_prompt_active ON ai.prompt_versions(prompt_name, is_active)
    WHERE is_active = true;

-- Index for name+version lookups
CREATE INDEX idx_prompt_name_version ON ai.prompt_versions(prompt_name, version);

COMMENT ON TABLE ai.prompt_versions IS 
    'Versioned prompt registry. Every prompt change creates a new row. '
    'Prompts are immutable once created. Only status field is updatable.';
```

## 4.2 Prompt Registry API

The Prompt Registry exposes a gRPC/REST API for runtime prompt retrieval:

```protobuf
service PromptRegistry {
    // Get the active version of a prompt
    rpc GetActivePrompt(GetActivePromptRequest) returns (PromptVersion);
    
    // Get a specific version
    rpc GetPromptVersion(GetPromptVersionRequest) returns (PromptVersion);
    
    // List versions of a prompt
    rpc ListPromptVersions(ListPromptVersionsRequest) returns (ListPromptVersionsResponse);
    
    // Create a new prompt version
    rpc CreatePromptVersion(CreatePromptVersionRequest) returns (PromptVersion);
    
    // Update prompt status (lifecycle transition)
    rpc UpdatePromptStatus(UpdatePromptStatusRequest) returns (PromptVersion);
}

message PromptVersion {
    string id = 1;
    string prompt_name = 2;
    string version = 3;
    string system_prompt = 4;
    string user_prompt_template = 5;
    string output_schema_json = 6;
    repeated FewShotExample few_shot_examples = 7;
    string default_model = 8;
    float default_temperature = 9;
    int32 default_max_tokens = 10;
    string status = 11;
    string content_hash = 12;
    string change_reason = 13;
    string created_at = 14;
}
```

## 4.3 Runtime Resolution Strategy

When a worker needs a prompt, it resolves using this priority:

```
1. Explicit version pin (if specified in job config):
   SELECT * FROM ai.prompt_versions
   WHERE prompt_name = 'story_canonicalization'
     AND version = '1.2.3';

2. Active version (if no version specified):
   SELECT * FROM ai.prompt_versions
   WHERE prompt_name = 'story_canonicalization'
     AND is_active = true;

3. Default version (fallback):
   SELECT * FROM ai.prompt_versions
   WHERE prompt_name = 'story_canonicalization'
   ORDER BY created_at DESC LIMIT 1;
```

---

# 5. Prompt Lifecycle

## 5.1 Lifecycle States

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
| **DRAFT** | Prompt is being authored, not yet ready for review | No | Yes |
| **REVIEW** | Prompt submitted for review, awaiting approval | No | No |
| **APPROVED** | Reviewed and approved, ready for deployment | No | No |
| **ACTIVE** | Currently deployed in production, serving live traffic | Yes | No |
| **DEPRECATED** | Replaced by a newer version, still available for pinned jobs | Yes (pinned) | No |
| **ARCHIVED** | No longer available, removed from runtime lookups | No | No |

## 5.2 Transitions

| From | To | Trigger | Required Role | Conditions |
|------|----|---------|---------------|-----------|
| DRAFT | REVIEW | Submit for review | Author | Golden dataset tests pass |
| REVIEW | APPROVED | Approve | Prompt Reviewer | All evaluation metrics meet thresholds |
| REVIEW | DRAFT | Request changes | Reviewer | Review notes provided |
| APPROVED | ACTIVE | Deploy to production | Platform Engineer | Canary test passes |
| ACTIVE | DEPRECATED | New version activated | System (automatic) | Newer version promoted to ACTIVE |
| ACTIVE | ARCHIVED | Force archive | Admin | Emergency removal |
| DEPRECATED | ARCHIVED | Auto-archive | System | 90 days since deprecation |

## 5.3 State Machine Implementation

```python
class PromptLifecycle:
    VALID_TRANSITIONS = {
        'draft': ['review'],
        'review': ['approved', 'draft'],
        'approved': ['active', 'draft'],
        'active': ['deprecated', 'archived'],
        'deprecated': ['archived'],
        'archived': [],  # Terminal state
    }
    
    @classmethod
    def transition(cls, prompt_id: UUID, to_status: str, actor: str, reason: str):
        current = get_prompt_status(prompt_id)
        
        if to_status not in cls.VALID_TRANSITIONS.get(current, []):
            raise InvalidTransitionError(
                f"Cannot transition from {current} to {to_status}"
            )
        
        # Execute transition
        update_prompt_status(prompt_id, to_status)
        
        # When activating, deprecate the previous active version
        if to_status == 'active':
            deactivate_current_active(prompt_id)
        
        # Log audit
        log_audit(
            action='prompt_status_change',
            prompt_id=prompt_id,
            from_status=current,
            to_status=to_status,
            actor=actor,
            reason=reason
        )
```

## 5.4 Responsibilities by Role

| Role | Responsibilities |
|------|-----------------|
| **Prompt Author** | Creates drafts, writes prompt content, runs initial tests |
| **Prompt Reviewer** | Reviews prompts for quality, safety, completeness; approves/rejects |
| **Platform Engineer** | Deploys approved prompts to production, monitors rollout |
| **Domain Expert** | Validates cultural accuracy of prompts (Indonesian folklore expertise) |
| **ML Engineer** | Evaluates prompt performance metrics, recommends improvements |

## 5.5 Coexistence Window

When a new prompt version is activated, the previous ACTIVE version transitions to DEPRECATED but remains available for 90 days. This ensures:
- In-flight jobs pinned to the old version complete without changes.
- Consumers have time to migrate if they explicitly reference the old version.
- Emergency rollback is possible.

---

# 6. Prompt Storage Strategy

## 6.1 Recommended: Hybrid Architecture

The recommended architecture uses **Git as source of truth** with **PostgreSQL as the runtime registry**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      GIT REPOSITORY (Source of Truth)                │
│                                                                      │
│  ai-platform/shared/src/ai_shared/prompts.py                         │
│    → story_canonicalization (system + user prompt)                   │
│    → knowledge_normalization (system + user prompt)                  │
│    → knowledge_validation (system + user prompt)                     │
│    → narrative_article (system + user prompt)                        │
│    → ...                                                             │
│                                                                      │
│  ai-platform/extraction-service/schemas/prompts/                     │
│    → story-extraction-v1.json (JSON Schema for output)               │
│    → theme-extraction-v1.json                                        │
│    → ...                                                             │
│                                                                      │
│  ai-platform/prompt-registry/tests/                                  │
│    → golden-dataset/ (test cases)                                    │
│    → evaluations/ (historical eval results)                          │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          │ CI/CD: lint → test → evaluate → register
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL (Runtime Registry)                     │
│                                                                      │
│  ai.prompt_versions → runtime lookups                                │
│  ai.prompt_tests → test results                                      │
│  ai.prompt_evaluations → evaluation metrics                          │
│  ai.prompt_audit_log → change history                                │
└─────────────────────────────────────────────────────────────────────┘
```

## 6.2 Git Repository Structure

```
ai-platform/
├── shared/
│   └── src/
│       └── ai_shared/
│           ├── prompts.py                    # All prompt templates as Python constants
│           └── schemas/
│               ├── story-canonicalization-schema.json
│               ├── knowledge-extraction-schema.json
│               └── article-response-schema.json
├── prompt-registry/
│   ├── tests/
│   │   ├── golden-dataset/
│   │   │   ├── story-extraction/
│   │   │   │   ├── test-case-001.json
│   │   │   │   ├── test-case-002.json
│   │   │   │   └── expected/
│   │   │   │       ├── test-case-001-expected.json
│   │   │   │       └── test-case-002-expected.json
│   │   │   ├── knowledge-normalization/
│   │   │   └── article-generation/
│   │   └── regression/
│   │       └── nightly-baseline.json
│   ├── evaluations/
│   │   ├── story-canonicalization-v1.0.0.json
│   │   └── story-canonicalization-v1.1.0.json
│   └── migrations/
│       ├── 001_create_prompt_registry.sql
│       └── 002_insert_initial_prompts.sql
└── scripts/
    ├── register_prompts.py                  # CI/CD: Git → PostgreSQL sync
    ├── evaluate_prompt.py                   # Run golden dataset evaluation
    └── rollback_prompt.py                   # Emergency rollback tool
```

## 6.3 Git → Database Sync Process

The sync process (in CI/CD) registers prompts from Git into the database:

```python
def sync_prompts_to_registry():
    """Read prompts from prompts.py and register in database."""
    from ai_shared.prompts import PROMPT_REGISTRY
    
    for prompt_name, prompt_data in PROMPT_REGISTRY.items():
        content_hash = sha256(prompt_data['system_prompt'] + prompt_data['user_prompt_template'])
        
        # Check if this exact content already exists
        existing = db.fetchone(
            "SELECT id, version FROM ai.prompt_versions "
            "WHERE prompt_name = $1 AND content_hash = $2",
            prompt_name, content_hash
        )
        
        if existing:
            continue  # Already registered, skip
        
        # Auto-increment version based on git history
        new_version = determine_version(prompt_name, content_hash)
        
        # Insert new version
        db.execute("""
            INSERT INTO ai.prompt_versions
            (prompt_name, version, system_prompt, user_prompt_template, 
             output_schema, content_hash, status, owner, author, change_reason)
            VALUES ($1, $2, $3, $4, $5, $6, 'draft', $7, $8, $9)
        """, prompt_name, new_version, prompt_data['system_prompt'],
            prompt_data['user_prompt_template'], prompt_data['output_schema'],
            content_hash, prompt_data['owner'], prompt_data['author'],
            prompt_data['change_reason'])
```

## 6.4 Version Determination

```python
def determine_version(prompt_name: str, content_hash: str) -> str:
    """Auto-determine version based on git history and semantic analysis."""
    # Get the current ACTIVE version
    current = db.fetchone(
        "SELECT version FROM ai.prompt_versions "
        "WHERE prompt_name = $1 AND is_active = true",
        prompt_name
    )
    
    if not current:
        return "1.0.0"
    
    # Check git log for the prompt file changes
    git_log = run_git_log(f"ai-platform/shared/src/ai_shared/prompts.py")
    
    # Analyze change type based on commit message convention:
    #   MAJOR: "BREAKING:" or "schema:" prefix
    #   MINOR: "feat:" or "add:" prefix  
    #   PATCH: "fix:" "docs:" "refactor:" prefix
    last_commit = git_log[0]
    
    if last_commit.startswith("BREAKING") or last_commit.startswith("schema"):
        return increment_major(current.version)
    elif last_commit.startswith("feat") or last_commit.startswith("add"):
        return increment_minor(current.version)
    else:
        return increment_patch(current.version)
```

## 6.5 Alternative: Database-Only Strategy

For teams without Git-based workflows, a database-only strategy is acceptable but NOT RECOMMENDED for production.

**Minimum requirements for DB-only:**
1. Every prompt change is an INSERT (never UPDATE existing rows).
2. Trigger-based content_hash enforcement.
3. Audit log for all changes.
4. Regular database backups for recovery.

---

# 7. Prompt Testing Framework

## 7.1 Golden Dataset

The golden dataset is a curated collection of test cases with known-correct expected outputs.

**Dataset structure:**
```
prompt-registry/
└── tests/
    └── golden-dataset/
        ├── story-extraction/
        │   ├── test-case-001.json   # Standard interview transcript
        │   ├── test-case-002.json   # Multiple speakers, contradictions
        │   ├── test-case-003.json   # Single witness, low audio quality
        │   ├── test-case-004.json   # Empty transcript (edge case)
        │   ├── test-case-005.json   # Non-Indonesian language
        │   └── expected/
        │       ├── test-case-001-expected.json
        │       ├── test-case-002-expected.json
        │       └── ...
        ├── knowledge-extraction/
        │   ├── test-case-001.json
        │   └── ...
        └── article-generation/
            ├── test-case-001.json
            └── ...
```

**Test case format:**
```json
{
  "testCaseId": "story-extraction-001",
  "description": "Standard interview transcript with clear narrative",
  "promptName": "story_canonicalization",
  "input": {
    "transcript": "Full transcript text here...",
    "metadata": {
      "title": "Misteri Kuntilanak di Desa Sukamaju",
      "language": "id"
    }
  },
  "expectedOutput": {
    "storyTitle": "Penampakan Kuntilanak di Pemakaman Desa Sukamaju",
    "storySummary": "Pak Sariman menceritakan pengalamannya...",
    "keyEvents": [
      {"description": "Pulang dari sawah jam 11 malam"},
      {"description": "Melihat sosok perempuan berambut panjang"}
    ]
  },
  "metrics": {
    "minimumAccuracy": 0.85,
    "maximumHallucinationRate": 0.05
  },
  "tags": ["smoke", "regression", "indonesian"]
}
```

## 7.2 Testing Pipeline

```
                          ┌─────────────────────┐
                          │  Prompt Version     │
                          │  (DRAFT status)     │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │  Golden Dataset     │
                          │  Execution          │
                          └──────────┬──────────┘
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
              ┌──────────────────┐    ┌──────────────────┐
              │ Structure Check  │    │ Content Check    │
              │ - Valid JSON?    │    │ - Semantic       │
              │ - Schema match?  │    │   similarity     │
              │ - Types correct? │    │ - Hallucination  │
              └──────────┬───────┘    │   detection      │
                         │            │ - Completeness   │
                         │            └────────┬─────────┘
                         ▼                     ▼
              ┌─────────────────────────────────────┐
              │  Metrics Calculation                  │
              │  accuracy, hallucination_rate,        │
              │  completeness, cost, latency          │
              └──────────────────┬──────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
           ┌──────────────┐          ┌──────────────┐
           │ All metrics  │          │ Metrics      │
           │ pass?        │          │ fail?        │
           └──────┬───────┘          └──────┬───────┘
                  │                         │
                  ▼                         ▼
           ┌──────────────┐          ┌──────────────┐
           │ Status:      │          │ Status:      │
           │ REVIEW       │          │ DRAFT + flag │
           └──────────────┘          └──────────────┘
```

## 7.3 Regression Testing

Regression testing runs ALL golden dataset cases against the new prompt version and compares against the previous ACTIVE version's results.

```python
def run_regression_test(prompt_name: str, new_version: str) -> RegressionReport:
    current_active = get_active_version(prompt_name)
    test_cases = load_golden_dataset(prompt_name)
    
    results = []
    for test_case in test_cases:
        # Run with new version
        new_output = execute_prompt(new_version, test_case.input)
        new_metrics = calculate_metrics(new_output, test_case.expected_output)
        
        # Run with current active version (baseline)
        old_output = execute_prompt(current_active.version, test_case.input)
        old_metrics = calculate_metrics(old_output, test_case.expected_output)
        
        results.append({
            'test_case': test_case.testCaseId,
            'new_accuracy': new_metrics.accuracy,
            'old_accuracy': old_metrics.accuracy,
            'accuracy_delta': new_metrics.accuracy - old_metrics.accuracy,
            'new_hallucination_rate': new_metrics.hallucination_rate,
            'old_hallucination_rate': old_metrics.hallucination_rate,
            'passed': new_metrics.accuracy >= test_case.minimumAccuracy
        })
    
    # Aggregate
    passed = all(r['passed'] for r in results)
    avg_accuracy_delta = sum(r['accuracy_delta'] for r in results) / len(results)
    
    return RegressionReport(
        prompt_name=prompt_name,
        new_version=new_version,
        old_version=current_active.version,
        results=results,
        passed=passed,
        avg_accuracy_delta=avg_accuracy_delta,
        regression_detected=avg_accuracy_delta < -0.05  # 5% drop = regression
    )
```

## 7.4 Quality Scoring

Each prompt version receives a quality score that determines whether it can proceed to deployment.

```python
def calculate_quality_score(metrics: dict) -> float:
    """
    Weighted quality score (0.0 - 1.0).
    Higher score = better quality.
    """
    weights = {
        'accuracy': 0.40,
        'completeness': 0.20,
        'hallucination_rate': 0.20,  # inverted (low = good)
        'consistency': 0.10,
        'cost_efficiency': 0.10,
    }
    
    score = 0.0
    score += metrics['accuracy'] * weights['accuracy']
    score += metrics['completeness'] * weights['completeness']
    score += (1.0 - metrics['hallucination_rate']) * weights['hallucination_rate']
    score += metrics['consistency'] * weights['consistency']
    score += metrics['cost_efficiency'] * weights['cost_efficiency']
    
    return round(score, 4)
```

## 7.5 Human Review

In addition to automated testing, every prompt must undergo human review before deployment:

**Checklist for reviewers:**
- [ ] Output schema is valid and complete
- [ ] No hallucination-inducing language
- [ ] Cultural nuance preserved (domain expert sign-off required for Indonesian folklore prompts)
- [ ] Instructions are unambiguous
- [ ] Few-shot examples are representative and correct
- [ ] Temperature setting is appropriate for the task
- [ ] Security: no prompt injection vulnerabilities
- [ ] No PII or sensitive data in few-shot examples
- [ ] All edge cases considered (empty input, non-Indonesian, etc.)

---

# 8. Prompt Evaluation Metrics

## 8.1 Metric Definitions

| Metric | Definition | Measurement | Target | Weight |
|--------|-----------|-------------|--------|--------|
| **Accuracy** | Fraction of outputs matching expected golden dataset values | Exact match + semantic similarity (cosine > 0.9) | ≥ 0.85 | 0.40 |
| **Completeness** | Fraction of required fields populated | null field count / total required fields | ≥ 0.90 | 0.20 |
| **Hallucination Rate** | Fraction of extracted claims not supported by input evidence | Provenance check against source transcript | ≤ 0.05 | 0.20 |
| **Consistency** | Variance in output for identical inputs across 3 runs | Standard deviation of quality scores | ≤ 0.10 | 0.10 |
| **Cost Efficiency** | Token usage relative to baseline | (baseline_tokens / actual_tokens) | ≥ 0.80 | 0.05 |
| **Latency** | 95th percentile response time | P95 of execution time | ≤ 30s | 0.05 |

## 8.2 Metric Collection

All metrics are collected at runtime and stored for analysis:

```sql
CREATE TABLE ai.prompt_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_name VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    
    -- Test results
    golden_dataset_size INTEGER NOT NULL,
    tests_passed INTEGER NOT NULL,
    tests_failed INTEGER NOT NULL,
    
    -- Metrics
    accuracy DECIMAL(6,4),
    completeness DECIMAL(6,4),
    hallucination_rate DECIMAL(6,4),
    consistency DECIMAL(6,4),
    cost_efficiency DECIMAL(6,4),
    latency_p50_ms INTEGER,
    latency_p95_ms INTEGER,
    latency_p99_ms INTEGER,
    
    -- Cost
    total_input_tokens INTEGER,
    total_output_tokens INTEGER,
    total_cost DECIMAL(10,6),
    avg_cost_per_call DECIMAL(10,6),
    
    -- Quality
    quality_score DECIMAL(6,4),
    
    -- Metadata
    model_used VARCHAR(100),
    evaluation_type VARCHAR(50),  -- golden_dataset, regression, canary, production
    passed_threshold BOOLEAN,
    regression_detected BOOLEAN,
    run_by VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_prompt_eval_name_ver 
    ON ai.prompt_evaluations(prompt_name, prompt_version);
CREATE INDEX idx_prompt_eval_score 
    ON ai.prompt_evaluations(quality_score DESC);
```

## 8.3 Production Monitoring

Metrics collected from production traffic provide continuous quality monitoring:

```sql
-- Track quality score over time per prompt version
SELECT 
    prompt_version,
    AVG(quality_score) as avg_quality,
    COUNT(*) as total_calls,
    MIN(quality_score) as min_quality,
    MAX(quality_score) as max_quality
FROM ai.extraction_runs
WHERE prompt_name = 'story_canonicalization'
  AND created_at > now() - interval '7 days'
GROUP BY prompt_version
ORDER BY prompt_version;
```

**Alert thresholds:**
- Quality score drops > 5% compared to rolling 7-day average → alert
- Hallucination rate exceeds 10% in any 1-hour window → alert
- Average token usage increases > 50% compared to baseline → alert

## 8.4 Evaluation Dashboard (Grafana)

```
Panel: Prompt Quality Score (by version)
  - Query: quality_score over time, grouped by prompt_version
  - Alert: quality_score < 0.75 for > 1 hour

Panel: Hallucination Rate (by prompt)
  - Query: hallucination_rate over time
  - Alert: hallucination_rate > 0.10

Panel: Token Usage (by prompt version)
  - Query: avg input + output tokens per call
  - Compare: new version vs previous version

Panel: Cost per Extraction
  - Query: avg_cost_per_call by prompt_version
  - Compare: cost efficiency across versions

Panel: Latency (P95)
  - Query: latency_p95_ms over time
  - Alert: latency_p95 > 30s
```

---

# 9. Prompt Deployment Strategy

## 9.1 Deployment Process

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  DRAFT   │───►│  REVIEW  │───►│ APPROVED │───►│  ACTIVE  │───►│MONITORING│
│  Author  │    │ Reviewer │    │ Ready    │    │  Canary  │    │ 7 Days   │
└──────────┘    └──────────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
                                     │                │               │
                                     │                │               │
                                     ▼                ▼               ▼
                              ┌──────────┐     ┌──────────┐    ┌──────────┐
                              │REJECTED  │     │ROLLBACK  │    │ FULL     │
                              │Back to   │     │Previous  │    │ ROLLOUT  │
                              │DRAFT     │     │Version   │    │ 100%     │
                              └──────────┘     └──────────┘    └──────────┘
```

## 9.2 Safe Rollout Strategy

**Phase 1: Shadow Mode (0% traffic, data collection only)**
- Prompt is deployed in parallel with the current ACTIVE version.
- Both prompts process the same inputs.
- Only the current ACTIVE prompt's output is used.
- Comparison metrics are collected.
- Duration: 24 hours minimum.

**Phase 2: Canary (5% traffic)**
- 5% of new jobs use the new prompt version.
- Compare metrics: quality score, hallucination rate, cost, latency.
- Automatic rollback if any metric degrades > 5%.
- Duration: 4 hours minimum (ideally 24 hours).

**Phase 3: Ramp (25% → 50% → 100%)**
- Gradual traffic increase with metric verification at each step.
- Each step: minimum 2 hours monitoring.
- Full rollout: minimum 72 hours after canary.

**Phase 4: Full Rollout**
- 100% of new jobs use the new prompt version.
- Previous version transitions to DEPRECATED.
- 90-day coexistence window for pinned jobs.

## 9.3 Canary Implementation

```python
def resolve_prompt_version(prompt_name: str, job_config: dict) -> str:
    """Resolve which prompt version to use, supporting canary deployments."""
    
    # 1. Explicit override in job config (for testing)
    if job_config.get('prompt_version'):
        return job_config['prompt_version']
    
    # 2. Canary selection based on percentage
    active_version = get_active_version(prompt_name)
    canary_version = get_canary_version(prompt_name)
    
    if canary_version and should_route_to_canary(canary_version.canary_percentage):
        return canary_version.version
    
    # 3. Default to active
    return active_version.version


def should_route_to_canary(percentage: float) -> bool:
    """Deterministic canary routing based on hash of job ID."""
    job_id = get_current_job_id()
    hash_val = int(hashlib.md5(str(job_id).encode()).hexdigest(), 16)
    return (hash_val % 100) < (percentage * 100)
```

## 9.4 Version Pinning

Jobs can pin a specific prompt version for reproducibility:

```json
{
  "jobId": "e5f6a7b8-c901-2def-3456-789012345678",
  "jobType": "story_extraction",
  "promptVersion": "1.2.3",          // Pinned version
  "extractionConfig": {
    "model": "gemini-2.5-pro",
    "temperature": 0.3
  }
}
```

**Rules:**
- Pinned versions must be in ACTIVE or DEPRECATED status.
- ARCHIVED versions cannot be pinned.
- Pinning to a non-existent version falls back to ACTIVE with a warning.

## 9.5 Rollback Procedure

```bash
# Emergency rollback to previous version
ai-cli prompts rollback --prompt story_canonicalization --version 1.2.2

# Rollback with reason
ai-cli prompts rollback \
  --prompt story_canonicalization \
  --version 1.2.2 \
  --reason "Quality score dropped from 0.88 to 0.72"

# Dry run (show impact without executing)
ai-cli prompts rollback \
  --prompt story_canonicalization \
  --version 1.2.2 \
  --dry-run

# Output:
# Current active: 1.3.0 (canary: 10%)
# Target: 1.2.2 (previously active, status: deprecated)
# Impact: All new jobs will use 1.2.2 instead of 1.3.0
# In-flight jobs: 3 jobs pinned to 1.3.0 will continue
```

---

# 10. Audit Requirements

## 10.1 Audit Log Schema

```sql
CREATE TABLE ai.prompt_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL,                    -- FK to ai.prompt_versions
    prompt_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    
    -- What changed
    action VARCHAR(50) NOT NULL,
        -- created, status_changed, content_updated, deployed,
        -- rolled_back, tested, evaluated, archived
    
    -- Who
    actor_type VARCHAR(50) NOT NULL,             -- user, system, ci_cd
    actor_id UUID,                               -- user ID if user action
    actor_name VARCHAR(255) NOT NULL,            -- username or system name
    
    -- Why
    reason TEXT NOT NULL,
    change_summary TEXT,                         -- human-readable summary of changes
    
    -- Previous state (for rollback tracking)
    previous_version VARCHAR(50),
    previous_status VARCHAR(50),
    
    -- Metadata
    metadata JSONB NOT NULL DEFAULT '{}',
    correlation_id UUID,                         -- links to deployment pipeline run
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_prompt_audit_name ON ai.prompt_audit_log(prompt_name, version);
CREATE INDEX idx_prompt_audit_time ON ai.prompt_audit_log(created_at DESC);
CREATE INDEX idx_prompt_audit_actor ON ai.prompt_audit_log(actor_name);
```

## 10.2 Audit Requirements

| Requirement | Implementation |
|-------------|---------------|
| **Who changed the prompt** | `actor_name` + `actor_id` in audit log |
| **When it changed** | `created_at` timestamp |
| **Why it changed** | `reason` field (required, non-empty enforced) |
| **What changed** | `change_summary` + full version content stored in `ai.prompt_versions` |
| **Before/after comparison** | `previous_version` + `previous_status` in audit log |
| **Approval history** | Audit log entries for `review→approved` transitions with reviewer identity |
| **Deployment history** | Audit log entries for `approved→active` transitions with deployment metadata |

## 10.3 Audit Queries

```sql
-- Get full history of a prompt
SELECT action, actor_name, reason, created_at
FROM ai.prompt_audit_log
WHERE prompt_name = 'story_canonicalization'
ORDER BY created_at DESC;

-- Who approved the current active version?
SELECT pg.prompt_name, pg.version, al.actor_name AS approved_by, al.created_at AS approved_at
FROM ai.prompt_versions pg
JOIN ai.prompt_audit_log al 
    ON al.prompt_id = pg.id AND al.action = 'status_changed' AND al.metadata->>'to_status' = 'approved'
WHERE pg.prompt_name = 'story_canonicalization' AND pg.is_active = true;

-- All rollbacks in the last 30 days
SELECT prompt_name, version, previous_version, actor_name, reason, created_at
FROM ai.prompt_audit_log
WHERE action = 'rolled_back'
  AND created_at > now() - interval '30 days'
ORDER BY created_at DESC;

-- Deployment frequency per prompt
SELECT prompt_name, COUNT(*) as deployments
FROM ai.prompt_audit_log
WHERE action = 'deployed'
  AND created_at > now() - interval '30 days'
GROUP BY prompt_name
ORDER BY deployments DESC;
```

## 10.4 Traceability from Extraction to Prompt

Every extraction run records the prompt version used:

```sql
SELECT 
    er.extraction_id,
    er.created_at,
    er.prompt_name,
    er.prompt_version,
    pv.status AS prompt_status,
    pv.content_hash,
    al.actor_name AS prompt_author,
    al.created_at AS prompt_created_at
FROM ai.extraction_runs er
JOIN ai.prompt_versions pv 
    ON pv.prompt_name = er.prompt_name AND pv.version = er.prompt_version
JOIN ai.prompt_audit_log al 
    ON al.prompt_id = pv.id AND al.action = 'created'
WHERE er.extraction_id = '...';
```

This query answers: "Which prompt version produced this extraction, who wrote it, when was it created, and what was its content hash?"

---

# 11. Future Compatibility

## 11.1 Multi-Model Support

The prompt registry already supports multi-model deployment via the `default_model` field. Future enhancements:

```sql
ALTER TABLE ai.prompt_versions ADD COLUMN model_configs JSONB NOT NULL DEFAULT '[]';
```

**Model configuration per prompt:**
```json
{
  "modelConfigs": [
    {
      "model": "gemini-2.5-pro",
      "temperature": 0.3,
      "maxTokens": 8192,
      "priority": 1
    },
    {
      "model": "claude-sonnet-4",
      "temperature": 0.3,
      "maxTokens": 8192,
      "priority": 2
    },
    {
      "model": "gpt-4o",
      "temperature": 0.3,
      "maxTokens": 8192, 
      "priority": 3
    }
  ]
}
```

**Model selection at runtime:**
```python
def select_model(prompt_version: dict, provider_status: dict) -> str:
    """Select the best available model based on priority and availability."""
    models = sorted(prompt_version['model_configs'], key=lambda x: x['priority'])
    
    for model_config in models:
        model = model_config['model']
        if provider_status.get(model, {}).get('available', False):
            return model
    
    # Fallback to any available model
    return provider_status.get_first_available()
```

## 11.2 Fine-Tuning Compatibility

When models are fine-tuned, prompts shift from the runtime layer to the training data layer.

**Architecture for fine-tuned models:**
```
Current (prompt-based):    Prompt + Input → Model → Output
Future (fine-tuned):       Input → Fine-Tuned Model → Output
```

The prompt registry supports this transition by storing:
- **Training datasets** linked to prompt versions that were used to generate them.
- **Fine-tuned model identifiers** with lineage back to source prompts.
- **Evaluation comparisons** between prompt-based vs fine-tuned outputs.

```sql
-- Future table for fine-tuning lineage
CREATE TABLE ai.fine_tuned_models (
    model_id UUID PRIMARY KEY,
    model_name VARCHAR(200) NOT NULL,
    base_model VARCHAR(100) NOT NULL,
    training_prompt_version UUID REFERENCES ai.prompt_versions(id),
    training_data_query TEXT,
    training_date TIMESTAMPTZ NOT NULL,
    evaluation_results JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'training'
);
```

## 11.3 Prompt Chaining

Complex extraction workflows will chain multiple prompts together. The registry must support chain definitions:

```json
{
  "chainName": "complete_extraction_pipeline",
  "chainVersion": "1.0.0",
  "steps": [
    {
      "step": 1,
      "promptName": "story_canonicalization",
      "version": "1.2.3",
      "inputMapping": {"transcript": "$.input.transcript"},
      "outputMapping": {"story": "$.output"}
    },
    {
      "step": 2,
      "promptName": "theme_extraction",
      "version": "2.0.1",
      "inputMapping": {"story": "$.steps[0].output"},
      "outputMapping": {"themes": "$.output"}
    },
    {
      "step": 3,
      "promptName": "entity_extraction",
      "version": "1.1.0",
      "inputMapping": {"story": "$.steps[0].output"},
      "outputMapping": {"entities": "$.output"}
    }
  ]
}
```

```sql
-- Future table for prompt chains
CREATE TABLE ai.prompt_chains (
    chain_id UUID PRIMARY KEY,
    chain_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    chain_definition JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    owner VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 11.4 Agentic Workflows

Future agent-based systems will dynamically select prompts based on context:

```
Agent receives a task → Agent analyzes task type →
  → Agent selects prompt from registry based on similarity →
  → Agent executes prompt → Agent evaluates output →
  → Agent may chain additional prompts →
  → Agent returns final result
```

The registry supports this by:
- **Tagging prompts** with semantic metadata for similarity search.
- **Recording prompt execution history** for reinforcement learning.
- **Exposing evaluation metrics** so agents can select the best prompt for a given context.

```sql
-- Future: Semantic prompt search for agentic workflows
ALTER TABLE ai.prompt_versions ADD COLUMN embedding VECTOR(1536);

-- Index for similarity search
CREATE INDEX idx_prompt_embedding ON ai.prompt_versions
    USING ivfflat (embedding vector_cosine_ops);
```

## 11.5 Migration Path

| Phase | Timeline | Capability |
|-------|----------|-----------|
| **Phase 1** | Now | Single-prompt, single-model extraction pipeline |
| **Phase 2** | Near-term | Multi-model prompt configurations, automated A/B testing |
| **Phase 3** | Mid-term | Prompt chaining, chain-level evaluation, golden dataset expansion |
| **Phase 4** | Long-term | Fine-tuned models, agentic prompt selection, reinforcement learning from feedback |

---

# References

- **ADR-009:** AI Pipeline Integration
- **PRD.md §13:** Prompt Governance (versioned, stored separately)
- **PRD.md §12:** Cost Governance (token tracking, prompt version in cost records)
- **docs/ai-platform/domain-event-catalog.md:** AI Platform Domain Event Catalog
- **docs/ai-platform/ai-pipeline-state-machine-specification.md:** AI Pipeline State Machine
- **ai-platform/shared/src/ai_shared/prompts.py:** Existing prompt template implementations
- **ai-platform/shared/src/ai_shared/canonical_pipeline.py:** Canonical pipeline prompt usage
- **ai-platform/enrichment-service/src/enrichment/infrastructure/prompt_templates.py:** Extraction prompt templates
- **ai-platform/article-service/src/article/application/service.py:** Article generation prompt usage
- **ai-platform/scripts/generate_migration_sql.py:** Existing prompt_versions table DDL
- **ai-platform/scripts/setup_database_schemas.py:** Existing prompt registration scripts