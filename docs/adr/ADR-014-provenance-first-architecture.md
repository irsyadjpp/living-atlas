# ADR-014: Provenance First Architecture — Every Knowledge Object Traceable to Source Evidence

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture preserves and structures cultural knowledge for researchers, anthropologists, journalists, and cultural preservation bodies. These users require source traceability for every knowledge artifact. A researcher citing a claim from the platform must be able to trace it back to the exact transcript segment, in the exact source material, that supports the claim. Without provenance, the platform is just another content site — with provenance, it is a research-grade knowledge base.

The platform serves multiple communities with different provenance requirements:

- **Researchers and anthropologists**: Need to verify claims against source evidence. Must be able to cite specific source passages.
- **Journalists and writers**: Need to fact-check AI-generated content against original sources.
- **Editors and reviewers**: Need to validate that AI-extracted claims are grounded in evidence before approval.
- **Cultural preservation bodies**: Need to ensure that cultural knowledge is accurately attributed to its source communities.
- **General readers**: Need confidence that published content is evidence-based, not AI-invented.

The PRD states: "Every knowledge object must be traceable. Knowledge Object → Claim → Evidence → Transcript Segment → Transcript → Source." (Backend Platform PRD §3.5)

## Technical Context

The platform already has foundational provenance infrastructure:

1. **ADR-007 (Canonical Story Core Contract)**: Every Canonical Story includes a `provenance` object with `sourceId`, `transcriptId`, `extractionJobId`, `promptVersion`, and `modelUsed`. Every entity, claim, belief, and motif includes `evidence` array referencing source transcript segments.

2. **ADR-008 (Immutable Versioning)**: All content is versioned. No overwrites. Every version is preserved, enabling temporal provenance queries.

3. **ADR-013 (Human Review Required)**: Every review decision is logged with reviewer identity, timestamp, and reason. Review history is part of the provenance chain.

4. **Existing Lineage entity**: The codebase has a `Lineage` entity in the identity service that tracks cross-entity relationships:

```java
@Entity
@Table(name = "lineage", schema = "identity")
public class Lineage {
    private UUID objectId;
    private String objectType;
    private UUID parentObjectId;
    private String parentObjectType;
    private String relationshipType;
    private String description;
    private UUID tenantId;
    private OffsetDateTime createdAt;
}
```

5. **Audit requirements**: Every business table contains `created_at`, `created_by`, `updated_at`, `updated_by`, `deleted_at`, `deleted_by`, `version`, `tenant_id`, `workspace_id`.

## Constraints

1. **Complete traceability**: Every knowledge artifact must be traceable to its source evidence. The chain must be complete — no broken links.

2. **Provenance is structural, not optional**: Provenance is not metadata that can be omitted. It is a structural requirement enforced by the Canonical Story schema (ADR-007 Rule 7).

3. **Immutable source material**: Sources and transcripts must never be deleted. They are the foundation of the provenance chain.

4. **AI-generated vs human-generated distinction**: Users must be able to distinguish AI-generated content from human-authored content. Every artifact must declare its generation method.

5. **Contradiction preservation**: Conflicting claims from different sources must be preserved, not resolved. Both sides of a contradiction must be traceable to their respective sources.

6. **Cross-entity lineage**: Knowledge objects, claims, stories, and articles have complex relationships. The lineage system must track these relationships bidirectionally.

7. **Scalability**: At 100,000 stories, 1,000,000 knowledge objects, and 10,000,000 transcript segments, the provenance system must not become a bottleneck.

8. **Research citation**: Researchers must be able to export provenance information for citations. The provenance chain should support academic citation formats.

## Problem Statement

Every knowledge object in the platform must be traceable to its source evidence. The provenance chain spans multiple systems: source materials (videos, podcasts, documents), transcripts, AI-extracted canonical stories, knowledge objects, claims, articles, and human review decisions. The provenance must distinguish AI-generated from human-generated content, preserve contradictions with their source attributions, and support research citation. How do we design a provenance architecture that enforces complete traceability from source to published artifact, integrates with the existing Canonical Story schema, lineage entity, immutable versioning, and review infrastructure, and scales to 100,000+ stories and 1,000,000+ knowledge objects?

# Decision

