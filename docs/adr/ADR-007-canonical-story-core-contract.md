# ADR-007: Canonical Story as the Platform Core Contract

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture transforms unstructured cultural narratives into structured, verifiable, searchable, and reusable cultural knowledge. The transformation pipeline has multiple stages, each producing different artifacts:

1. **Transcript → Canonical Story** (extraction service)
2. **Canonical Story → Knowledge Objects** (knowledge extraction service)
3. **Canonical Story + Knowledge → Articles** (article service)
4. **Canonical Story + Knowledge → Embeddings** (embedding service)
5. **Canonical Story + Knowledge → Graph Projection** (graph projection worker)

Without a single shared contract, each pair of pipeline stages would need its own interface agreement. The extraction service would define its output format, the knowledge service would define its input format, the article service would define another, and so on. Over time, these interfaces would diverge, creating translation layers, data loss, and integration complexity.

## Technical Context

The AI Platform PRD §3.6 states: "All AI outputs must eventually conform to Canonical Story Specification. Canonical Story becomes the contract between extraction, knowledge, articles, embeddings, and graph."

The existing `docs/ai-platform/canonical-story-specification.md` defines a comprehensive JSON Schema (v1.0.0) covering:
- Core story narrative (title, summary, narrative type, cultural context, witnesses, key events)
- Entities (spirits, deities, creatures, people, locations with attributes, relationships, aliases)
- Claims (evidence-grounded statements with confidence, validation, and review state)
- Locations (geographic coordinates, types, cultural significance)
- Beliefs, rituals, traditions (community-attributed cultural practices)
- Themes and motifs (recurring patterns with AAT classification)
- Contradictions (explicitly preserved conflicting accounts with multiple sides)
- Research gaps and uncertainties (missing data, ambiguous references)
- Provenance chain (source → transcript → extraction job → model → prompt version)
- Extraction metadata (model, prompt version, tokens, cost, quality score)

The specification is 1,987 lines and includes a complete JSON Schema, a worked example ("Kuntilanak Sighting at Sukamaju Village Cemetery"), entity type taxonomy, and mapping rules.

## Constraints

1. **Single source of truth for AI output**: The Canonical Story is the authoritative output of AI extraction. All downstream artifacts are derived from it. No downstream system should independently define its own input contract.

2. **Provenance chain**: Every piece of data in the Canonical Story must be traceable to a source transcript segment (ADR-003 §provenance-first). The contract must enforce this structurally.

3. **Immutable versioning**: Canonical Stories are versioned and immutable. Updates create new versions (Backend Platform PRD §3.7).

4. **Human review gate**: Canonical Stories are written to PostgreSQL in `REVIEW_REQUIRED` state. Only after review are they used for article generation, graph projection, and embedding generation (ADR-004 Rule 10).

5. **Multi-consumer compatibility**: The Canonical Story must serve as input for at least 5 downstream consumers: PostgreSQL (story + knowledge tables), Neo4j (graph projection), Weaviate (vector embedding), Article Service (4 article types), and future analytics/research pipelines.

6. **Schema evolution**: The contract must support versioning. Breaking changes to the Canonical Story schema require coordinated updates across all downstream consumers.

7. **Cultural sensitivity**: Indonesian mystery culture spans hundreds of ethnic groups. The contract must preserve regional variations, original language names, and community-specific beliefs.

## Problem Statement

The AI extraction pipeline produces a Canonical Story. Downstream systems need entities, claims, articles, graph nodes, and embeddings. Without a single shared contract, each downstream system would define its own input format, leading to interface proliferation, data loss, and integration complexity. How do we establish the Canonical Story as the single, versioned, immutable contract that all pipeline stages conform to, while supporting schema evolution, provenance tracking, and multi-consumer compatibility?

# Decision