**Every knowledge object is traceable to its source evidence through a complete, immutable provenance chain. The chain is: Knowledge Object → Claim → Evidence → Transcript Segment → Transcript → Source. Provenance is structurally enforced by the Canonical Story schema, extended by the lineage table for cross-entity relationships, and supported by immutable versioning for temporal queries. Every artifact declares its generation method (AI-extracted, human-authored, system-generated). Contradictions are preserved with dual provenance chains. AI extraction metadata (model, prompt version, confidence) is recorded at every level.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE PROVENANCE CHAIN                              │
│                                                                          │
│  Level 0: Source                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  content_sources                                                   │   │
│  │  ├── id: UUID (stable, immutable)                                  │   │
│  │  ├── source_type: 'youtube_video' | 'podcast' | 'document' | ...  │   │
│  │  ├── title, url, author, published_date                            │   │
│  │  ├── channel, episode, duration                                    │   │
│  │  ├── metadata (JSONB): language, region, topic tags                │   │
│  │  └── created_at, created_by (immutable after creation)             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           │ 1:N (one source can have multiple transcripts)              │
│           ▼                                                              │
│  Level 1: Transcript                                                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  content_transcripts                                              │   │
│  │  ├── id: UUID                                                     │   │
│  │  ├── source_id: UUID → content_sources.id                         │   │
│  │  ├── language, duration, speaker_count                            │   │
│  │  ├── text: TEXT (full transcript)                                  │   │
│  │  ├── segments: JSONB (segments with timestamps, speakers)          │   │
│  │  ├── version: INTEGER                                             │   │
│  │  └── created_at, created_by                                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           │ 1:N (one transcript → many segments)                        │
│           ▼                                                              │
│  Level 2: Transcript Segment                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  (stored as JSONB array in content_transcripts.segments)           │   │
│  │  ├── segment_index: INTEGER                                        │   │
│  │  ├── text: TEXT                                                     │   │
│  │  ├── start_time: FLOAT (seconds)                                   │   │
│  │  ├── end_time: FLOAT                                               │   │
│  │  └── speaker: STRING (speaker name or identifier)                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           │ N:M (many evidence refs per claim, many claims per segment) │
│           ▼                                                              │
│  Level 3: Claim / Knowledge Object / Entity                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Canonical Story (JSONB in ai_output_canonical_stories)           │   │
│  │  ├── entities[].evidence[]: [{ segmentIndex, text, startTime,    │   │
│  │  │                                endTime, speaker }]             │   │
│  │  ├── claims[].evidence[]: [{ segmentIndex, text, ... }]           │   │
│  │  ├── beliefs[].evidence[]: [{ segmentIndex, text, ... }]          │   │
│  │  ├── themes[].evidence[]: [{ segmentIndex, text, ... }]           │   │
│  │  └── provenance: { sourceId, transcriptId, extractionJobId,       │   │
│  │                    promptVersion, modelUsed, extractedAt }         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│           │                                                              │
│           │ 1:N (one story → many derived artifacts)                    │
│           ▼                                                              │
│  Level 4: Derived Artifacts                                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Knowledge Objects (knowledge_objects)                            │   │
│  │  ├── provenance: { canonical_story_id, extraction_method,         │   │
│  │  │                model_version, confidence }                     │   │
│  │                                                                    │   │
│  │  Articles (content_articles)                                       │   │
│  │  ├── provenance: { source_story_id, generation_method,            │   │
│  │  │                prompt_version, model_used, reviewer }          │   │
│  │                                                                    │   │
│  │  Graph Projections (Neo4j)                                         │   │
│  │  ├── Each node carries: { version, source_id, projected_at }      │   │
│  │                                                                    │   │
│  │  Vector Embeddings (Weaviate)                                      │   │
│  │  ├── Each object carries: { source_id, embedding_model,           │   │
│  │  │                          content_version }                     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    LINEAGE TABLE (Cross-Entity Tracking)           │   │
│  │                                                                   │   │
│  │  Tracks any relationship between any two entities:                │   │
│  │  ├── Story "A" → DERIVED_FROM → Transcript "B"                   │   │
│  │  ├── Claim "C" → EVIDENCE_FOR → KnowledgeObject "D"              │   │
│  │  ├── Article "E" → BASED_ON → Story "A"                          │   │
│  │  ├── KnowledgeObject "F" → CORRECTED_BY → KnowledgeObject "G"    │   │
│  │  │   (version chain)                                              │   │
│  │  └── Review "H" → APPROVED → Article "E"                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Five-Level Provenance Chain

Every knowledge artifact exists within a five-level provenance chain. Each level provides traceability to the level below.

```
Level 0: Source  (content_sources)
  └── Original material: YouTube video, podcast episode, document, interview
  └── Immutable: never deleted, never modified after creation
  └── ID referenced by all derived artifacts

Level 1: Transcript  (content_transcripts)
  └── Textual representation of source content
  └── Versioned: corrections create new versions, old versions preserved
  └── References: source_id → content_sources.id

Level 2: Transcript Segment  (JSONB in content_transcripts.segments)
  └── Individual segment with timestamp, speaker, and text
  └── Referenced by evidence arrays in Canonical Story
  └── Evidence reference: { segmentIndex, text, startTime, endTime, speaker }

Level 3: Canonical Story + Knowledge  (ai_output_canonical_stories)
  └── AI-extracted structured representation of the narrative
  └── Every entity, claim, belief, theme includes evidence array
  └── Provenance object at the story level

Level 4: Derived Artifacts  (knowledge_objects, content_articles)
  └── Knowledge objects, claims, articles derived from Canonical Story
  └── Each includes provenance back to the Canonical Story
```

**Enforcement**: Any artifact at Level 3 or 4 that cannot be traced to a Level 0 source is invalid. This is enforced by the Canonical Story JSON Schema validation (ADR-007 Rule 2).

### Rule 2: Provenance Is Structural, Not Metadata

Provenance is not an optional field. It is a structural requirement enforced at the schema level. Every extractable item in the Canonical Story must have evidence.

```python
# Canonical Story Schema — provenance is REQUIRED at every level
VALID_CANONICAL_STORY = {
    "canonicalStoryId": "uuid",
    "provenance": {                         # REQUIRED: story-level provenance
        "sourceId": "uuid",
        "transcriptId": "uuid",
        "extractionJobId": "uuid",
        "promptVersion": "string",
        "modelUsed": "string",
        "extractedAt": "ISO8601"
    },
    "entities": [
        {
            "entityId": "uuid",
            "name": "Kuntilanak",
            "confidence": 95,
            "evidence": [                    # REQUIRED: at least 1 evidence ref
                {
                    "segmentIndex": 2,
                    "text": "saya lihat sosok perempuan berambut panjang",
                    "startTime": 46.0,
                    "endTime": 52.3,
                    "speaker": "Pak Sariman"
                }
            ]
        }
    ],
    "claims": [
        {
            "claimId": "uuid",
            "statement": "Kuntilanak appeared at the cemetery in 2019",
            "evidence": [                    # REQUIRED: at least 1 evidence ref
                { "segmentIndex": 2, "text": "...", ... }
            ]
        }
    ]
    # beliefs[].evidence[], themes[].evidence[], motifs[].evidence[] — ALL REQUIRED
}
```

**Validation rule**: Any entity, claim, belief, theme, or motif without at least one evidence reference is rejected by schema validation. This is enforced at the extraction service output, at the knowledge extraction service input, and at the PostgreSQL CHECK constraint.

```sql
-- PostgreSQL CHECK constraint for evidence requirement
ALTER TABLE ai_output_canonical_stories
ADD CONSTRAINT canonical_story_evidence_check
CHECK (
    story_data->'entities' @? '$[*].evidence[0]'  -- Every entity has at least 1 evidence
    AND story_data->'claims' @? '$[*].evidence[0]'  -- Every claim has at least 1 evidence
    AND story_data->'beliefs' @? '$[*].evidence[0]'  -- Every belief has at least 1 evidence
);
```

### Rule 3: Generation Method Declaration