**The Canonical Story JSON is the platform contract. All AI outputs must conform to the Canonical Story Specification. Downstream systems (PostgreSQL persistence, knowledge extraction, article generation, embedding generation, graph projection) consume the Canonical Story as their single input. No downstream system defines its own independent input format. The Canonical Story Specification is versioned, immutable once created, and schema validation is enforced at every pipeline stage.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CANONICAL STORY CONTRACT                              │
│                                                                          │
│  A single, versioned, validated JSON schema that all pipeline stages     │
│  must produce and consume. No independent input contracts.               │
│                                                                          │
│  Specification: docs/ai-platform/canonical-story-specification.md        │
│  Schema: https://livingatlas.id/schemas/canonical-story-v1.json          │
│  Current Version: 1.0.0                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       AI PIPELINE STAGES                                  │
│                                                                          │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────────────┐   │
│  │   Transcript    │───►│   Extraction   │───►│  Canonical Story     │   │
│  │                 │    │   Service      │    │  JSON (EXTRACTED)    │   │
│  └────────────────┘    └────────────────┘    └──────────┬───────────┘   │
│                                                         │               │
│                                                         ▼               │
│                                              ┌──────────────────────┐   │
│                                              │  Knowledge           │   │
│                                              │  Extraction Service  │   │
│                                              │  (reads Canonical    │   │
│                                              │   Story, produces    │   │
│                                              │   Knowledge Objects) │   │
│                                              └──────────┬───────────┘   │
│                                                         │               │
│                                                         ▼               │
│                                              ┌──────────────────────┐   │
│                                              │  PostgreSQL           │   │
│                                              │  (Persisted Canonical│   │
│                                              │   Story + Knowledge) │   │
│                                              └──────────┬───────────┘   │
│                                                         │               │
│                            ┌────────────────────────────┼────────────┐   │
│                            │                            │            │   │
│                            ▼                            ▼            ▼   │
│                   ┌──────────────┐            ┌──────────────┐  ┌─────┐  │
│                   │  Article     │            │  Embedding   │  │Graph│  │
│                   │  Service     │            │  Service     │  │Proj.│  │
│                   │              │            │              │  │     │  │
│                   │  4 article   │            │  Story/entity│  │Neo4j│  │
│                   │  types       │            │  knowledge   │  │Nodes│  │
│                   └──────────────┘            └──────────────┘  └─────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Canonical Story Is the Single Contract

All pipeline stages use the Canonical Story JSON as their single, authoritative input format. No stage defines its own independent input contract.

**Meaning**:
- The extraction service produces Canonical Story JSON (nothing else).
- The knowledge extraction service consumes Canonical Story JSON (not raw transcripts, not a custom knowledge extraction format).
- The article service consumes Canonical Story JSON + validated Knowledge Objects extractable from it.
- The embedding service consumes Canonical Story JSON for story-level embeddings.
- The graph projection worker consumes Canonical Story JSON to derive nodes and relationships.

**What this prevents**:
- The extraction service producing a different format than the knowledge service expects
- The article service defining its own "ArticleInput" schema that duplicates Canonical Story fields
- The graph projection worker expecting a custom "GraphInput" format
- Data loss between pipeline stages due to format translation

**Enforcement**:
```python
# All AI workers validate their output/input against the Canonical Story schema
from jsonschema import validate, ValidationError

CANONICAL_STORY_SCHEMA = load_schema("canonical-story-v1.json")

class ExtractionService:
    async def extract(self, transcript, metadata) -> CanonicalStory:
        result = await ai_provider.extract_canonical_story(transcript, metadata)
        
        # Validate output against Canonical Story schema
        try:
            validate(instance=result, schema=CANONICAL_STORY_SCHEMA)
        except ValidationError as e:
            raise InvalidOutputError(f"Extraction output does not conform to Canonical Story schema: {e}")
        
        return CanonicalStory(**result)

class KnowledgeExtractionService:
    async def extract_knowledge(self, canonical_story: CanonicalStory) -> KnowledgeResult:
        # Input is already validated Canonical Story
        # Extract knowledge objects, claims, beliefs, etc.
        pass

class ArticleService:
    async def generate_article(self, canonical_story: CanonicalStory, article_type: str) -> Article:
        # Input is already validated Canonical Story
        # Generate article from the structured data
        pass
```

### Rule 2: Schema Validation at Every Stage

Every pipeline stage that produces or consumes a Canonical Story must validate against the schema. This is non-negotiable — validation is not optional.

**Validation points**:

| Stage | Action | Validation |
|-------|--------|------------|
| Extraction service | Produces Canonical Story | Validate output before writing to PostgreSQL |
| Orchestration service | Receives extraction.completed | Validate event payload contains valid Canonical Story |
| Knowledge extraction service | Consumes Canonical Story | Validate input before processing |
| Normalization service | Consumes Canonical Story | Validate input before processing |
| Validation service | Consumes Canonical Story | Validate input before scoring |
| Article service | Consumes Canonical Story | Validate input before article generation |
| Embedding service | Consumes Canonical Story | Validate input before embedding generation |
| Graph projection worker | Consumes Canonical Story from PostgreSQL | Validate before graph node creation |
| PostgreSQL persistence layer | Writes Canonical Story to DB | Validate JSONB before INSERT |