Every artifact must declare how it was generated. This distinguishes AI-generated from human-generated content.

```sql
CREATE TYPE generation_method AS ENUM (
    'ai_extracted',       -- Produced by AI extraction from transcript
    'ai_generated',       -- Produced by AI generation (articles, summaries)
    'human_created',      -- Created manually by a human user
    'human_edited',       -- Human-edited version of AI-generated content
    'system_generated',   -- Produced by system rules (normalization, aggregation)
    'imported'            -- Imported from external system
);
```

```sql
-- Every content table includes generation_method
ALTER TABLE content_stories ADD COLUMN generation_method generation_method NOT NULL;
ALTER TABLE content_articles ADD COLUMN generation_method generation_method NOT NULL;
ALTER TABLE knowledge_objects ADD COLUMN generation_method generation_method NOT NULL;
ALTER TABLE knowledge_claims ADD COLUMN generation_method generation_method NOT NULL;

-- AI-generated content also tracks the specific method
CREATE TABLE ai_generation_metadata (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference to the generated artifact
    artifact_type       VARCHAR(50) NOT NULL,  -- 'story', 'knowledge_object', 'claim', 'article'
    artifact_id         UUID NOT NULL,
    artifact_version    BIGINT NOT NULL,
    
    -- AI extraction details
    extraction_method   VARCHAR(50) NOT NULL,  -- 'canonical_story_extraction', 'knowledge_extraction',
                                               -- 'article_generation', 'embedding_generation'
    model_provider      VARCHAR(50) NOT NULL,  -- 'gemini', 'claude', 'openai'
    model_name          VARCHAR(100) NOT NULL,
    prompt_version      VARCHAR(50) NOT NULL,
    prompt_name         VARCHAR(100) NOT NULL,
    
    -- Provenance
    source_canonical_story_id UUID,            -- Which Canonical Story this was derived from
    extraction_job_id   UUID NOT NULL,
    
    -- Confidence
    confidence_score    DECIMAL(5,2),
    
    -- Timing
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(artifact_type, artifact_id, artifact_version)
);
```

**UI display**: The generation method is displayed to users in the UI:
- "AI-extracted from [source]" for AI-generated content
- "Written by [author name]" for human-created content
- "Edited by [editor name] from AI-generated draft" for human-edited AI content

### Rule 4: Lineage Table for Cross-Entity Relationships

The lineage table tracks relationships between any two entities in the system. This provides a queryable graph of provenance relationships beyond the direct chain.

```sql
CREATE TABLE provenance_lineage (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source entity
    source_type         VARCHAR(50) NOT NULL,   -- 'story', 'knowledge_object', 'claim',
                                                -- 'article', 'transcript', 'source',
                                                -- 'review_decision', 'collection'
    source_id           UUID NOT NULL,
    source_version      BIGINT,                 -- NULL if entity is not versioned
    
    -- Target entity
    target_type         VARCHAR(50) NOT NULL,
    target_id           UUID NOT NULL,
    target_version      BIGINT,
    
    -- Relationship
    relationship_type   VARCHAR(50) NOT NULL,
    -- 'derived_from'     : artifact was derived from source (e.g., article → story)
    -- 'evidence_for'     : artifact provides evidence for another (e.g., segment → claim)
    -- 'based_on'         : artifact is based on another (e.g., article → story)
    -- 'corrected_by'     : artifact was corrected by a newer version
    -- 'superseded_by'    : artifact was replaced by a newer version
    -- 'reviewed_by'      : artifact was reviewed (target is review decision)
    -- 'approved_by'      : artifact was approved (target is approval record)
    -- 'references'       : artifact references another (e.g., article → knowledge object)
    -- 'contains'         : artifact contains another (e.g., story → entity)
    -- 'contradicts'      : artifact contradicts another (e.g., claim → claim)
    
    -- Description for human readability
    description         TEXT,
    
    -- Metadata
    metadata            JSONB,                  -- Additional context (confidence, timing)
    tenant_id           UUID,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes for traversal queries
    CONSTRAINT unique_lineage UNIQUE(source_type, source_id, target_type, target_id, relationship_type)
);

CREATE INDEX idx_lineage_source ON provenance_lineage(source_type, source_id);
CREATE INDEX idx_lineage_target ON provenance_lineage(target_type, target_id);
CREATE INDEX idx_lineage_relationship ON provenance_lineage(relationship_type);
```

**Lineage queries**:

```sql
-- Forward traversal: find everything derived from a specific source
SELECT * FROM provenance_lineage
WHERE source_type = 'source' AND source_id = :sourceId
  AND relationship_type = 'derived_from';

-- Backward traversal: trace an article back to its source
SELECT pl.* FROM provenance_lineage pl
WHERE pl.target_type = 'article' AND pl.target_id = :articleId
ORDER BY pl.created_at ASC;

-- Full provenance chain for a knowledge object:
-- Knowledge Object → Canonical Story → Transcript → Source
SELECT * FROM provenance_lineage
WHERE source_type = 'knowledge_object' AND source_id = :knowledgeObjectId
UNION
SELECT * FROM provenance_lineage
WHERE target_type = 'knowledge_object' AND target_id = :knowledgeObjectId
ORDER BY created_at ASC;
```

### Rule 5: AI Extraction Metadata at Every Level

Every AI-involved step in the provenance chain records the exact AI model, prompt version, and confidence.

```python
# Canonical Story extraction metadata (stored in extractionMetadata field)
EXTRACTION_METADATA = {
    "modelUsed": "gemini-2.5-pro",
    "promptVersion": "story-canonicalization-v3",
    "promptName": "story_canonicalization",
    "inputTokens": 4502,
    "outputTokens": 1280,
    "executionCost": 0.0032,
    "executionTimeMs": 12450,
    "qualityScore": 0.88,
    "provider": "google",
}

# Entity-level AI metadata (stored per entity in Canonical Story)
ENTITY_METADATA = {
    "entityId": "uuid",
    "name": "Kuntilanak",
    "confidence": 95,                    # AI confidence score
    "extractionMethod": "ai_extracted",  # How this entity was obtained
    "normalizedBy": "ai_normalization",  # If normalized, which process
    "evidence": [                        # Source evidence
        {
            "segmentIndex": 2,
            "text": "saya lihat sosok perempuan berambut panjang",
            "startTime": 46.0,
            "endTime": 52.3,
            "speaker": "Pak Sariman"
        }
    ]
}
```

**Traceability query** — "How was this knowledge object produced?":
```sql
SELECT 
    ko.id AS knowledge_object_id,
    ko.generation_method,
    agm.model_provider,
    agm.model_name,
    agm.prompt_version,
    agm.confidence_score,
    agm.extraction_job_id,
    agm.source_canonical_story_id,
    cs.provenance->>'sourceId' AS source_id,
    cs.provenance->>'transcriptId' AS transcript_id
FROM knowledge_objects ko
LEFT JOIN ai_generation_metadata agm 
    ON agm.artifact_type = 'knowledge_object' 
    AND agm.artifact_id = ko.id
    AND agm.artifact_version = ko.version
LEFT JOIN ai_output_canonical_stories cs
    ON cs.id = agm.source_canonical_story_id
WHERE ko.id = :knowledgeObjectId;
```

### Rule 6: Contradiction Preservation with Dual Provenance

Contradictions are preserved, not resolved. Each side of a contradiction has its own provenance chain.

```sql
CREATE TABLE provenance_contradictions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- The two sides of the contradiction
    entity_a_type       VARCHAR(50) NOT NULL,  -- 'claim', 'entity', 'belief'
    entity_a_id         UUID NOT NULL,
    entity_a_version    BIGINT,
    
    entity_b_type       VARCHAR(50) NOT NULL,
    entity_b_id         UUID NOT NULL,
    entity_b_version    BIGINT,
    
    -- Contradiction details
    contradiction_type  VARCHAR(50) NOT NULL,
    -- 'regional'        : Different regions have different accounts
    -- 'historical'      : Different time periods have different accounts
    -- 'witness'         : Two witnesses describe the same thing differently
    -- 'source'          : Two sources have conflicting information
    -- 'interpretation'  : Two interpretations of the same evidence differ
    
    description         TEXT NOT NULL,
    severity            VARCHAR(20) NOT NULL DEFAULT 'medium',
    -- 'low', 'medium', 'high'
    
    resolution          TEXT,  -- NULL if unresolved
    
    -- Both provenance chains are preserved independently
    -- Each entity_a/b references its own source evidence
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_contradiction UNIQUE(entity_a_type, entity_a_id, entity_b_type, entity_b_id)
);

CREATE INDEX idx_contradiction_entity 
    ON provenance_contradictions(entity_a_type, entity_a_id);
CREATE INDEX idx_contradiction_entity_b 
    ON provenance_contradictions(entity_b_type, entity_b_id);
```

**Contradiction example**:
```json
{
  "contradictionId": "uuid",
  "type": "regional",
  "description": "Kuntilanak is described as a young woman in Javanese folklore, but as an old woman in Kalimantan accounts.",
  "sides": [
    {
      "label": "Javanese folklore (Witness: Mbah Karno)",
      "statement": "Kuntilanak berwujud perempuan muda dengan rambut panjang",
      "entityIds": ["entity-kuntilanak-java"],
      "evidence": [
        {
          "segmentIndex": 5,
          "text": "Kuntilanak iku wedok nom-noman rambute dawa",
          "startTime": 120.0,
          "endTime": 125.0,
          "speaker": "Mbah Karno"
        }
      ],
      "sourceDescription": "Interview in Desa Jati, Jawa Tengah, 2024"
    },
    {
      "label": "Kalimantan folklore (Witness: Pak Usman)",
      "statement": "Kuntilanak berwujud perempuan tua",
      "entityIds": ["entity-kuntilanak-borneo"],
      "evidence": [
        {
          "segmentIndex": 3,
          "text": "Kuntilanak berupa perempuan tua",
          "startTime": 45.0,
          "endTime": 48.0,
          "speaker": "Pak Usman"
        }
      ],
      "sourceDescription": "Interview in Desa Seberang, Kalimantan Barat, 2024"
    }
  ],
  "resolution": null,
  "severity": "medium"
}
```

### Rule 7: Immutable Source Material

Sources and transcripts are the foundation of the provenance chain. They must never be deleted.

```sql
-- Sources are immutable after creation
CREATE TABLE content_sources (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source identification
    source_type         VARCHAR(50) NOT NULL,
    -- 'youtube_video', 'youtube_channel', 'podcast_episode',
    -- 'document', 'interview', 'folklore_record', 'book', 'article'
    
    title               TEXT NOT NULL,
    description         TEXT,
    url                 TEXT,
    
    -- Source-specific metadata
    channel_name        VARCHAR(500),
    episode_number      INTEGER,
    duration_seconds    INTEGER,
    published_date      DATE,
    author              VARCHAR(500),
    language            VARCHAR(20),
    
    -- Cultural context
    region              VARCHAR(200),
    ethnic_group        VARCHAR(200),
    
    -- Additional metadata
    metadata            JSONB NOT NULL DEFAULT '{}',
    
    -- Provenance for the source itself
    acquired_by         UUID NOT NULL,           -- Who registered this source
    acquisition_method  VARCHAR(50) NOT NULL,    -- 'api_import', 'manual_submission', 'partner_integration'
    external_id         VARCHAR(500),            -- ID in external system (YouTube video ID, etc.)
    
    -- Immutable: sources are NEVER deleted
    -- Soft delete only for regulatory compliance
    is_deleted          BOOLEAN NOT NULL DEFAULT false,
    deleted_at          TIMESTAMPTZ,
    deleted_reason      TEXT,
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL
);

-- Transcripts are versioned, never deleted
CREATE TABLE content_transcripts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id           UUID NOT NULL REFERENCES content_sources(id),
    
    -- Content
    language            VARCHAR(20) NOT NULL,
    text                TEXT NOT NULL,
    segments            JSONB NOT NULL,          -- Array of { segmentIndex, text, startTime, endTime, speaker }
    
    -- Versioning
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id UUID REFERENCES content_transcripts(id),
    change_reason       TEXT,
    
    -- Metadata
    duration_seconds    INTEGER,
    speaker_count       INTEGER,
    generated_by        VARCHAR(50) NOT NULL,    -- 'whisperx', 'manual_transcription', 'imported'
    
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL
);
```