**Validation implementation** (Python, using `jsonschema`):
```python
def validate_canonical_story(story: dict) -> bool:
    """Validate a Canonical Story against the schema. Raises on failure."""
    try:
        validate(instance=story, schema=CANONICAL_STORY_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"Canonical Story validation failed: {e.message}", 
                     extra={
                         "canonical_story_id": story.get("canonicalStoryId"),
                         "path": list(e.absolute_path),
                         "schema_path": list(e.schema_path)
                     })
        raise

# PostgreSQL CHECK constraint for defense-in-depth
ALTER TABLE ai_output_canonical_stories
ADD CONSTRAINT canonical_story_schema_check
CHECK (validate_canonical_story_schema(story_data));
```

### Rule 3: Downstream Consumers Extract, Not Translate

Downstream consumers must extract the data they need from the Canonical Story. They must not translate or transform the Canonical Story into a different intermediate format.

**Correct approach** — extraction:
```python
class GraphProjectionWorker:
    async def project_story(self, canonical_story: CanonicalStory):
        # Extract story node data directly from Canonical Story
        story_node = {
            "id": canonical_story.canonicalStoryId,
            "title": canonical_story.story.title,
            "summary": canonical_story.story.summary,
            "narrative_type": canonical_story.story.narrativeType,
            "language": canonical_story.story.language,
        }
        await neo4j.run("MERGE (s:Story {id: $id}) SET s += $props", 
                       id=story_node["id"], props=story_node)
        
        # Extract entity nodes directly from Canonical Story entities array
        for entity in canonical_story.entities:
            entity_node = {
                "id": entity.entityId,
                "name": entity.name,
                "normalized_name": entity.normalizedName,
                "entity_type": entity.entityType,
                "subtype": entity.subtype,
            }
            await neo4j.run("MERGE (e:Entity {id: $id}) SET e += $props",
                           id=entity_node["id"], props=entity_node)
            
            # Create relationship between story and entity
            await neo4j.run("""
                MATCH (s:Story {id: $story_id})
                MATCH (e:Entity {id: $entity_id})
                MERGE (s)-[:MENTIONS {confidence: $confidence}]->(e)
            """, story_id=story_node["id"], entity_id=entity_node["id"],
                 confidence=entity.confidence)
```

**Incorrect approach** — translation:
```python
# DO NOT DO THIS: Creating an intermediate "GraphInput" format
class GraphInputTranslator:
    def translate(self, canonical_story: CanonicalStory) -> GraphInput:
        # This creates a parallel data model that must be maintained
        return GraphInput(
            nodes=self.extract_nodes(canonical_story),
            edges=self.extract_edges(canonical_story)
        )
```

### Rule 4: Immutable Canonical Story Versions

Canonical Stories are immutable. When a story is re-extracted (e.g., with an improved prompt or updated transcript), a new version is created. The old version is preserved.

```json
{
  "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
  "version": 1,
  "extractedAt": "2026-06-20T15:08:30.000Z",
  "story": { ... }
}

// Version 2 (re-extracted with improved prompt)
{
  "canonicalStoryId": "f8e7d6c5-b0a9-4321-bafe-098765432109",  // NEW ID
  "previousVersionId": "c5d6e7f8-a9b0-1234-efab-345678901234",  // Reference to v1
  "version": 2,
  "extractedAt": "2026-06-25T10:00:00.000Z",
  "extractionMetadata": {
    "promptVersion": "story-canonicalization-v4",  // New prompt
    ...
  },
  "story": { ... }  // Updated content
}
```

**Versioning rules**:
- Each version gets a new `canonicalStoryId` (UUID v4)
- The `version` field increments (1, 2, 3...)
- Optional `previousVersionId` links to the previous version
- The full version history is preserved in PostgreSQL
- Downstream consumers process each version independently
- Graph projection uses the latest version for current state, but can show history

### Rule 5: Canonical Story Fields Map Directly to Downstream Storage

The Canonical Story JSON fields map directly to PostgreSQL tables, Neo4j node properties, Weaviate class properties, and article generation prompts. No intermediate mapping layer is needed.

**PostgreSQL mapping**:

```sql
-- content_stories table (direct mapping from Canonical Story story.* fields)
INSERT INTO content_stories (
    id,                          -- canonicalStory.canonicalStoryId
    transcript_id,               -- canonicalStory.transcriptId
    title,                       -- canonicalStory.story.title
    title_en,                    -- canonicalStory.story.titleEn
    summary,                     -- canonicalStory.story.summary
    language,                    -- canonicalStory.story.language
    narrative_type,              -- canonicalStory.story.narrativeType
    tone,                        -- canonicalStory.story.tone
    cultural_context,            -- canonicalStory.story.culturalContext (JSONB)
    version,                     -- canonicalStory.version
    source_id,                   -- canonicalStory.sourceId
    created_at,                  -- NOW()
    tenant_id,                   -- canonicalStory.metadata.tenantId
    workspace_id,                -- (from event metadata)
    created_by                   -- (system, extraction job)
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), $12, $13, $14);

-- knowledge_objects table (from Canonical Story entities.*)
INSERT INTO knowledge_objects (
    id,                          -- entity.entityId
    canonical_story_id,          -- canonicalStory.canonicalStoryId
    name,                        -- entity.name
    normalized_name,             -- entity.normalizedName
    entity_type,                 -- entity.entityType
    subtype,                     -- entity.subtype
    description,                 -- entity.description
    attributes,                  -- entity.attributes (JSONB)
    cultural_context,            -- entity.culturalContext (JSONB)
    confidence,                  -- entity.confidence
    provenance,                  -- entity.evidence (JSONB)
    created_at,
    tenant_id
) VALUES (...);

-- claims table (from Canonical Story claims.*)
INSERT INTO knowledge_claims (
    id,                          -- claim.claimId
    canonical_story_id,
    statement,                   -- claim.statement
    category,                    -- claim.category
    confidence,                  -- claim.confidence
    evidence,                    -- claim.evidence (JSONB)
    status,                      -- claim.status
    tenant_id
) VALUES (...);
```

**Neo4j mapping**:
```cypher
// Story node from Canonical Story story.*
MERGE (s:Story {id: $canonicalStoryId})
SET s.title = $story.title,
    s.summary = $story.summary,
    s.narrativeType = $story.narrativeType,
    s.language = $story.language,
    s.tenantId = $metadata.tenantId

// Entity nodes from Canonical Story entities[]
UNWIND $entities AS entity
MERGE (e:Entity {id: entity.entityId})
SET e.name = entity.name,
    e.entityType = entity.entityType,
    e.subtype = entity.subtype

// Story-Entity relationships from entities[].relationships[]
UNWIND $entities AS entity
UNWIND entity.relationships AS rel
MATCH (s:Story {id: $canonicalStoryId})
MATCH (e:Entity {id: rel.targetEntityId})
MERGE (s)-[r:MENTIONS]->(e)
SET r.confidence = rel.confidence,
    r.relationType = rel.relationType
```

### Rule 6: Schema Evolution Strategy

The Canonical Story schema evolves over time. Changes follow semantic versioning (MAJOR.MINOR.PATCH).

**Versioning rules**:

| Change Type | Version Bump | Consumer Impact |
|-------------|-------------|-----------------|
| Adding optional fields | PATCH (1.0.0 → 1.0.1) | None — consumers ignore unknown fields |
| Adding required fields | MINOR (1.0.0 → 1.1.0) | Consumers must be updated within grace period |
| Renaming fields | MAJOR (1.0.0 → 2.0.0) | All consumers must be updated before deployment |
| Removing fields | MAJOR (1.0.0 → 2.0.0) | All consumers must be updated before deployment |
| Changing field types | MAJOR (1.0.0 → 2.0.0) | All consumers must be updated before deployment |

**Coordination process for MAJOR version changes**:

```
1. Propose schema change (ADR + PR to canonical-story-specification.md)
2. Update all downstream consumers to handle old + new schema
3. Deploy consumers in "dual-mode" (can process v1 and v2)
4. Deploy producers with new schema (v2 output only)
5. Monitor for consumer errors
6. Remove v1 compatibility code from consumers
7. Update schema version in documentation
```

**Schema version in Canonical Story**:
```json
{
  "metadata": {
    "schemaVersion": "1.0.0",
    "schemaUrl": "https://livingatlas.id/schemas/canonical-story-v1.json"
  }
}
```

**Consumer version compatibility**:
```python
class CanonicalStoryConsumer:
    # Consumer declares which schema versions it supports
    SUPPORTED_SCHEMA_VERSIONS = [">=1.0.0", "<2.0.0"]
    
    def validate_compatibility(self, story: dict):
        schema_version = story["metadata"]["schemaVersion"]
        if not self.is_version_compatible(schema_version):
            raise IncompatibleSchemaError(
                f"Consumer supports versions {self.SUPPORTED_SCHEMA_VERSIONS}, "
                f"got {schema_version}"
            )
```

### Rule 7: Provenance Is Structural, Not Optional

Provenance is not metadata — it is a structural requirement of the Canonical Story. Every extraction must include a complete provenance chain.