### Rule 8: Research Citation Support

The provenance chain must support academic citation formats. Researchers must be able to export provenance information for citations.

```python
class CitationGenerator:
    """Generates academic citations from provenance data."""
    
    async def generate_citation(
        self, 
        content_type: str, 
        content_id: UUID, 
        format: str = "apa"
    ) -> dict:
        """Generate a citation for a knowledge artifact.
        
        Args:
            content_type: Type of artifact ('claim', 'knowledge_object', 'story')
            content_id: UUID of the artifact
            format: Citation format ('apa', 'mla', 'chicago', 'ieee')
        
        Returns:
            Citation in requested format with full provenance chain
        """
        # Resolve the full provenance chain
        chain = await self._resolve_provenance_chain(content_type, content_id)
        
        if format == "apa":
            return self._format_apa(chain)
        elif format == "mla":
            return self._format_mla(chain)
        else:
            return self._format_chicago(chain)
    
    def _format_apa(self, chain: ProvenanceChain) -> dict:
        """Generate APA-style citation with provenance."""
        source = chain['source']
        transcript = chain['transcript']
        
        citation_text = (
            f"{source['author']} ({source['published_year']}). "
            f"{source['title']} [Source: {source['source_type']}]. "
            f"The Living Atlas of Indonesian Mystery Culture. "
            f"https://livingatlas.id/sources/{source['id']}"
        )
        
        return {
            "citation": citation_text,
            "format": "APA 7th Edition",
            "provenance": {
                "source": {
                    "id": str(source['id']),
                    "title": source['title'],
                    "type": source['source_type'],
                    "url": source['url'],
                },
                "transcript": {
                    "id": str(transcript['id']),
                    "language": transcript['language'],
                    "segment": chain.get('segment_index'),
                },
                "artifact": {
                    "type": chain['artifact_type'],
                    "id": str(chain['artifact_id']),
                    "version": chain['artifact_version'],
                    "generation_method": chain['generation_method'],
                },
                "ai_extraction": chain.get('ai_metadata'),
                "review": chain.get('review_metadata'),
            }
        }
    
    async def _resolve_provenance_chain(
        self, content_type: str, content_id: UUID
    ) -> ProvenanceChain:
        """Resolve the complete provenance chain for an artifact."""
        # Follow lineage backward from artifact to source
        chain = {}
        current_type = content_type
        current_id = content_id
        
        while current_type != 'source':
            lineage = await db.fetch_one("""
                SELECT source_type, source_id, target_type, target_id, 
                       relationship_type
                FROM provenance_lineage
                WHERE (target_type = $1 AND target_id = $2)
                   OR (source_type = $1 AND source_id = $2)
                ORDER BY created_at ASC
                LIMIT 1
            """, current_type, current_id)
            
            if not lineage:
                break
            
            # Move to the parent in the chain
            if lineage['target_type'] == current_type and lineage['target_id'] == current_id:
                current_type = lineage['source_type']
                current_id = lineage['source_id']
            else:
                current_type = lineage['target_type']
                current_id = lineage['target_id']
            
            chain[f'level_{current_type}'] = {
                'id': current_id,
                'type': current_type
            }
        
        return ProvenanceChain(**chain)
```

**API endpoint for citations**:
```
GET /api/v1/provenance/citation?type=claim&id=:claimId&format=apa

Response:
{
  "citation": "Sariman, P. (2024). Penampakan Kuntilanak di Pemakaman Desa Sukamaju [YouTube video]. The Living Atlas of Indonesian Mystery Culture. https://livingatlas.id/sources/b1c2d3e4-...",
  "format": "APA 7th Edition",
  "provenance": {
    "source": { "id": "b1c2d3e4-...", "title": "Misteri Kuntilanak", "type": "youtube_video" },
    "transcript": { "id": "d4c3b2a1-...", "language": "id", "segment": 2 },
    "artifact": { "type": "claim", "id": "d6e7f8a9-...", "version": 1, "generation_method": "ai_extracted" },
    "ai_extraction": { "model": "gemini-2.5-pro", "prompt_version": "story-canonicalization-v3", "confidence": 85 },
    "review": { "reviewed_by": "editor@tenant", "reviewed_at": "2026-06-26T10:00:00Z", "decision": "approved" }
  }
}
```

### Rule 9: Provenance in Projections

Provenance is carried through to Neo4j and Weaviate projections. Every graph node and vector object carries source identification metadata.

```cypher
// Neo4j — every node carries provenance
MERGE (s:Story {id: $story_id})
SET s.source_id = $source_id,
    s.transcript_id = $transcript_id,
    s.version = $version,
    s.generation_method = $generation_method,
    s.extraction_model = $model,
    s.prompt_version = $prompt_version,
    s.confidence = $confidence,
    s.review_status = $review_status,
    s.reviewed_by = $reviewed_by,
    s.published_at = $published_at

// Evidence relationships in Neo4j
MATCH (c:Claim {id: $claim_id})
MATCH (ts:TranscriptSegment {id: $segment_id})
MERGE (c)-[:SUPPORTED_BY {confidence: $confidence}]->(ts)
```

```python
# Weaviate — every object carries provenance
weaviate_client.data_object.create(
    class_name="Story",
    uuid=story['id'],
    vector=embedding,
    properties={
        "title": story['title'],
        "content": story['content'],
        "source_id": str(story['source_id']),
        "transcript_id": str(story['transcript_id']),
        "generation_method": story['generation_method'],
        "extraction_model": story.get('extraction_model'),
        "confidence": story.get('confidence'),
        "review_status": story['review_status'],
    },
    tenant=tenant_id
)
```

### Rule 10: Provenance Query API

A dedicated provenance API enables external consumers (research tools, citation managers, audit systems) to query the full provenance chain for any artifact.

```python
# REST API endpoints for provenance
GET /api/v1/provenance/{content_type}/{content_id}
# Returns the complete provenance chain from source to artifact

GET /api/v1/provenance/{content_type}/{content_id}/chain
# Returns the sequential chain: Source → Transcript → Segment → Artifact

GET /api/v1/provenance/{content_type}/{content_id}/tree
# Returns the full provenance tree including derived artifacts

GET /api/v1/provenance/{content_type}/{content_id}/citation?format=apa
# Returns a formatted academic citation with provenance

GET /api/v1/provenance/lineage?source_type=:type&source_id=:id
# Returns all entities derived from a given source

# GraphQL interface
query {
  provenance(contentType: "claim", contentId: "uuid") {
    chain {
      level
      type
      id
      description
    }
    citations(format: APA)
    generationMethod
    aiMetadata {
      model
      promptVersion
      confidence
    }
    reviewHistory {
      decision
      reviewer
      timestamp
    }
  }
}
```

**Provenance API response**:
```json
{
  "artifact": {
    "type": "claim",
    "id": "d6e7f8a9-0123-4567-8901-234567890123",
    "version": 1,
    "generation_method": "ai_extracted",
    "created_at": "2026-06-25T01:00:00Z"
  },
  "chain": [
    {
      "level": 0,
      "type": "source",
      "id": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
      "title": "Misteri Kuntilanak di Desa Sukamaju",
      "source_type": "youtube_video",
      "url": "https://youtube.com/watch?v=abc123"
    },
    {
      "level": 1,
      "type": "transcript",
      "id": "d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b",
      "language": "id",
      "version": 1
    },
    {
      "level": 2,
      "type": "transcript_segment",
      "segment_index": 2,
      "text": "waktu itu tahun 2019, saya pulang dari sawah jam 11 malam...",
      "speaker": "Pak Sariman",
      "start_time": 46.0,
      "end_time": 120.5
    },
    {
      "level": 3,
      "type": "canonical_story",
      "id": "c5d6e7f8-a9b0-1234-efab-345678901234",
      "version": 1,
      "ai_metadata": {
        "model": "gemini-2.5-pro",
        "prompt_version": "story-canonicalization-v3",
        "confidence": 85
      }
    },
    {
      "level": 4,
      "type": "review",
      "decision": "approved",
      "reviewed_by": "editor@tenant",
      "reviewed_at": "2026-06-26T10:00:00Z"
    }
  ],
  "citations": {
    "apa": "Sariman, P. (2024). Misteri Kuntilanak di Desa Sukamaju [YouTube video]. The Living Atlas of Indonesian Mystery Culture. https://livingatlas.id/sources/b1c2d3e4-...",
    "mla": "Sariman, Pak. \"Misteri Kuntilanak di Desa Sukamaju.\" The Living Atlas of Indonesian Mystery Culture, 2024, https://livingatlas.id/sources/b1c2d3e4-..."
  }
}
```

# Alternatives Considered

## Alternative 1: Provenance as Free-Text Metadata

**Description**: Store provenance as a free-text field in each content table. Authors, sources, and evidence are described in natural language rather than structured references. No enforced provenance chain.

**Advantages**:
- Simplest implementation — single text field, no foreign keys
- Flexible — can describe any provenance scenario in prose
- No schema changes when new provenance patterns emerge
- Low storage overhead
- No complex validation logic

**Disadvantages**:
- **Not machine-queryable**: Cannot answer "which claims are derived from this source?" because provenance is unstructured text.
- **No automated validation**: Cannot verify that evidence references point to real transcript segments. A hallucinated claim with a plausible-looking free-text provenance passes all checks.
- **No citation generation**: Cannot generate structured citations from free-text provenance. Researchers must manually format citations.
- **No cross-entity lineage**: Cannot trace relationships between entities programmatically. Each entity's provenance is an island.
- **Inconsistent formatting**: Different AI extraction runs may format provenance differently. Downstream tools cannot parse provenance reliably.
- **No AI vs human distinction**: Free-text provenance may not consistently indicate whether content was AI-generated or human-authored.

**Rejection rationale**: Free-text provenance is insufficient for research-grade traceability. The platform's core value proposition — verifiable, citable cultural knowledge — requires machine-queryable, structurally enforced provenance. The structured provenance chain (source → transcript → segment → artifact) with foreign key references is essential for automated validation, citation generation, and cross-entity queries.

## Alternative 2: Provenance Only at the Story Level

**Description**: Track provenance only at the story level (which source produced this story). Entities, claims, and beliefs within the story inherit the story's provenance implicitly. No per-item evidence tracking.

**Advantages**:
- Simpler Canonical Story schema — no evidence arrays on every entity/claim
- Lower storage overhead — no duplication of evidence references
- Faster AI extraction — no per-item evidence generation
- Simpler validation — check story-level provenance only
- Less complex review UI — reviewers check story-level provenance

**Disadvantages**:
- **No per-claim evidence verification**: A claim within the story may be hallucinated, but there is no evidence reference to verify against. Reviewers cannot easily determine which claims are supported.
- **No granular citation**: A researcher citing a specific claim cannot reference the exact transcript segment. They must cite the entire story, which may contain unrelated content.
- **Weak hallucination detection**: The evidence requirement is the strongest defense against AI hallucination (per ADR-013). Without per-item evidence, AI extraction may invent entities and claims that "feel right" for the story but are not actually in the transcript.
- **No contradiction resolution**: Two contradictory claims within the same story cannot be traced to different transcript segments. Both claims appear equally valid without evidence references.
- **Reduced researcher trust**: Researchers cannot verify that a specific claim is grounded in evidence without reading the entire source transcript.

**Rejection rationale**: Story-level provenance is necessary but not sufficient. The platform's "Provenance First" principle (§3.5) requires every knowledge object to be traceable. Per-item evidence is the mechanism that makes this possible. Without it, the provenance chain breaks at the first branching — a story may have a valid source, but individual claims within it may be unsupported.

## Alternative 3: Centralized Provenance Registry

**Description**: Store all provenance data in a centralized `provenance_entries` table instead of embedding evidence in the Canonical Story. Each entity references its provenance entries by ID. The Canonical Story contains only entity data without embedded evidence.