```json
{
  "provenance": {
    "sourceId": "b1c2d3e4-...",          // Original source (video, podcast, document)
    "transcriptId": "d4c3b2a1-...",       // Transcript the story was extracted from
    "extractionJobId": "e5f6a7b8-...",    // AI Platform job that created this extraction
    "promptVersion": "story-canonicalization-v3",  // Exact prompt version used
    "modelUsed": "gemini-2.5-pro",        // AI model used
    "extractedAt": "2026-06-20T15:08:30.000Z"
  }
}
```

**Provenance chain enforcement**:

| Level | Field | Enforcement |
|-------|-------|-------------|
| Source | `provenance.sourceId` | Required. Must reference a valid source in `content_sources` table. |
| Transcript | `provenance.transcriptId` | Required. Must reference a valid transcript in `content_transcripts` table. |
| Job | `provenance.extractionJobId` | Required. Must reference a valid AI job in `ai_jobs` table. |
| Prompt | `provenance.promptVersion` | Required. Must reference a registered prompt version in the prompt registry. |
| Model | `provenance.modelUsed` | Required. Must be a configured AI provider model. |

**Per-item provenance** (within entities, claims, beliefs, etc.):
```json
{
  "entities": [
    {
      "entityId": "...",
      "name": "Kuntilanak",
      "confidence": 95,
      "evidence": [
        {
          "segmentIndex": 2,
          "text": "saya lihat sosok perempuan berambut panjang pakai baju putih",
          "startTime": 46.0,
          "endTime": 52.3,
          "speaker": "Pak Sariman"
        }
      ]
    }
  ]
}
```

Every entity, claim, belief, ritual, theme, and motif must include at least one `evidence` entry with a `segmentIndex` referencing the source transcript. Removal of evidence breaks provenance and is forbidden.

### Rule 8: Contradictions and Uncertainties Are First-Class Citizens

Contradictions and uncertainties are preserved alongside facts. They are not resolved or merged away during normalization.

**Contradictions** capture conflicting accounts:
- Regional: "Kuntilanak is described as a young woman in Java, an old woman in Kalimantan"
- Historical: "1800s accounts describe Kuntilanak differently than modern accounts"
- Source: "Podcast host says one thing, interviewee says another"
- Interpretation: "Two researchers interpret the same entity differently"

**Uncertainties** capture what is not known:
- Ambiguous reference ("Witness used two names for the same entity")
- Unclear timeline ("Event happened, but exact year is unknown")
- Speculative interpretation ("This might be a type of Kuntilanak, but evidence is thin")
- Translation ambiguity ("The word could mean 'spirit' or 'ghost' depending on context")

**Storage**: Contradictions and uncertainties are stored as arrays in the Canonical Story JSON. They are also extracted as separate tables in PostgreSQL for research analytics:

```sql
CREATE TABLE knowledge_contradictions (
    id                  UUID PRIMARY KEY,
    canonical_story_id  UUID NOT NULL,
    type                VARCHAR(50) NOT NULL,    -- regional, historical, source, etc.
    description         TEXT NOT NULL,
    sides               JSONB NOT NULL,           -- Array of {label, statement, evidence}
    severity            VARCHAR(20) NOT NULL,
    resolution          TEXT,                     -- null if unresolved
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE knowledge_uncertainties (
    id                  UUID PRIMARY KEY,
    canonical_story_id  UUID NOT NULL,
    target_type         VARCHAR(50) NOT NULL,     -- entity, claim, event, etc.
    target_id           UUID,
    uncertainty_type    VARCHAR(50) NOT NULL,     -- ambiguous_reference, unclear_timeline, etc.
    description         TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

# Alternatives Considered

## Alternative 1: Separate Contracts per Pipeline Stage

**Description**: Each pipeline stage defines its own input/output contract. The extraction service produces an "ExtractionOutput." The knowledge service defines its own "KnowledgeInput" and produces a "KnowledgeOutput." The article service defines an "ArticleInput." Each contract is independently versioned and evolved.

**Advantages**:
- Each contract is optimized for its specific stage — no unnecessary fields
- A change to one stage's contract does not affect other stages
- Smaller, simpler schemas per stage
- Teams own their own contracts independently

**Disadvantages**:
- **N² interface problem**: 6 pipeline stages with independent contracts means up to 15 interface pairs that must be maintained and kept in sync.
- **Data loss between stages**: The extraction output may include fields that the knowledge input does not define. These fields are silently dropped during translation.
- **Translation layers everywhere**: Each stage boundary requires a translation function: `ExtractionOutput → KnowledgeInput`, `KnowledgeOutput → ArticleInput`, etc. These translation functions are untested, undocumented liabilities.
- **No provenance chain across stages**: If the extraction output includes provenance but the knowledge input does not define provenance fields, the provenance chain is broken at the first translation.
- **Schema divergence over time**: Stage A adds a field. Stage B does not update its input contract. Stage C never receives the field. The system silently loses data.
- **Debugging complexity**: A data quality issue must be traced through 5+ translation functions to find the root cause.

**Rejection rationale**: Separate contracts per stage create an N² interface maintenance problem, enable silent data loss through translation, and break the provenance chain that is fundamental to the platform's "Provenance First" principle. A single Canonical Story contract eliminates these problems by ensuring every stage speaks the same language.

## Alternative 2: Canonical Story with Stage-Specific Views

**Description**: The Canonical Story remains the single contract, but each downstream stage defines a "view" — a JSON Schema subset that specifies which fields it needs. The Canonical Story is validated against the full schema. Each stage validates that its required fields are present using the view schema.

**Advantages**:
- Single source of truth (Canonical Story)
- Each stage declares its dependencies explicitly via view schemas
- Schema evolution impact is clear — which stages depend on which fields
- A new field can be added without affecting stages that don't need it
- Better documentation of inter-stage dependencies

**Disadvantages**:
- **Schema proliferation**: With 6+ stages, there are 6+ view schemas to maintain alongside the main schema. Each view schema is another file to review, test, and version.
- **View schema drift**: Over time, view schemas may define constraints that diverge from the main schema. A field marked optional in the main schema may be required in a view, creating hidden coupling.
- **Validation complexity**: The system must validate against the full schema AND the view schema. Two validation steps per stage. Error messages must distinguish between "invalid Canonical Story" and "required field missing for this stage."
- **Stage dependency mapping**: Adding a new field requires updating the main schema AND potentially updating each view schema. This coordination overhead reduces the benefit of a single contract.

**Rejection rationale**: View schemas add maintenance overhead without proportional benefit for a small team. For a platform with 3–8 engineers, maintaining 6+ view schemas in addition to the main schema is not justified. Stage dependencies are better documented through code (which fields does this stage actually read?) rather than through separate view schema files. The Canonical Story contract with explicit field documentation serves as the single source of truth.

## Alternative 3: Protocol Buffers Instead of JSON Schema

**Description**: Replace JSON Schema with Protocol Buffers (protobuf) for the Canonical Story contract. Services communicate using serialized protobuf messages instead of JSON. The .proto file becomes the single source of truth, with code generation for Java and Python.

**Advantages**:
- Strongly typed contracts enforced at compile time in both Java and Python
- Smaller message size (binary protobuf vs. text JSON)
- Faster serialization/deserialization
- Clear schema evolution rules built into protobuf (field numbers, reserved fields)
- Code generation eliminates manual DTO creation
- Backward compatibility is enforced by the protobuf compiler

**Disadvantages**:
- **Human readability is critical for this contract**: The Canonical Story is not just a message format — it is the core data model of the platform. Researchers, editors, and operators need to inspect Canonical Stories directly. JSON is human-readable. Protobuf binary is not.
- **JSONB storage in PostgreSQL**: Canonical Stories are stored as JSONB in PostgreSQL for flexible querying, indexing, and ad-hoc analysis. Protobuf would require a separate serialization step for storage.
- **Event-driven architecture already uses JSON**: Redpanda events use JSON for schema flexibility and human readability (ADR-003). Introducing protobuf would mean maintaining two serialization formats.
- **Python JSON ecosystem**: The AI Platform (Python) extensively uses JSON for AI provider communication, data analysis, and debugging. Protobuf adds a compilation step to the Python build process.
- **Debugging overhead**: Inspecting a Canonical Story in production requires decoding protobuf binary. JSON can be read directly from the database or event log.
- **No schema registry integration**: Redpanda's Schema Registry works with JSON Schema, Avro, and Protobuf. JSON Schema integration is simpler and more mature in the existing stack.

**Rejection rationale**: Protocol Buffers provide performance and type safety benefits that are valuable for high-throughput RPC communication. The Canonical Story contract is not an RPC message — it is a persistent data model that must be human-readable, storable as JSONB, debuggable in production, and easily inspectable by non-engineers (researchers, editors). JSON Schema provides the necessary validation and versioning capabilities without sacrificing human readability. The existing JSON-first event-driven architecture (ADR-003) reinforces this decision.

## Alternative 4: GraphQL as the Contract Layer

**Description**: Use GraphQL as the contract layer. The extraction service exposes a GraphQL mutation that accepts transcripts and returns Canonical Stories. Downstream consumers query for the specific fields they need using GraphQL queries. The GraphQL schema becomes the contract.

**Advantages**:
- Consumers query exactly the fields they need — no over-fetching
- GraphQL schema provides built-in documentation and introspection
- Schema evolution is additive by default (new fields don't break existing queries)
- Single endpoint for all pipeline stages
- Strong typing via GraphQL schema language

**Disadvantages**:
- **GraphQL is synchronous**: Pipeline stages need asynchronous communication (events). GraphQL subscriptions exist but add significant complexity over the current event-driven approach.
- **No event-driven integration**: GraphQL mutations are request/response. They do not support the transactional outbox pattern, event replay, or dead letter queues.
- **Operational complexity**: A GraphQL server must be deployed, scaled, and monitored for an internal processing pipeline. This adds infrastructure overhead.
- **Performance overhead**: GraphQL query parsing and validation add latency to every stage transition. For a pipeline that already takes minutes (AI provider latency), this overhead is unnecessary.
- **Schema Registry incompatibility**: Redpanda Schema Registry works with JSON Schema, Avro, and Protobuf — not GraphQL. The event-driven architecture would lose schema enforcement at the broker level.
- **Overkill for internal pipeline**: GraphQL is designed for frontend-backend communication where client needs vary. In the AI pipeline, every consumer needs most of the Canonical Story. Over-fetching is not a concern.

**Rejection rationale**: GraphQL is a powerful tool for API gateways and frontend communication, but it is not designed for asynchronous, event-driven internal pipelines. The synchronous request/response model is incompatible with the queue-driven AI platform architecture (ADR-004). JSON Schema provides the validation and documentation benefits of GraphQL without the operational overhead and architectural mismatch.

# Consequences

## Positive

1. **Single source of truth for all AI output**: Every downstream artifact (knowledge objects, articles, graph nodes, embeddings) originates from the same Canonical Story JSON. There is no ambiguity about which data is authoritative.

2. **No interface proliferation**: 6 pipeline stages × 1 contract = 6 integrations. With separate contracts, 6 stages × 5 interfaces = 15 integration pairs. The single contract reduces integration complexity by 60%.

3. **Provenance chain integrity**: The Canonical Story schema enforces provenance at every level. Every entity, claim, and belief includes evidence references to source transcript segments. The provenance chain cannot be accidentally dropped during translation.

4. **Schema validation at every stage**: Validation is not optional. Every pipeline stage validates input/output against the schema. Malformed Canonical Stories are caught at the stage boundary, not propagated downstream.

5. **Human-readable and debuggable**: The Canonical Story JSON can be read by engineers, researchers, and editors directly. No special decoding tools needed. Production debugging is straightforward — read the JSON from PostgreSQL.

6. **JSONB storage enables flexible querying**: Canonical Stories stored as JSONB in PostgreSQL can be queried with JSON path expressions, indexed with GIN indexes, and analyzed with SQL JSON functions. This enables ad-hoc analysis without schema changes.

7. **Direct mapping to all downstream stores**: Canonical Story fields map directly to PostgreSQL columns, Neo4j node properties, and Weaviate class properties. No intermediate mapping layer is needed. This simplifies both initial implementation and ongoing maintenance.

8. **Immutable versioning**: Each Canonical Story version is preserved. History is never overwritten. This enables temporal queries, version comparison, and audit trails.

## Negative

1. **Large payload size**: A Canonical Story JSON can be 10KB–100KB depending on the number of entities, claims, and evidence segments. This increases storage costs and event message sizes. Mitigation: store large payloads in PostgreSQL and pass only the ID in events (ADR-004 Rule 2).

2. **Rigid schema evolution**: MAJOR version changes (renaming fields, removing fields, changing types) require coordinated updates across all 6+ pipeline stages. This slows down schema evolution compared to stage-specific contracts.

3. **Validation overhead**: Every pipeline stage validates against the JSON Schema. For a 100KB Canonical Story with dozens of entities and claims, schema validation takes 5–50ms per stage. Across 6 stages, this adds 30–300ms of validation latency.

4. **Over-fetching for simple consumers**: The graph projection worker only needs entity names and relationships, but receives the full Canonical Story including full transcript text, extraction metadata, and research gaps. This is acceptable for an internal pipeline but represents wasted I/O.

5. **Schema complexity**: The Canonical Story schema is large (690+ lines of JSON Schema, 20+ object types, deep nesting). Developers must understand the full schema even if their stage only uses a subset.

6. **Coordination overhead for schema changes**: Adding a field to the Canonical Story requires updating the schema file, the extraction service, and potentially all downstream consumers. Even optional fields require consumer awareness to handle the new field.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Integration complexity** | 1 contract × 6 stages vs. 15 interface pairs | Rigid schema evolution coordination |
| **Provenance integrity** | Structural enforcement at every level | Large payload size from evidence arrays |
| **Human readability** | JSON readable by all roles | Larger payload than binary formats |
| **Schema validation** | Errors caught at stage boundaries | 5–50ms validation latency per stage |
| **Schema evolution** | Additive changes are safe | MAJOR changes require multi-stage coordination |
| **Storage flexibility** | JSONB enables ad-hoc queries | Cannot use all PostgreSQL features on nested JSONB |
| **Downstream mapping** | Direct mapping, no translation layer | Over-fetching for simple consumers |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Schema validation becomes a bottleneck** | Low | Medium — increased pipeline latency | Cache compiled schema. Validate in parallel where possible. Benchmark validation time. Consider schema subset validation for time-critical paths. |
| **Canonical Story JSON exceeds PostgreSQL JSONB size limit** | Low | Critical — cannot store story | PostgreSQL JSONB limit is ~1GB. Canonical Stories are 10KB–100KB. Only at extreme scale (10,000+ entities per story) would this be an issue. Monitor story size. |
| **Schema evolution causes consumer breakage** | Medium | High — pipeline stall | Strict semantic versioning. Grace period for MINOR changes. Dual-mode deployment for MAJOR changes. Schema Registry enforcement. |
| **Evidence text duplicates transcript storage** | High | Medium — increased storage cost | Evidence text is a subset of the full transcript. Storage increase is 2–5× per story. Mitigation: store evidence as segment indices only, resolve text at query time. But this breaks self-contained Canonical Story principle. Accept the trade-off. |
| **Deep JSON nesting causes slow query performance** | Medium | Medium — slow PostgreSQL queries | Use JSON path expressions with GIN indexes. Avoid queries that traverse the full JSONB for every request. Extract frequently-queried fields to indexed columns. |
| **Inconsistent field presence across pipeline stages** | Medium | Medium — some consumers get incomplete data | Schema validation catches missing required fields. For optional fields, implement default values. Log warnings when optional fields are missing. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Schema file becomes out of sync with actual production data** | Low | High — validation fails silently | CI/CD pipeline runs schema validation against production sample data. Schema is the source of truth — all changes start with the schema file. |
| **Developer adds field to Canonical Story without updating downstream consumers** | Medium | Medium — new field not processed | Mandatory code review for schema changes. Add integration test that verifies all consumers handle the new field. Schema Registry alerts on unrecognized fields. |
| **Canonical Story version history grows unbounded** | Medium | Low — storage growth over time | Implement archiving policy: keep last N versions online, archive older versions to cold storage. Monitor version count per transcript. |
| **Human review of Canonical Story JSON is impractical for non-technical reviewers** | High | High — reviewers cannot interpret the JSON | Build review UI that renders Canonical Story as a structured form, not raw JSON. The JSON is the contract for engineering. The UI is the contract for reviewers. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Schema becomes too large to manage effectively** | Schema changes become slow and risky | Split into modular sub-schemas (story-core, entities, claims, provenance) that compose into the full Canonical Story. Each sub-schema can evolve independently within version constraints. |
| **New pipeline stage needs data not in Canonical Story** | Stage cannot be added without schema change | Add field to Canonical Story schema (PATCH or MINOR version). The new field is optional — existing stages ignore it. |
| **Real-time processing requires subset of Canonical Story** | Full schema validation on real-time path is too slow | Define a "lightweight" Canonical Story profile for real-time paths. Validate against the full schema asynchronously. The lightweight profile is a subset, not a separate contract. |
| **Multiple Canonical Story versions need to be compared** | Version comparison requires custom tooling | Build version diff tools that compare two Canonical Story versions and highlight changes in entities, claims, and evidence. This is a research feature for Phase 3. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Canonical Story schema becomes too large**: If the schema exceeds 2,000 lines or 30 object types, consider splitting into modular sub-schemas. The full Canonical Story becomes a composition of sub-schemas.

2. **Schema validation latency exceeds pipeline tolerance**: If 6 stages × 50ms validation = 300ms added latency becomes problematic (unlikely, since AI provider calls take 10–120 seconds), consider optimized validation (compiled schemas, subset validation, parallel validation).

3. **New technology requires different contract format**: If a future technology (e.g., a graph neural network training pipeline) requires a different data format (e.g., TFRecord, Parquet), the Canonical Story can be exported to that format. The Canonical Story JSON remains the source of truth; the export is a derived format.

4. **Real-time AI features require lightweight contract**: If the platform introduces real-time AI features (ADR-004 Future Revisions), a lightweight subset of the Canonical Story may be needed for the real-time path. The lightweight version is a profile of the full schema, not a separate contract.