**Advantages**:
- Single source of truth for all provenance — one table to query
- No data duplication — evidence text is stored once, referenced many times
- Provenance can be updated independently of content (e.g., correcting an evidence reference)
- Cross-entity provenance queries are simpler — one table
- Smaller Canonical Story payload — no large evidence arrays

**Disadvantages**:
- **Broken self-contained Canonical Story**: The Canonical Story is designed as a self-contained artifact (ADR-007). Without embedded evidence, a Canonical Story export is incomplete — it requires joins to the provenance registry.
- **Additional join at query time**: Reading a Canonical Story requires querying both the story table and the provenance entries table. This adds latency to the critical path.
- **Referential integrity complexity**: Provenance entries reference transcript segments. If the registry is centralized, foreign key relationships span multiple tables, increasing complexity.
- **Provenance consistency**: When a Canonical Story is validated, the provenance entries must also be validated. Two-phase validation adds complexity.
- **No offline portability**: A Canonical Story exported for external use (research, backup) is incomplete without the provenance registry. Embedded evidence is self-contained.
- **Versioning complexity**: When a Canonical Story is re-extracted, old provenance entries must be deprecated and new ones created. Embedded evidence is versioned with the story automatically.

**Rejection rationale**: A centralized provenance registry provides cleaner normalization but breaks the self-contained Canonical Story contract. For a platform where Canonical Stories are exported for research, audited for compliance, and archived for long-term preservation, self-contained artifacts with embedded evidence are superior to a normalized but coupled design. The storage duplication of evidence text is an acceptable trade-off for self-containment and portability.

## Alternative 4: Blockchain-Based Provenance

**Description**: Use a blockchain or distributed ledger to record provenance entries. Each provenance event (source registered, transcript created, story extracted, claim validated) is recorded as an immutable transaction on the ledger. The ledger provides tamper-evident provenance.

**Advantages**:
- Tamper-evident provenance — no one can modify provenance history without detection
- Decentralized trust — researchers can verify provenance without trusting the platform
- Immutable event log — every provenance event is permanently recorded
- Public verifiability — provenance can be verified by third parties
- Alignment with cultural preservation values — permanent, unchangeable record

**Disadvantages**:
- **Massive operational complexity**: Running a blockchain node, managing transactions, and ensuring ledger consistency adds enormous operational burden for a small team.
- **Latency and cost**: Every provenance event requires a blockchain transaction, which takes seconds to minutes and costs transaction fees. At 1M+ knowledge objects, transaction costs are prohibitive.
- **No query capability**: Blockchains are not designed for complex queries like "find all claims derived from this source." Provenance data would need to be mirrored to a queryable database anyway.
- **Data privacy**: Provenance data may contain sensitive information (reviewer identities, unpublished content status). A public ledger is incompatible with data privacy requirements.
- **Storage bloat**: Storing evidence text (transcript segments, evidence references) on a blockchain is impractical due to block size limits and cost. Only hashes would be stored, requiring off-chain data for verification.
- **Regulatory uncertainty**: Indonesian data sovereignty regulations may not permit storing cultural knowledge provenance on a public blockchain.
- **Overkill for the problem**: The platform needs provable provenance, not decentralized trust. Immutable versioning in PostgreSQL (ADR-008) provides tamper-evident provenance without blockchain complexity.

**Rejection rationale**: Blockchain-based provenance is a solution looking for a problem. The platform's existing infrastructure — immutable versioning in PostgreSQL (ADR-008), complete audit trails (ADR-013), and structural provenance enforcement (this ADR) — provides tamper-evident provenance without blockchain complexity. Blockchain would add orders of magnitude operational overhead for no practical benefit over the current approach.

# Consequences

## Positive

1. **Research-grade traceability**: Every knowledge object can be traced to its source evidence. Researchers can verify claims, cite specific source passages, and trust that published content is evidence-grounded.

2. **AI-generated vs human-generated distinction**: Every artifact declares its generation method. Users can distinguish AI-extracted content from human-authored content. AI extraction metadata (model, prompt, confidence) is recorded.

3. **Contradiction preservation with provenance**: Contradictory claims from different sources are preserved with complete provenance chains for each side. Researchers can explore conflicting accounts with full source attribution.

4. **Self-contained Canonical Stories**: The Canonical Story JSON includes embedded evidence for every entity, claim, belief, theme, and motif. A Canonical Story export is complete — no external joins needed for provenance verification.

5. **Academic citation support**: The provenance API generates formatted citations (APA, MLA, Chicago, IEEE) from provenance data. Researchers can export citations with full provenance context.

6. **Complete lineage tracking**: The `provenance_lineage` table tracks relationships between any two entities. This enables backward tracing (find the source of any artifact) and forward tracing (find all artifacts derived from a source).

7. **Immutable source material**: Sources and transcripts are never deleted. The foundation of the provenance chain is permanent. Soft delete is available for regulatory compliance only.

8. **Provenance in projections**: Neo4j nodes and Weaviate objects carry source identification metadata. Graph and search results include provenance context.

## Negative

1. **Storage overhead**: Evidence text is stored in every Canonical Story, duplicating transcript content. At 10M transcript segments referenced across 100K stories, this adds significant storage.

2. **Extraction cost**: AI extraction must generate evidence references for every entity, claim, belief, theme, and motif. This increases token usage and AI provider costs (estimated 10–20% increase per extraction).

3. **Validation complexity**: Every evidence reference must be validated — does the referenced segment exist? Does the segment text match? This adds validation time.

4. **Schema complexity**: The Canonical Story schema is large due to embedded evidence arrays. Developers must understand the evidence structure to work with the schema.

5. **Citation generation dependency on data quality**: Citation quality depends on source metadata quality. If source metadata (author, published date) is incomplete, generated citations are also incomplete.

6. **Lineage table growth**: Every cross-entity relationship creates a lineage row. At 100M graph relationships, the lineage table may grow to 200M+ rows (each relationship creates at least one lineage entry).

7. **No automatic provenance repair**: If a source or transcript is found to be incorrect, all derived artifacts inherit the error. Provenance traces the chain, but does not correct it. Correction requires re-extraction with corrected source material.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Traceability** | Every artifact traces to source evidence | Evidence storage duplication (2–5×) |
| **AI vs human distinction** | Clear generation method for every artifact | AI extraction metadata overhead |
| **Research citation** | Structured citations from provenance | Citation quality depends on source metadata |
| **Contradiction handling** | Both sides preserved with full provenance | Contradiction resolution is never automatic |
| **Self-contained stories** | Complete provenance in one JSON document | Larger payload, slower to validate |
| **Lineage tracking** | Full cross-entity relationship graph | Lineage table growth at 200M+ rows |
| **Provenance cost** | Research-grade trustworthiness | 10–20% increased AI extraction cost |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Evidence reference points to non-existent segment** | Medium | Medium — broken provenance chain | Validate evidence references during extraction. FK constraint on segment_index. Alert on broken references. |
| **Evidence text diverges from actual transcript** | Medium | Medium — incorrect evidence, misleading provenance | Include segment_index in evidence. The UI should always display the actual transcript text from the segment, not the evidence text. |
| **Lineage table grows unbounded** | High | Medium — query performance degrades | Archive lineage entries older than 1 year. Implement TTL-based archiving. Use partitioning by creation date. |
| **Provenance API performance degrades** | Medium | Medium — slow provenance queries | Cache resolved provenance chains. Use materialized views for common queries. Limit depth of chain traversal. |
| **Source metadata quality is inconsistent** | High | Medium — citations may be incomplete | Validate source metadata on creation. Required fields: title, source_type, acquired_by. Optional fields with warnings: author, published_date. |
| **Cross-entity lineage cycles** | Low | Low — infinite loop in provenance traversal | Detect cycles during lineage insertion. Reject cyclic relationships. Implement cycle detection in traversal queries. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Source/Transcript accidentally hard-deleted** | Low | Critical — entire provenance chain broken | PostgreSQL triggers prevent DELETE on content_sources and content_transcripts. Only soft delete is allowed. |
| **Evidence validation fails for historical data** | Medium | Medium — old extractions may have invalid evidence | Run periodic evidence validation job. Flag invalid evidence for reprocessing. Implement repair workflow. |
| **Citation generation exposes unreviewed content** | Low | Medium — citation may reference REVIEW_REQUIRED content | Provenance API checks review status before generating citations. REVIEW_REQUIRED content returns 403. |
| **Storage costs for evidence duplication exceed budget** | Medium | Medium — unexpected storage growth | Monitor evidence storage growth. Estimate 2–5× increase. Budget accordingly. Archive old versions. |
| **Generation method not declared for new content types** | Medium | Low — cannot distinguish AI vs human for new types | Enforce generation method at the database level. DEFAULT 'human_created' for tables that support it. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Regulatory requirement for AI content labeling** | Must label AI-generated content prominently | Already tracked via generation_method. Extend UI to show "AI" badge prominently. |
| **W3C Provenance Ontology (PROV-O) alignment required** | Must align provenance model with W3C standard | The five-level chain maps to PROV-O entities. Add PROV-O mapping layer for compliance. |
| **Cross-platform provenance sharing** | External systems need to consume provenance data | Expose provenance API (Rule 10). Support PROV-O JSON-LD format for interoperability. |
| **Fine-grained provenance at the paragraph level** | Articles need per-paragraph source attribution | Extend evidence model to support paragraph-level provenance. Current model supports story/claim/entity level. |
| **Real-time provenance verification** | Users need instant provenance verification | Cache resolved chains. Implement pre-computed chain materialization for frequently accessed artifacts. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **W3C PROV-O alignment required**: If the platform needs to exchange provenance data with external systems (research databases, cultural heritage institutions), implement a PROV-O mapping layer. The five-level chain maps naturally to PROV-O entities, activities, and agents.

2. **Fine-grained provenance at paragraph or sentence level**: If articles need per-paragraph source attribution, extend the evidence model to support nested evidence references. This is an evolution of the current per-claim model, not a replacement.

3. **Real-time provenance verification for interactive research**: If researchers need instant provenance verification during interactive graph exploration, implement pre-computed chain materialization and caching for frequently accessed artifacts.

4. **Automated provenance repair**: If the platform needs to automatically repair broken provenance chains (e.g., when a source URL changes, all derived artifacts should be updated), implement a provenance repair pipeline with version creation for affected artifacts.

5. **External provenance ingestion**: If the platform ingests content from external sources with their own provenance (e.g., academic papers with DOIs, cultural heritage database records), implement a provenance mapping layer that translates external provenance to the platform's model.

6. **Privacy-preserving provenance**: If regulatory requirements mandate anonymization of certain provenance data (reviewer identities, source locations for sensitive cultural knowledge), implement provenance redaction while preserving the structural chain.

# References

- **Backend Platform PRD §3.5** — "Provenance First" — Every knowledge object must be traceable. Knowledge Object → Claim → Evidence → Transcript Segment → Transcript → Source.
- **Backend Platform PRD §12** — "Audit Requirements" — created_at, created_by, updated_at, updated_by, version on every business table.
- **AI Platform PRD §8** — "Canonical Story Extraction" — Rules: preserve provenance, preserve evidence.
- **ADR-001: PostgreSQL as Source of Truth** — Single authoritative store for all provenance data.
- **ADR-003: Event-Driven Architecture** — Domain events carry provenance context (correlationId, causationId).
- **ADR-007: Canonical Story Core Contract** — Provenance is structural, not optional. Every entity has evidence.
- **ADR-008: Immutable Versioning** — No overwrites. Every version preserved. Temporal provenance queries.
- **ADR-011: Knowledge Graph Projection** — Neo4j nodes carry source provenance metadata.
- **ADR-012: Vector Search Architecture** — Weaviate objects carry source identification metadata.
- **ADR-013: Human Review Required** — Review decisions are part of the provenance chain.
- **W3C PROV-O** — https://www.w3.org/TR/prov-o/ — W3C Provenance Ontology for interoperable provenance (future alignment).
- **Dublin Core** — https://www.dublincore.org/ — Metadata standards for cultural heritage (citation format alignment).
- **APA Citation Format** — https://apastyle.apa.org/ — Academic citation format supported by the citation generator.