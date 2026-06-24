# Canonical Story Specification

## The Living Atlas of Indonesian Mystery Culture

**Version:** 1.0  
**Status:** Draft  
**Owner:** AI Platform Team  
**Classification:** Principal Data Architecture Document

---

# Table of Contents

1. [Purpose](#1-purpose)
2. [Design Principles](#2-design-principles)
3. [Canonical Story Lifecycle](#3-canonical-story-lifecycle)
4. [Canonical Story JSON Schema](#4-canonical-story-json-schema)
5. [Entity Model](#5-entity-model)
6. [Claim Model](#6-claim-model)
7. [Contradiction Model](#7-contradiction-model)
8. [Provenance Model](#8-provenance-model)
9. [Confidence Scoring](#9-confidence-scoring)
10. [Mapping Rules](#10-mapping-rules)
11. [Versioning Rules](#11-versioning-rules)
12. [Validation Rules](#12-validation-rules)
13. [Future Compatibility](#13-future-compatibility)

---

# 1. Purpose

## 1.1 Why Canonical Story Exists

The Canonical Story is the **single source of truth** for all cultural knowledge in The Living Atlas. It is the output of the AI extraction pipeline and the input to every downstream system.

A Canonical Story is NOT:
- A transcript (raw, unstructured, speaker-dependent).
- An article (polished, editorialized, audience-specific).
- A knowledge graph node (projected, relational, indexed).
- A vector embedding (numerical, semantic, lossy).

A Canonical Story IS:
- A structured, provenance-tracked, evidence-grounded representation of a cultural narrative extracted from a source transcript.
- An immutable record of what was said, by whom, with what confidence, and what cultural knowledge can be derived.
- The foundational data asset from which all other artifacts (articles, graph nodes, embeddings, analytics) are derived.

## 1.2 Why All Downstream Systems Depend on Canonical Story

```
                    ┌─────────────────────────────┐
                    │     CANONICAL STORY          │
                    │     (Single Source of Truth) │
                    └──────────┬──────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  PostgreSQL   │   │    Neo4j     │   │   Weaviate   │
    │  (Relational) │   │  (Graph)     │   │  (Vectors)   │
    │               │   │              │   │              │
    │  stories      │   │  Story node  │   │  Story       │
    │  entities     │   │  Entity node │   │  embedding   │
    │  claims       │   │  Claim node  │   │  Entity      │
    │  evidence     │   │  Relations   │   │  embedding   │
    │  versions     │   │  Provenance  │   │  Article     │
    └──────┬───────┘   └──────┬───────┘   │  embedding   │
           │                  │           └──────┬───────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Articles    │   │  Research    │   │   Search     │
    │  (4 types)   │   │  Analytics   │   │  Semantic    │
    └──────────────┘   └──────────────┘   └──────────────┘
```

| Downstream System | Depends On | Why |
|------------------|-----------|-----|
| **PostgreSQL (content-service)** | Canonical Story → Story entity | The `stories` table is the operational record. Every story in the system originates from a Canonical Story. |
| **PostgreSQL (knowledge-service)** | Canonical Story → Knowledge Objects | Entities, themes, motifs, claims, beliefs, rituals are extracted from the Canonical Story. |
| **Neo4j (knowledge graph)** | Canonical Story → Graph projection | Nodes (stories, entities, themes) and relationships (associated_with, appears_in, contradicts) are derived from the Canonical Story. |
| **Weaviate (vector search)** | Canonical Story → Embeddings | Story embeddings, entity embeddings, and article embeddings are generated from Canonical Story content. |
| **Article Service** | Canonical Story → Article generation | All 4 article types (narrative, knowledge, news, creative) are generated from the validated Canonical Story. |
| **Search** | Canonical Story → Indexed fields | Full-text search indexes story titles, summaries, entities, and claims from the Canonical Story. |
| **Analytics** | Canonical Story → Metrics | Cultural trend analysis, entity frequency, theme distribution, and research gap detection all query Canonical Story data. |
| **Future ML Pipelines** | Canonical Story → Training data | Story DNA, narrative genome, adaptation intelligence, and cultural evolution models train on Canonical Story datasets. |

---

# 2. Design Principles

## 2.1 Source of Truth

The Canonical Story is the authoritative record. All downstream representations (relational rows, graph nodes, vector embeddings, article text) are **derived projections**. If a discrepancy exists between any derived artifact and the Canonical Story, the Canonical Story wins.

**Rule:** Never modify a derived artifact directly. Always modify the Canonical Story and regenerate.

## 2.2 Non-Hallucination

The AI extraction prompt explicitly forbids invention. The Canonical Story schema enforces this structurally:

- Every `claim` must reference at least one `evidence` segment.
- Every `entity` must have a `provenance` field linking to source transcript text.
- Every `confidence` score must reflect the AI's uncertainty, not a fabricated certainty.
- The `uncertainties` array captures what is unknown — explicitly.

**Rule:** If the transcript does not support a claim, the claim MUST NOT appear in the Canonical Story. Period.

## 2.3 Provenance First

Every piece of data in the Canonical Story is traceable to its source:

```
Knowledge Object → Claim → Evidence → Transcript Segment → Transcript → Source
```

This chain is **mandatory**, not optional. Any data point that cannot be traced to a source transcript segment is excluded from the Canonical Story.

**Rule:** Provenance is not metadata. Provenance is structural. Every extraction must include `provenance` with `sourceId`, `transcriptId`, `segmentIndex`, and `text`.

## 2.4 Immutable History

Once created, a Canonical Story version is **never modified**. Corrections, enrichments, and updates create new versions. The full version history is preserved.

**Rule:** No UPDATE on Canonical Story records. Only INSERT (new version) and soft DELETE (admin only).

## 2.5 Cultural Sensitivity

Indonesian mystery culture spans hundreds of ethnic groups, languages, and belief systems. The Canonical Story model respects this diversity:

- Entity names are stored in their **original language** alongside normalized forms.
- Regional variants are preserved, not merged without evidence.
- Beliefs are attributed to specific communities, not generalized.
- Cultural context is captured in the `culturalContext` field.

**Rule:** Never normalize away cultural specificity. "Kuntilanak" in Java and "Pontianak" in Kalimantan are distinct cultural expressions — preserve both.

## 2.6 Contradiction Preservation

Contradictions are **features, not bugs**. Indonesian folklore is rich with contradictory accounts — different regions, different witnesses, different eras. The Canonical Story captures contradictions explicitly:

- Two witnesses may describe the same entity differently.
- Historical accounts may conflict with modern interpretations.
- Different regions may have opposing beliefs about the same phenomenon.

**Rule:** Contradictions are preserved, not resolved. The `contradictions` array is a first-class citizen of the schema.

## 2.7 Evidence-Based Extraction

Every extraction decision must be grounded in evidence from the source transcript:

| Extraction | Evidence Required | Example |
|-----------|------------------|---------|
| Entity | At least 1 transcript segment naming the entity | "Saya melihat Kuntilanak..." |
| Claim | At least 1 transcript segment supporting the claim | "Waktu itu jam 11 malam..." |
| Theme | At least 2 transcript segments exhibiting the theme | Multiple mentions of "pemakaman" |
| Belief | At least 1 transcript segment expressing the belief | "Kami percaya Kuntilanak menjaga makam" |
| Contradiction | At least 2 segments with conflicting information | Witness A says "putih", Witness B says "hitam" |

**Rule:** Zero-evidence extractions are hallucinations. The schema rejects them at the validation gate.

---

# 3. Canonical Story Lifecycle

## 3.1 Lifecycle Flow

```
Transcript
   │
   ▼
┌──────────────────────────────────────────────────────────────┐
│                   CANONICAL STORY EXTRACTION                  │
│                                                              │
│  Input:  Normalized transcript + metadata                    │
│  Model:  AI Provider (Gemini/Claude/OpenAI)                  │
│  Prompt: story_canonicalization (v1.x.x)                     │
│  Output: CanonicalStory JSON (v1 schema)                     │
│  State:  EXTRACTED                                           │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE EXTRACTION                        │
│                                                              │
│  Input:  CanonicalStory JSON                                 │
│  Output: Entities, Themes, Motifs, Claims, Rituals, Beliefs  │
│  State:  KNOWLEDGE_EXTRACTED                                 │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE NORMALIZATION                     │
│                                                              │
│  Input:  Raw extracted knowledge                             │
│  Output: Normalized entities, resolved aliases, merged dupes │
│  State:  NORMALIZED                                          │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE VALIDATION                        │
│                                                              │
│  Input:  Normalized CanonicalStory + Knowledge               │
│  Output: Validation report, quality score, warnings          │
│  State:  VALIDATED (or REVIEW_NEEDED)                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   PERSISTENCE (PostgreSQL)                    │
│                                                              │
│  Write: stories, entities, claims, evidence, versions        │
│  State: PERSISTED                                            │
└──────────────────────────┬───────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌──────────────────────┐   ┌──────────────────────┐
│  ARTICLE GENERATION  │   │  GRAPH PROJECTION    │
│                      │   │                      │
│  4 article types     │   │  Neo4j nodes + edges │
│  State: PUBLISHED    │   │  State: PROJECTED    │
└──────────────────────┘   └──────────────────────┘
              │                         │
              ▼                         ▼
┌──────────────────────┐   ┌──────────────────────┐
│  EMBEDDING GENERATION│   │  EMBEDDING GENERATION│
│                      │   │                      │
│  Story embeddings    │   │  Entity embeddings   │
│  Article embeddings  │   │  Knowledge embeddings│
└──────────────────────┘   └──────────────────────┘
```

## 3.2 State Machine

| State | Description | Downstream Actions |
|-------|-------------|-------------------|
| `EXTRACTED` | Raw Canonical Story from AI | Knowledge extraction queued |
| `KNOWLEDGE_EXTRACTED` | Entities, claims, themes extracted | Normalization queued |
| `NORMALIZED` | Aliases resolved, duplicates merged | Validation queued |
| `VALIDATED` | Quality check passed | Persistence queued |
| `REVIEW_NEEDED` | Quality below threshold | Human review required |
| `PERSISTED` | Written to PostgreSQL | Article + graph + embedding queued |
| `ARTICLES_GENERATED` | All article types created | Embedding queued |
| `PROJECTED` | Graph projection complete | Embedding queued |
| `EMBEDDED` | All embeddings generated | Pipeline complete |
| `FINISHED` | Full lifecycle done | — |
| `FAILED` | Irrecoverable error | Operator intervention |

## 3.3 Event Emissions

Each state transition emits a domain event (see `domain-event-catalog.md`):

| Transition | Event |
|-----------|-------|
| Transcript → Canonical Story | `CanonicalStoryExtracted` |
| Canonical Story → Knowledge | `KnowledgeExtracted` |
| Knowledge → Normalized | `KnowledgeNormalized` |
| Normalized → Validated | `KnowledgeValidated` |
| Validated → Persisted | (internal write) |
| Persisted → Articles | `ArticleGenerationRequested` |
| Persisted → Graph | `GraphProjectionRequested` |
| Articles/Graph → Embeddings | `EmbeddingGenerationRequested` |

---

# 4. Canonical Story JSON Schema

## 4.1 Full JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://livingatlas.id/schemas/canonical-story-v1.json",
  "title": "CanonicalStory",
  "description": "The canonical representation of a cultural narrative extracted from a source transcript.",
  "type": "object",
  "required": [
    "canonicalStoryId",
    "sourceId",
    "transcriptId",
    "story",
    "entities",
    "claims",
    "provenance",
    "metadata"
  ],
  "properties": {
    "canonicalStoryId": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this Canonical Story version"
    },
    "sourceId": {
      "type": "string",
      "format": "uuid",
      "description": "The source this story was extracted from"
    },
    "transcriptId": {
      "type": "string",
      "format": "uuid",
      "description": "The transcript this story was extracted from"
    },
    "version": {
      "type": "integer",
      "minimum": 1,
      "description": "Version number of this Canonical Story (immutable, increments on each extraction)"
    },
    "extractedAt": {
      "type": "string",
      "format": "date-time",
      "description": "ISO8601 timestamp of extraction"
    },
    "extractionMetadata": {
      "type": "object",
      "required": ["modelUsed", "promptVersion", "inputTokens", "outputTokens", "executionCost"],
      "properties": {
        "modelUsed": { "type": "string" },
        "promptVersion": { "type": "string" },
        "inputTokens": { "type": "integer" },
        "outputTokens": { "type": "integer" },
        "executionCost": { "type": "number" },
        "executionTimeMs": { "type": "integer" },
        "qualityScore": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    },
    "story": {
      "type": "object",
      "description": "The core narrative structure",
      "required": ["title", "summary", "language", "narrativeType"],
      "properties": {
        "title": { "type": "string", "description": "Extracted story title in original language" },
        "titleEn": { "type": "string", "description": "English translation of title (if applicable)" },
        "summary": { "type": "string", "description": "Concise summary of the story (2-3 sentences)" },
        "language": { "type": "string", "description": "ISO 639-1 language code (e.g., 'id', 'en', 'jv')" },
        "narrativeType": {
          "type": "string",
          "enum": ["first_person", "third_person", "interview", "legend", "myth", "folktale", "ritual_description", "mixed"],
          "description": "The narrative structure type"
        },
        "tone": {
          "type": "string",
          "enum": ["factual", "legendary", "personal", "instructional", "cautionary", "humorous", "reverent"],
          "description": "The emotional or rhetorical tone"
        },
        "culturalContext": {
          "type": "object",
          "properties": {
            "region": { "type": "string", "description": "Geographic region (e.g., 'Jawa Timur', 'Kalimantan Barat')" },
            "ethnicGroup": { "type": "string", "description": "Ethnic group (e.g., 'Jawa', 'Dayak', 'Sunda')" },
            "religiousTradition": { "type": "string", "description": "Religious or spiritual tradition" },
            "timePeriod": { "type": "string", "description": "When the story is set (e.g., '2019', 'colonial era', 'contemporary')" }
          }
        },
        "witnesses": {
          "type": "array",
          "description": "People who provided testimony in the source",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "role": { "type": "string", "description": "e.g., 'witness', 'elder', 'shaman', 'researcher'" },
              "age": { "type": "string" },
              "origin": { "type": "string", "description": "Village or community" }
            }
          }
        },
        "keyEvents": {
          "type": "array",
          "description": "Chronological or thematic sequence of events in the story",
          "items": {
            "type": "object",
            "required": ["description", "order"],
            "properties": {
              "order": { "type": "integer", "description": "Sequence position" },
              "description": { "type": "string" },
              "timestamp": { "type": "string", "description": "When the event occurred (if known)" },
              "location": { "type": "string", "description": "Where the event occurred" },
              "participants": { "type": "array", "items": { "type": "string" } }
            }
          }
        }
      }
    },
    "entities": {
      "type": "array",
      "description": "All named entities extracted from the story",
      "items": { "$ref": "#/definitions/Entity" }
    },
    "locations": {
      "type": "array",
      "description": "Geographic locations mentioned in the story",
      "items": {
        "type": "object",
        "required": ["name", "entityId"],
        "properties": {
          "entityId": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "nameLocal": { "type": "string", "description": "Local name (e.g., 'Desa Sukamaju')" },
          "latitude": { "type": "number" },
          "longitude": { "type": "number" },
          "locationType": { "type": "string", "enum": ["village", "city", "forest", "cemetery", "river", "mountain", "cave", "sea", "house", "temple", "other"] },
          "significance": { "type": "string", "description": "Why this location matters to the story" }
        }
      }
    },
    "events": {
      "type": "array",
      "description": "Broader events that contextualize the story",
      "items": {
        "type": "object",
        "properties": {
          "eventId": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "date": { "type": "string" },
          "location": { "type": "string" },
          "entityIds": { "type": "array", "items": { "type": "string", "format": "uuid" } }
        }
      }
    },
    "beliefs": {
      "type": "array",
      "description": "Cultural beliefs expressed in the story",
      "items": {
        "type": "object",
        "required": ["beliefId", "statement", "adherentCommunity", "confidence"],
        "properties": {
          "beliefId": { "type": "string", "format": "uuid" },
          "statement": { "type": "string", "description": "The belief statement" },
          "adherentCommunity": { "type": "string", "description": "Community that holds this belief" },
          "entityIds": { "type": "array", "items": { "type": "string", "format": "uuid" } },
          "confidence": { "type": "integer", "minimum": 0, "maximum": 100 },
          "evidence": { "type": "array", "items": { "$ref": "#/definitions/EvidenceRef" } }
        }
      }
    },
    "rituals": {
      "type": "array",
      "description": "Rituals described in the story",
      "items": {
        "type": "object",
        "required": ["ritualId", "name", "description", "confidence"],
        "properties": {
          "ritualId": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "nameLocal": { "type": "string" },
          "description": { "type": "string" },
          "purpose": { "type": "string", "description": "e.g., 'protection', 'healing', 'exorcism', 'offering'" },
          "steps": { "type": "array", "items": { "type": "string" } },
          "requiredItems": { "type": "array", "items": { "type": "string" } },
          "entityIds": { "type": "array", "items": { "type": "string", "format": "uuid" } },
          "confidence": { "type": "integer", "minimum": 0, "maximum": 100 },
          "evidence": { "type": "array", "items": { "$ref": "#/definitions/EvidenceRef" } }
        }
      }
    },
    "traditions": {
      "type": "array",
      "description": "Broader cultural traditions referenced",
      "items": {
        "type": "object",
        "properties": {
          "traditionId": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "community": { "type": "string" },
          "entityIds": { "type": "array", "items": { "type": "string", "format": "uuid" } }
        }
      }
    },
    "themes": {
      "type": "array",
      "description": "Recurring cultural themes",
      "items": {
        "type": "object",
        "required": ["themeId", "name", "confidence"],
        "properties": {
          "themeId": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "category": { "type": "string", "enum": ["supernatural", "moral", "social", "historical", "natural", "psychological"] },
          "confidence": { "type": "integer", "minimum": 0, "maximum": 100 },
          "evidence": { "type": "array", "items": { "$ref": "#/definitions/EvidenceRef" } }
        }
      }
    },
    "motifs": {
      "type": "array",
      "description": "Narrative motifs (recurring patterns in folklore)",
      "items": {
        "type": "object",
        "required": ["motifId", "name", "motifType", "confidence"],
        "properties": {
          "motifId": { "type": "string", "format": "uuid" },
          "name": { "type": "string" },
          "motifType": { "type": "string", "enum": ["setting", "character", "plot", "symbol", "transformation", "taboo"] },
          "description": { "type": "string" },
          "aatClassification": { "type": "string", "description": "Art & Architecture Thesaurus classification (if applicable)" },
          "confidence": { "type": "integer", "minimum": 0, "maximum": 100 },
          "evidence": { "type": "array", "items": { "$ref": "#/definitions/EvidenceRef" } }
        }
      }
    },
    "claims": {
      "type": "array",
      "description": "Factual claims extracted with supporting evidence",
      "items": { "$ref": "#/definitions/Claim" }
    },
    "contradictions": {
      "type": "array",
      "description": "Explicitly preserved contradictions",
      "items": { "$ref": "#/definitions/Contradiction" }
    },
    "researchGaps": {
      "type": "array",
      "description": "Identified gaps in knowledge that warrant further research",
      "items": {
        "type": "object",
        "properties": {
          "gapId": { "type": "string", "format": "uuid" },
          "description": { "type": "string" },
          "type": { "type": "string", "enum": ["missing_entity_detail", "unresolved_contradiction", "unverified_claim", "insufficient_evidence", "cultural_context_needed"] },
          "severity": { "type": "string", "enum": ["low", "medium", "high"] },
          "relatedEntityIds": { "type": "array", "items": { "type": "string", "format": "uuid" } }
        }
      }
    },
    "uncertainties": {
      "type": "array",
      "description": "Explicitly marked uncertainties in the extraction",
      "items": {
        "type": "object",
        "properties": {
          "targetType": { "type": "string", "enum": ["entity", "claim", "event", "location", "belief", "ritual"] },
          "targetId": { "type": "string", "format": "uuid" },
          "uncertaintyType": { "type": "string", "enum": ["ambiguous_reference", "unclear_timeline", "conflicting_names", "speculative_interpretation", "translation_ambiguity"] },
          "description": { "type": "string" }
        }
      }
    },
    "provenance": {
      "type": "object",
      "description": "Complete provenance chain for this extraction",
      "required": ["sourceId", "transcriptId", "extractionJobId", "promptVersion", "modelUsed"],
      "properties": {
        "sourceId": { "type": "string", "format": "uuid" },
        "transcriptId": { "type": "string", "format": "uuid" },
        "extractionJobId": { "type": "string", "format": "uuid" },
        "promptVersion": { "type": "string" },
        "modelUsed": { "type": "string" },
        "extractedAt": { "type": "string", "format": "date-time" },
        "normalizedAt": { "type": "string", "format": "date-time" },
        "validatedAt": { "type": "string", "format": "date-time" },
        "validationReport": {
          "type": "object",
          "properties": {
            "overallScore": { "type": "number", "minimum": 0, "maximum": 1 },
            "passed": { "type": "boolean" },
            "warnings": { "type": "array", "items": { "type": "object" } }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "description": "System metadata",
      "required": ["tenantId", "correlationId", "schemaVersion"],
      "properties": {
        "tenantId": { "type": "string", "format": "uuid" },
        "correlationId": { "type": "string", "format": "uuid" },
        "schemaVersion": { "type": "string", "description": "Version of this schema (e.g., '1.0.0')" },
        "tags": { "type": "array", "items": { "type": "string" } },
        "notes": { "type": "string" }
      }
    }
  },
  "definitions": {
    "EvidenceRef": {
      "type": "object",
      "required": ["segmentIndex", "text"],
      "properties": {
        "segmentIndex": { "type": "integer", "description": "Index of the transcript segment" },
        "text": { "type": "string", "description": "The exact text from the transcript" },
        "startTime": { "type": "number", "description": "Start time in seconds (if timestamped)" },
        "endTime": { "type": "number", "description": "End time in seconds (if timestamped)" },
        "speaker": { "type": "string", "description": "Speaker who said this (if identified)" }
      }
    },
    "Entity": {
      "type": "object",
      "required": ["entityId", "name", "entityType", "confidence"],
      "properties": {
        "entityId": { "type": "string", "format": "uuid" },
        "name": { "type": "string", "description": "Name as mentioned in the source" },
        "nameLocal": { "type": "string", "description": "Name in local language/dialect" },
        "normalizedName": { "type": "string", "description": "Normalized canonical name (set during normalization)" },
        "aliases": { "type": "array", "items": { "type": "string" }, "description": "Alternative names or spellings" },
        "entityType": {
          "type": "string",
          "enum": ["spirit", "deity", "creature", "person", "location", "object", "phenomenon", "concept", "group", "other"]
        },
        "subtype": { "type": "string", "description": "More specific type (e.g., 'kuntilanak', 'genderuwo', 'jinn')" },
        "description": { "type": "string" },
        "attributes": {
          "type": "object",
          "properties": {
            "appearance": { "type": "string" },
            "behavior": { "type": "string" },
            "habitat": { "type": "string" },
            "powers": { "type": "array", "items": { "type": "string" } },
            "weaknesses": { "type": "array", "items": { "type": "string" } }
          }
        },
        "culturalContext": {
          "type": "object",
          "properties": {
            "region": { "type": "string" },
            "ethnicGroup": { "type": "string" },
            "tradition": { "type": "string" }
          }
        },
        "confidence": { "type": "integer", "minimum": 0, "maximum": 100 },
        "evidence": { "type": "array", "items": { "$ref": "#/definitions/EvidenceRef" } },
        "relationships": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "targetEntityId": { "type": "string", "format": "uuid" },
              "relationType": { "type": "string", "enum": ["associated_with", "manifestation_of", "appears_in", "contradicts", "parent_of", "guardian_of", "enemy_of", "helper_of", "transformation_of", "same_as"] },
              "confidence": { "type": "integer", "minimum": 0, "maximum": 100 },
              "evidence": { "type": "array", "items": { "$ref": "#/definitions/EvidenceRef" } }
            }
          }
        }
      }
    },
    "Claim": {
      "type": "object",
      "required": ["claimId", "statement", "confidence", "evidence"],
      "properties": {
        "claimId": { "type": "string", "format": "uuid" },
        "statement": { "type": "string", "description": "The claim statement" },
        "category": { "type": "string", "enum": ["existence", "behavior", "appearance", "location", "history", "origin", "power", "relationship", "ritual", "belief"] },
        "confidence": { "type": "integer", "minimum": 0, "maximum": 100 },
        "entityIds": { "type": "array", "items": { "type": "string", "format": "uuid" }, "description": "Entities this claim references" },
        "evidence": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/EvidenceRef" }
        },
        "status": { "type": "string", "enum": ["extracted", "normalized", "validated", "disputed", "verified", "rejected"] },
        "validationState": { "type": "string", "enum": ["unreviewed", "auto_passed", "auto_failed", "human_passed", "human_failed"] },
        "reviewState": { "type": "string", "enum": ["not_required", "pending", "approved", "rejected"] }
      }
    },
    "Contradiction": {
      "type": "object",
      "required": ["contradictionId", "type", "description", "sides"],
      "properties": {
        "contradictionId": { "type": "string", "format": "uuid" },
        "type": {
          "type": "string",
          "enum": ["regional", "historical", "source", "interpretation", "witness", "temporal"]
        },
        "description": { "type": "string" },
        "sides": {
          "type": "array",
          "minItems": 2,
          "items": {
            "type": "object",
            "required": ["label", "statement", "evidence"],
            "properties": {
              "label": { "type": "string", "description": "e.g., 'Witness A', 'Region Java', 'Historical account 1800s'" },
              "statement": { "type": "string" },
              "entityIds": { "type": "array", "items": { "type": "string", "format": "uuid" } },
              "evidence": { "type": "array", "items": { "$ref": "#/definitions/EvidenceRef" } },
              "sourceDescription": { "type": "string" }
            }
          }
        },
        "resolution": { "type": "string", "description": "If resolved, how (null if unresolved)" },
        "severity": { "type": "string", "enum": ["low", "medium", "high"] }
      }
    }
  }
}
```

## 4.2 Complete JSON Example

```json
{
  "canonicalStoryId": "c5d6e7f8-a9b0-1234-efab-345678901234",
  "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
  "transcriptId": "d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b",
  "version": 1,
  "extractedAt": "2026-06-20T15:08:30.000Z",
  "extractionMetadata": {
    "modelUsed": "gemini-2.5-pro",
    "promptVersion": "story-canonicalization-v3",
    "inputTokens": 4502,
    "outputTokens": 1280,
    "executionCost": 0.0032,
    "executionTimeMs": 12450,
    "qualityScore": 0.88
  },
  "story": {
    "title": "Penampakan Kuntilanak di Pemakaman Desa Sukamaju",
    "titleEn": "Kuntilanak Sighting at Sukamaju Village Cemetery",
    "summary": "Pak Sariman, a farmer in Sukamaju Village, recounts his experience seeing a Kuntilanak at the village cemetery in 2019. The entity appeared as a long-haired woman in a white dress and vanished when approached.",
    "language": "id",
    "narrativeType": "first_person",
    "tone": "factual",
    "culturalContext": {
      "region": "Jawa Timur",
      "ethnicGroup": "Jawa",
      "religiousTradition": "Kejawen",
      "timePeriod": "2019"
    },
    "witnesses": [
      {
        "name": "Pak Sariman",
        "role": "witness",
        "age": "45",
        "origin": "Desa Sukamaju"
      }
    ],
    "keyEvents": [
      {
        "order": 1,
        "description": "Pak Sariman returns from rice fields at 11 PM",
        "timestamp": "2019-03-15T23:00:00",
        "location": "Sawah (rice field) near cemetery",
        "participants": ["Pak Sariman"]
      },
      {
        "order": 2,
        "description": "Sees a white figure among the gravestones",
        "location": "Desa Sukamaju cemetery",
        "participants": ["Pak Sariman"]
      },
      {
        "order": 3,
        "description": "Figure approaches, reveals itself as a woman with long black hair in white dress",
        "location": "Desa Sukamaju cemetery"
      },
      {
        "order": 4,
        "description": "Figure vanishes when Pak Sariman recites a prayer",
        "location": "Desa Sukamaju cemetery"
      }
    ]
  },
  "entities": [
    {
      "entityId": "c9d0e1f2-3456-7bcd-8901-234567890123",
      "name": "Kuntilanak",
      "nameLocal": "Kuntilanak",
      "normalizedName": "Kuntilanak",
      "aliases": ["Pontianak", "Kunti"],
      "entityType": "spirit",
      "subtype": "kuntilanak",
      "description": "A female vengeful spirit in Indonesian mythology, often depicted as a woman with long black hair and a white dress",
      "attributes": {
        "appearance": "Wanita berambut panjang dengan gaun putih",
        "behavior": "Appears at night, especially near cemeteries; may attack pregnant women",
        "habitat": "Cemeteries, abandoned buildings, forests",
        "powers": ["shapeshifting", "invisibility", "possession"],
        "weaknesses": ["prayers", "sharp objects", "nail"]
      },
      "culturalContext": {
        "region": "Jawa Timur",
        "ethnicGroup": "Jawa",
        "tradition": "Kejawen"
      },
      "confidence": 95,
      "evidence": [
        {
          "segmentIndex": 2,
          "text": "saya lihat sosok perempuan berambut panjang pakai baju putih",
          "startTime": 46.0,
          "endTime": 52.3,
          "speaker": "Pak Sariman"
        }
      ],
      "relationships": [
        {
          "targetEntityId": "d0e1f2a3-4567-8cde-9012-345678901234",
          "relationType": "associated_with",
          "confidence": 80,
          "evidence": [
            {
              "segmentIndex": 3,
              "text": "Kuntilanak itu sering muncul di pemakaman",
              "startTime": 60.0,
              "endTime": 65.0,
              "speaker": "Pak Sariman"
            }
          ]
        }
      ]
    },
    {
      "entityId": "d0e1f2a3-4567-8cde-9012-345678901234",
      "name": "Pak Sariman",
      "entityType": "person",
      "description": "Petani (farmer) from Sukamaju Village, primary witness",
      "confidence": 98,
      "evidence": [
        {
          "segmentIndex": 0,
          "text": "Selamat malam, Pak Sariman",
          "startTime": 0.0,
          "endTime": 3.0,
          "speaker": "Pewawancara"
        }
      ]
    }
  ],
  "locations": [
    {
      "entityId": "e1f2a3b4-5678-9def-0123-456789012345",
      "name": "Desa Sukamaju",
      "nameLocal": "Desa Sukamaju",
      "locationType": "village",
      "significance": "Home village of the witness and location of the sighting"
    },
    {
      "entityId": "f2a3b4c5-6789-0efa-1234-567890123456",
      "name": "Pemakaman Desa Sukamaju",
      "nameLocal": "Pemakaman Desa Sukamaju",
      "locationType": "cemetery",
      "significance": "Location of the Kuntilanak sighting"
    }
  ],
  "events": [],
  "beliefs": [
    {
      "beliefId": "a3b4c5d6-e789-0f12-3456-789012345678",
      "statement": "Kuntilanak menjaga area pemakaman dan muncul kepada mereka yang melintas di malam hari",
      "adherentCommunity": "Warga Desa Sukamaju",
      "entityIds": ["c9d0e1f2-3456-7bcd-8901-234567890123"],
      "confidence": 75,
      "evidence": [
        {
          "segmentIndex": 4,
          "text": "menurut warga sini, Kuntilanak itu penjaga makam",
          "startTime": 80.0,
          "endTime": 85.0,
          "speaker": "Pak Sariman"
        }
      ]
    }
  ],
  "rituals": [],
  "traditions": [],
  "themes": [
    {
      "themeId": "b4c5d6e7-f890-1234-5678-901234567890",
      "name": "Penampakan Mistis di Area Pemakaman",
      "description": "Supernatural sightings in cemetery areas, a common theme in Indonesian folklore",
      "category": "supernatural",
      "confidence": 92,
      "evidence": [
        {
          "segmentIndex": 2,
          "text": "saya lihat sosok perempuan...",
          "startTime": 46.0,
          "endTime": 52.3
        }
      ]
    }
  ],
  "motifs": [
    {
      "motifId": "c5d6e7f8-9012-3456-7890-123456789012",
      "name": "Penampakan di Pemakaman",
      "motifType": "setting",
      "description": "Cemetery as the setting for supernatural encounters",
      "confidence": 78,
      "evidence": [
        {
          "segmentIndex": 2,
          "text": "waktu itu saya pulang dari sawah jam 11 malam...",
          "startTime": 46.0,
          "endTime": 120.5
        }
      ]
    }
  ],
  "claims": [
    {
      "claimId": "d6e7f8a9-0123-4567-8901-234567890123",
      "statement": "Kuntilanak muncul di pemakaman Desa Sukamaju pada tahun 2019 sekitar jam 11 malam",
      "category": "existence",
      "confidence": 85,
      "entityIds": ["c9d0e1f2-3456-7bcd-8901-234567890123", "f2a3b4c5-6789-0efa-1234-567890123456"],
      "evidence": [
        {
          "segmentIndex": 2,
          "text": "waktu itu tahun 2019, saya pulang dari sawah jam 11 malam...",
          "startTime": 46.0,
          "endTime": 120.5,
          "speaker": "Pak Sariman"
        }
      ],
      "status": "extracted",
      "validationState": "unreviewed",
      "reviewState": "not_required"
    }
  ],
  "contradictions": [],
  "researchGaps": [
    {
      "gapId": "e7f8a9b0-1234-5678-9012-345678901234",
      "description": "Only one witness account available; corroborating witnesses needed",
      "type": "insufficient_evidence",
      "severity": "medium",
      "relatedEntityIds": ["c9d0e1f2-3456-7bcd-8901-234567890123"]
    }
  ],
  "uncertainties": [
    {
      "targetType": "entity",
      "targetId": "c9d0e1f2-3456-7bcd-8901-234567890123",
      "uncertaintyType": "ambiguous_reference",
      "description": "Witness referred to entity as both 'Kuntilanak' and 'hantu perempuan' — exact classification uncertain"
    }
  ],
  "provenance": {
    "sourceId": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
    "transcriptId": "d4c3b2a1-0f9e-8d7c-6b5a-4c3d2e1f0a9b",
    "extractionJobId": "e5f6a7b8-c901-2def-3456-789012345678",
    "promptVersion": "story-canonicalization-v3",
    "modelUsed": "gemini-2.5-pro",
    "extractedAt": "2026-06-20T15:08:30.000Z",
    "normalizedAt": null,
    "validatedAt": null,
    "validationReport": null
  },
  "metadata": {
    "tenantId": "00000000-0000-0000-0000-000000000001",
    "correlationId": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "schemaVersion": "1.0.0",
    "tags": ["kuntilanak", "cemetery", "jawa-timur", "first-person"],
    "notes": "Initial extraction, pending normalization and validation"
  }
}
```

---

# 5. Entity Model

## 5.1 Entity Definition

An **Entity** is any named thing in a Canonical Story that has cultural significance. Entities are the building blocks of the knowledge graph.

### Entity Type Taxonomy

```
spirit
├── kuntilanak / pontianak
├── genderuwo
├── pocong
├── tuyul
├── wewe / gandarwa
├── leak
├── babi ngepet
├── jelangkung
└── other

deity
├── dewi
├── hyang
├── roh leluhur
└── other

creature
├── naga
├── garuda
├── buto
└── other

person
├── witness
├── elder
├── shaman / dukun
├── researcher
└── other

location
├── village
├── cemetery
├── forest
├── river
├── mountain
├── cave
├── sea
├── house
├── temple
└── other

object
├── weapon (keris, etc.)
├── talisman
├── offering
└── other

phenomenon
├── natural
├── supernatural
└── other

concept
├── belief
├── value
├── taboo
└── other

group
├── ethnic group
├── community
├── organization
└── other
```

## 5.2 Entity Identity Resolution

Entities go through a three-stage identity resolution:

```
Stage 1: Raw Extraction
  Name as mentioned: "Kuntilanak", "hantu perempuan", "si Kunti"
  → Multiple raw entity records, potentially duplicates

Stage 2: Normalization
  Alias detection: "Kuntilanak" = "Pontianak" = "Kunti"
  → Merged into single entity with aliases array

Stage 3: Canonical Identity
  Canonical name: "Kuntilanak"
  Normalized name: "Kuntilanak"
  → Single canonical entity with full alias history
```

### Entity Identity Table

```sql
CREATE TABLE knowledge.entity_identities (
    entity_id UUID PRIMARY KEY,
    canonical_name VARCHAR(500) NOT NULL,
    normalized_name VARCHAR(500) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    subtype VARCHAR(100),
    description TEXT,
    attributes JSONB,
    cultural_context JSONB,
    confidence_score INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'extracted',
    -- provenance
    source_id UUID NOT NULL,
    canonical_story_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge.entity_aliases (
    alias_id UUID PRIMARY KEY,
    entity_id UUID NOT NULL REFERENCES knowledge.entity_identities(entity_id),
    alias VARCHAR(500) NOT NULL,
    language VARCHAR(10),
    region VARCHAR(200),
    is_primary BOOLEAN NOT NULL DEFAULT false,
    source_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 5.3 Entity Relationship Types

| Relationship | Description | Directional | Example |
|-------------|-------------|-------------|---------|
| `associated_with` | General association | No | Kuntilanak ↔ Cemetery |
| `manifestation_of` | Entity is a form of another | Yes | Kuntilanak → Female Vengeful Spirit |
| `appears_in` | Entity appears in a story | Yes | Kuntilanak → Story-001 |
| `contradicts` | Entity description contradicts another | No | Kuntilanak (Java) ↔ Pontianak (Kalimantan) |
| `parent_of` | Entity is parent/creator of another | Yes | Dewi → Kuntilanak |
| `guardian_of` | Entity guards a location | Yes | Kuntilanak → Cemetery |
| `enemy_of` | Entity is opposed to another | No | Dukun ↔ Kuntilanak |
| `helper_of` | Entity assists another | Yes | Dukun → Victim |
| `transformation_of` | Entity transforms into another | Yes | Woman → Kuntilanak |
| `same_as` | Two entity references refer to the same entity | No | Kuntilanak ↔ Pontianak |

---

# 6. Claim Model

## 6.1 Claim Definition

A **Claim** is a factual statement extracted from the transcript, supported by at least one piece of evidence. Claims are the atomic units of cultural knowledge.

### Claim Categories

| Category | Description | Example |
|----------|-------------|---------|
| `existence` | Entity exists or existed | "Kuntilanak exists in Sukamaju village" |
| `behavior` | Entity behaves in a specific way | "Kuntilanak appears at night" |
| `appearance` | Entity has specific appearance | "Kuntilanak wears a white dress" |
| `location` | Entity is found at a location | "Kuntilanak haunts the cemetery" |
| `history` | Historical event or origin | "The first sighting was in 2019" |
| `origin` | Entity's origin story | "Kuntilanak is the spirit of a woman who died in childbirth" |
| `power` | Entity has supernatural abilities | "Kuntilanak can shapeshift" |
| `relationship` | Relationship between entities | "Kuntilanak guards the cemetery" |
| `ritual` | Ritual practice described | "Offerings are left at the cemetery every Friday night" |
| `belief` | Cultural belief | "Pregnant women should not go out at night" |

## 6.2 Claim Lifecycle

```
EXTRACTED
   │
   ▼
NORMALIZED (aliases resolved, duplicates merged)
   │
   ▼
VALIDATED (quality check)
   │
   ├──→ VERIFIED (passed validation)
   │
   └──→ DISPUTED (contradiction detected)
          │
          ├──→ VERIFIED (contradiction resolved)
          │
          └──→ REJECTED (contradiction confirmed)
```

## 6.3 Claim Evidence Requirements

| Claim Confidence | Minimum Evidence Segments | Evidence Quality |
|-----------------|--------------------------|-----------------|
| 0-30 | 1 | Any mention, even ambiguous |
| 31-60 | 1 | Clear statement from witness |
| 61-85 | 2 | Corroborating statements |
| 86-100 | 3+ | Multiple independent corroborations |

## 6.4 Claim Example

```json
{
  "claimId": "d6e7f8a9-0123-4567-8901-234567890123",
  "statement": "Kuntilanak muncul di pemakaman Desa Sukamaju pada tahun 2019 sekitar jam 11 malam",
  "category": "existence",
  "confidence": 85,
  "entityIds": [
    "c9d0e1f2-3456-7bcd-8901-234567890123",
    "f2a3b4c5-6789-0efa-1234-567890123456"
  ],
  "evidence": [
    {
      "segmentIndex": 2,
      "text": "waktu itu tahun 2019, saya pulang dari sawah jam 11 malam...",
      "startTime": 46.0,
      "endTime": 120.5,
      "speaker": "Pak Sariman"
    }
  ],
  "status": "extracted",
  "validationState": "unreviewed",
  "reviewState": "not_required"
}
```

---

# 7. Contradiction Model

## 7.1 Contradiction Definition

A **Contradiction** is an explicit record of conflicting information within or across sources. Contradictions are preserved, not resolved.

### Contradiction Types

| Type | Description | Example |
|------|-------------|---------|
| **Regional** | Different regions describe the same entity differently | Java: Kuntilanak wears white; Kalimantan: Pontianak wears black |
| **Historical** | Accounts from different time periods conflict | 1800s: Kuntilanak is a forest spirit; 2020s: Kuntilanak haunts housing complexes |
| **Source** | Different sources provide conflicting information | YouTube witness: Kuntilanak is harmless; Podcast witness: Kuntilanak is deadly |
| **Interpretation** | Same evidence interpreted differently | Scholar A: Kuntilanak is pre-Islamic; Scholar B: Kuntilanak is Islamic |
| **Witness** | Two witnesses in the same source disagree | Witness 1: saw it at midnight; Witness 2: saw it at dawn |
| **Temporal** | Same witness contradicts themselves over time | 2019 interview: "never seen it"; 2023 interview: "seen it many times" |

## 7.2 Contradiction Example

```json
{
  "contradictionId": "f8a9b0c1-2345-6789-0123-456789012345",
  "type": "regional",
  "description": "The appearance of Kuntilanak differs between Javanese and Kalimantan traditions",
  "sides": [
    {
      "label": "Jawa Timur tradition",
      "statement": "Kuntilanak digambarkan sebagai wanita berbaju putih dengan rambut panjang",
      "entityIds": ["c9d0e1f2-3456-7bcd-8901-234567890123"],
      "evidence": [
        {
          "segmentIndex": 2,
          "text": "sosok perempuan berambut panjang pakai baju putih",
          "startTime": 46.0,
          "endTime": 52.3,
          "speaker": "Pak Sariman"
        }
      ],
      "sourceDescription": "Interview with Pak Sariman, Desa Sukamaju, Jawa Timur"
    },
    {
      "label": "Kalimantan Barat tradition",
      "statement": "Pontianak digambarkan sebagai wanita berbaju hitam dengan mata merah menyala",
      "entityIds": ["c9d0e1f2-3456-7bcd-8901-234567890123"],
      "evidence": [
        {
          "segmentIndex": 5,
          "text": "menurut cerita dari Kalimantan, Pontianak itu matanya merah",
          "startTime": 150.0,
          "endTime": 155.0,
          "speaker": "Pewawancara"
        }
      ],
      "sourceDescription": "Interview with cultural researcher, Pontianak, Kalimantan Barat"
    }
  ],
  "resolution": null,
  "severity": "medium"
}
```

## 7.3 Contradiction Resolution

Contradictions may be resolved through:
- **Human review:** Editor determines which side is more credible.
- **Additional evidence:** New sources provide clarifying information.
- **Contextualization:** Both sides are valid in their respective contexts.

When resolved, the `resolution` field is populated but both sides are preserved.

---

# 8. Provenance Model

## 8.1 Provenance Chain

Every piece of data in the Canonical Story is traceable through a complete provenance chain:

```
Knowledge Object
    ↑
    │ references
    │
  Claim
    ↑
    │ supported by
    │
  Evidence
    ↑
    │ points to
    │
  Transcript Segment
    ↑
    │ part of
    │
  Transcript
    ↑
    │ derived from
    │
  Source (YouTube video, podcast, upload)
```

## 8.2 Provenance Data Model

```sql
-- Source: the origin of the content
CREATE TABLE content.sources (
    source_id UUID PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,  -- youtube_video, youtube_channel, podcast_rss, manual_upload
    platform_source_id VARCHAR(500),   -- YouTube video ID, channel ID, etc.
    title VARCHAR(500),
    description TEXT,
    language VARCHAR(10),
    submitted_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Transcript: the text extracted from the source
CREATE TABLE ai_platform.transcripts (
    transcript_id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES content.sources(source_id),
    language VARCHAR(10) NOT NULL,
    transcript_type VARCHAR(50) NOT NULL,  -- manual, youtube_caption, asr_generated, podcast_rss
    text_length INTEGER NOT NULL,
    storage_url VARCHAR(1000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Transcript segments: timestamped chunks of the transcript
CREATE TABLE ai_platform.transcript_segments (
    segment_id UUID PRIMARY KEY,
    transcript_id UUID NOT NULL REFERENCES ai_platform.transcripts(transcript_id),
    segment_index INTEGER NOT NULL,
    start_time DECIMAL(10,3),
    end_time DECIMAL(10,3),
    speaker VARCHAR(255),
    text TEXT NOT NULL,
    confidence DECIMAL(4,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Canonical stories: extracted structured narratives
CREATE TABLE ai_platform.canonical_stories (
    canonical_story_id UUID PRIMARY KEY,
    source_id UUID NOT NULL REFERENCES content.sources(source_id),
    transcript_id UUID NOT NULL REFERENCES ai_platform.transcripts(transcript_id),
    version INTEGER NOT NULL DEFAULT 1,
    story_json JSONB NOT NULL,           -- The full Canonical Story JSON
    extraction_job_id UUID,
    prompt_version VARCHAR(100),
    model_used VARCHAR(100),
    quality_score DECIMAL(4,3),
    status VARCHAR(50) NOT NULL DEFAULT 'extracted',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Evidence: links between claims and transcript segments
CREATE TABLE ai_platform.evidence (
    evidence_id UUID PRIMARY KEY,
    claim_id UUID NOT NULL,              -- FK to claims table
    segment_id UUID NOT NULL REFERENCES ai_platform.transcript_segments(segment_id),
    segment_index INTEGER NOT NULL,      -- Denormalized for fast access
    text_snippet VARCHAR(2000) NOT NULL, -- The exact text used as evidence
    start_time DECIMAL(10,3),
    end_time DECIMAL(10,3),
    speaker VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 8.3 Provenance Query Example

```sql
-- Trace a knowledge object back to its source
SELECT 
    ko.id AS knowledge_object_id,
    ko.canonical_name,
    c.claim_id,
    c.statement AS claim_statement,
    e.text_snippet AS evidence_text,
    ts.segment_index,
    ts.start_time,
    ts.speaker,
    t.transcript_id,
    s.title AS source_title,
    s.platform_source_id,
    s.source_type
FROM knowledge.objects ko
JOIN knowledge.claims c ON c.entity_ids @> ARRAY[ko.id]
JOIN ai_platform.evidence e ON e.claim_id = c.claim_id
JOIN ai_platform.transcript_segments ts ON ts.segment_id = e.segment_id
JOIN ai_platform.transcripts t ON t.transcript_id = ts.transcript_id
JOIN content.sources s ON s.source_id = t.source_id
WHERE ko.id = 'c9d0e1f2-3456-7bcd-8901-234567890123';
```

---

# 9. Confidence Scoring

## 9.1 Scoring Framework

Confidence is scored on a **0–100 integer scale** across three dimensions:

| Dimension | Scope | Source | Range |
|-----------|-------|--------|-------|
| **Extraction Confidence** | Per entity, claim, theme, motif | AI model's self-reported confidence | 0-100 |
| **Validation Confidence** | Per knowledge object | Validation service quality assessment | 0-100 |
| **Editorial Confidence** | Per knowledge object | Human reviewer assessment | 0-100 |

## 9.2 Extraction Confidence

Extraction confidence is the AI model's assessment of how reliably a piece of information was extracted from the source.

| Range | Label | Meaning |
|-------|-------|---------|
| 0-20 | Speculative | Weakly supported, possible hallucination |
| 21-40 | Low | Single ambiguous mention |
| 41-60 | Moderate | Single clear mention |
| 61-80 | High | Multiple mentions, consistent |
| 81-100 | Very High | Multiple independent corroborations, clear evidence |

**Calculation:**
```
ExtractionConfidence = f(
    evidence_count,        // Number of supporting transcript segments
    evidence_quality,      // Clarity and specificity of each segment
    speaker_reliability,   // Primary witness vs hearsay
    cross_references,      // Mentions by different speakers
    model_uncertainty      // AI model's self-reported uncertainty
)
```

## 9.3 Validation Confidence

Validation confidence is assigned by the validation service after quality assessment.

| Range | Label | Meaning |
|-------|-------|---------|
| 0-20 | Rejected | Fails schema validation, hallucination detected |
| 21-40 | Poor | Missing required fields, insufficient evidence |
| 41-60 | Fair | Meets minimum requirements, some gaps |
| 61-80 | Good | All required fields present, evidence adequate |
| 81-100 | Excellent | Exceeds requirements, multiple corroborations |

**Calculation:**
```
ValidationConfidence = f(
    schema_completeness,   // All required fields present
    evidence_sufficiency,  // Evidence meets minimum thresholds
    consistency_score,     // No internal contradictions
    hallucination_check,   // Provenance verification passed
    cross_entity_check     // Entity references are consistent
)
```

## 9.4 Editorial Confidence

Editorial confidence is assigned by a human reviewer after manual inspection.

| Range | Label | Meaning |
|-------|-------|---------|
| 0-20 | Rejected | Content is inaccurate or hallucinated |
| 21-40 | Needs Major Revision | Significant issues found |
| 41-60 | Needs Minor Revision | Some issues found |
| 61-80 | Approved with Notes | Acceptable with minor notes |
| 81-100 | Approved | Fully accurate and complete |

## 9.5 Composite Confidence

The composite confidence is a weighted combination:

```
CompositeConfidence = 
    ExtractionConfidence × 0.30 +
    ValidationConfidence × 0.40 +
    EditorialConfidence × 0.30
```

If editorial review has not been performed, the composite uses only extraction and validation:

```
CompositeConfidence (pre-review) = 
    ExtractionConfidence × 0.40 +
    ValidationConfidence × 0.60
```

## 9.6 Confidence Storage

```sql
CREATE TABLE ai_platform.confidence_scores (
    id UUID PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL,  -- entity, claim, theme, motif, story
    target_id UUID NOT NULL,
    extraction_confidence INTEGER CHECK (extraction_confidence BETWEEN 0 AND 100),
    validation_confidence INTEGER CHECK (validation_confidence BETWEEN 0 AND 100),
    editorial_confidence INTEGER CHECK (editorial_confidence BETWEEN 0 AND 100),
    composite_confidence DECIMAL(5,2),
    score_version VARCHAR(50) NOT NULL DEFAULT '1.0',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(target_type, target_id)
);
```

---

# 10. Mapping Rules

## 10.1 Canonical Story → PostgreSQL

### stories table (content schema)

| Canonical Story Field | PostgreSQL Column | Type | Notes |
|----------------------|-------------------|------|-------|
| `story.title` | `title` | TEXT | |
| `story.summary` | `summary` | TEXT | |
| `story.language` | `language_code` | VARCHAR(20) | |
| `extractionMetadata.qualityScore` | `confidence_score` | DECIMAL(5,2) | Converted from 0-1 to 0-100 |
| `sourceId` | `canonical_source_video_id` | UUID | |
| `metadata.tenantId` | `tenant_id` | UUID | |
| `metadata.correlationId` | (stored in metadata JSONB) | | |
| `canonicalStoryId` | (stored in metadata JSONB) | | |
| `story.culturalContext` | (stored in metadata JSONB) | | |

### entities table (knowledge schema)

| Canonical Story Field | PostgreSQL Column | Type | Notes |
|----------------------|-------------------|------|-------|
| `entities[].entityId` | `id` | UUID | |
| `entities[].normalizedName` | `canonical_name` | TEXT | |
| `entities[].name` | (stored in aliases) | | |
| `entities[].entityType` | `object_type` | VARCHAR(100) | |
| `entities[].confidence` | `confidence_score` | DECIMAL(5,2) | |
| `entities[].description` | `summary` | TEXT | |
| `entities[].attributes` | `metadata` | JSONB | |
| `entities[].culturalContext` | `metadata` | JSONB | |

### claims table (knowledge schema)

| Canonical Story Field | PostgreSQL Column | Type | Notes |
|----------------------|-------------------|------|-------|
| `claims[].claimId` | `id` | UUID | |
| `claims[].statement` | `statement` | TEXT | |
| `claims[].confidence` | `confidence_score` | DECIMAL(5,2) | |
| `claims[].status` | `status` | VARCHAR(50) | |
| `claims[].entityIds` | `entity_ids` | UUID[] | |
| `claims[].evidence` | (stored in evidence table) | | |

### evidence table (ai_platform schema)

| Canonical Story Field | PostgreSQL Column | Type | Notes |
|----------------------|-------------------|------|-------|
| `claims[].evidence[].segmentIndex` | `segment_index` | INTEGER | |
| `claims[].evidence[].text` | `text_snippet` | VARCHAR(2000) | |
| `claims[].evidence[].startTime` | `start_time` | DECIMAL(10,3) | |
| `claims[].evidence[].endTime` | `end_time` | DECIMAL(10,3) | |
| `claims[].evidence[].speaker` | `speaker` | VARCHAR(255) | |

## 10.2 Canonical Story → Neo4j

### Node Mapping

| Canonical Story Field | Neo4j Label | Properties |
|----------------------|-------------|------------|
| `story` | `:Story` | `{canonicalStoryId, title, summary, language, narrativeType, tone}` |
| `entities[]` | `:Entity` | `{entityId, name, normalizedName, entityType, subtype, confidence}` |
| `locations[]` | `:Location` | `{entityId, name, locationType, latitude, longitude}` |
| `themes[]` | `:Theme` | `{themeId, name, category, confidence}` |
| `motifs[]` | `:Motif` | `{motifId, name, motifType, confidence}` |
| `claims[]` | `:Claim` | `{claimId, statement, category, confidence, status}` |
| `beliefs[]` | `:Belief` | `{beliefId, statement, adherentCommunity, confidence}` |
| `rituals[]` | `:Ritual` | `{ritualId, name, purpose, confidence}` |
| `contradictions[]` | `:Contradiction` | `{contradictionId, type, description, severity}` |

### Relationship Mapping

| Source Label | Relationship | Target Label | Condition |
|-------------|--------------|-------------|-----------|
| `:Story` | `:HAS_ENTITY` | `:Entity` | Entity appears in story |
| `:Story` | `:HAS_THEME` | `:Theme` | Theme extracted from story |
| `:Story` | `:HAS_MOTIF` | `:Motif` | Motif extracted from story |
| `:Story` | `:HAS_CLAIM` | `:Claim` | Claim extracted from story |
| `:Story` | `:HAS_BELIEF` | `:Belief` | Belief expressed in story |
| `:Story` | `:HAS_RITUAL` | `:Ritual` | Ritual described in story |
| `:Story` | `:LOCATED_AT` | `:Location` | Story mentions location |
| `:Entity` | `:ASSOCIATED_WITH` | `:Entity` | `entities[].relationships[].relationType = 'associated_with'` |
| `:Entity` | `:MANIFESTATION_OF` | `:Entity` | `entities[].relationships[].relationType = 'manifestation_of'` |
| `:Entity` | `:APPEARS_IN` | `:Story` | Entity appears in story |
| `:Entity` | `:CONTRADICTS` | `:Entity` | `entities[].relationships[].relationType = 'contradicts'` |
| `:Entity` | `:GUARDIAN_OF` | `:Location` | `entities[].relationships[].relationType = 'guardian_of'` |
| `:Entity` | `:SAME_AS` | `:Entity` | `entities[].relationships[].relationType = 'same_as'` |
| `:Claim` | `:REFERENCES` | `:Entity` | `claims[].entityIds` |
| `:Claim` | `:SUPPORTED_BY` | `:Evidence` | `claims[].evidence` |
| `:Contradiction` | `:BETWEEN` | `:Entity` | `contradictions[].sides[].entityIds` |
| `:Belief` | `:HELD_BY` | `:Community` | `beliefs[].adherentCommunity` |

### Cypher Projection Query

```cypher
// Create story node
CREATE (s:Story {
    canonicalStoryId: $canonicalStoryId,
    title: $story.title,
    summary: $story.summary,
    language: $story.language,
    narrativeType: $story.narrativeType,
    tone: $story.tone
})

// Create entity nodes and relationships
UNWIND $entities AS entity
MERGE (e:Entity {entityId: entity.entityId})
SET e.name = entity.name,
    e.normalizedName = entity.normalizedName,
    e.entityType = entity.entityType,
    e.confidence = entity.confidence
CREATE (s)-[:HAS_ENTITY]->(e)

// Create entity-to-entity relationships
UNWIND entity.relationships AS rel
MATCH (source:Entity {entityId: entity.entityId})
MATCH (target:Entity {entityId: rel.targetEntityId})
CALL apoc.create.relationship(source, rel.relationType, {
    confidence: rel.confidence
}, target)
YIELD rel AS createdRel
RETURN count(createdRel)
```

## 10.3 Canonical Story → Weaviate

### Class Mapping

| Canonical Story Field | Weaviate Class | Vectorization | Properties |
|----------------------|---------------|---------------|------------|
| `story` | `CanonicalStory` | `story.title + story.summary` | `{canonicalStoryId, title, summary, language, narrativeType}` |
| `entities[]` | `CulturalEntity` | `entity.name + entity.description` | `{entityId, name, normalizedName, entityType, confidence}` |
| `claims[]` | `Claim` | `claim.statement` | `{claimId, statement, category, confidence}` |
| `themes[]` | `Theme` | `theme.name + theme.description` | `{themeId, name, category, confidence}` |
| `motifs[]` | `Motif` | `motif.name + motif.description` | `{motifId, name, motifType, confidence}` |

### Weaviate Schema

```json
{
  "class": "CanonicalStory",
  "description": "A canonical story extracted from a source transcript",
  "vectorizer": "text2vec-openai",
  "moduleConfig": {
    "text2vec-openai": {
      "model": "text-embedding-3-large",
      "dimensions": 1536
    }
  },
  "properties": [
    { "name": "canonicalStoryId", "dataType": ["uuid"], "description": "Unique story identifier" },
    { "name": "title", "dataType": ["text"], "description": "Story title in original language" },
    { "name": "summary", "dataType": ["text"], "description": "Story summary" },
    { "name": "language", "dataType": ["string"] },
    { "name": "narrativeType", "dataType": ["string"] },
    { "name": "tone", "dataType": ["string"] },
    { "name": "region", "dataType": ["string"], "description": "Geographic region" },
    { "name": "ethnicGroup", "dataType": ["string"] },
    { "name": "entityIds", "dataType": ["uuid[]"], "description": "Related entity IDs" },
    { "name": "themeIds", "dataType": ["uuid[]"], "description": "Related theme IDs" },
    { "name": "claimIds", "dataType": ["uuid[]"], "description": "Related claim IDs" },
    { "name": "sourceId", "dataType": ["uuid"] },
    { "name": "qualityScore", "dataType": ["number"] },
    { "name": "extractedAt", "dataType": ["date"] }
  ]
}
```

### Cross-Reference Mapping

Weaviate cross-references enable graph-like traversal:

```json
{
  "class": "CulturalEntity",
  "properties": [
    { "name": "entityId", "dataType": ["uuid"] },
    { "name": "name", "dataType": ["text"] },
    { "name": "normalizedName", "dataType": ["text"] },
    { "name": "entityType", "dataType": ["string"] },
    { "name": "confidence", "dataType": ["number"] },
    { "name": "inStories", "dataType": ["CanonicalStory"], "description": "Stories this entity appears in" },
    { "name": "relatedEntities", "dataType": ["CulturalEntity"], "description": "Related entities" }
  ]
}
```

---

# 11. Versioning Rules

## 11.1 Immutable Versioning

**Rule: Canonical Stories are immutable. No UPDATE. Only INSERT.**

Each time a Canonical Story is re-extracted (due to prompt changes, model upgrades, or corrections), a new version is created:

```sql
CREATE TABLE ai_platform.canonical_story_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_story_id UUID NOT NULL,       -- Logical story identifier (same across versions)
    source_id UUID NOT NULL,
    transcript_id UUID NOT NULL,
    version INTEGER NOT NULL,
    story_json JSONB NOT NULL,               -- The complete Canonical Story JSON
    change_reason VARCHAR(500) NOT NULL,     -- Why this version was created
    change_type VARCHAR(50) NOT NULL,        -- initial_extraction, re_extraction, manual_correction, prompt_update, model_upgrade
    previous_version_id UUID,                -- Link to previous version
    extraction_job_id UUID,
    prompt_version VARCHAR(100),
    model_used VARCHAR(100),
    quality_score DECIMAL(4,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    CONSTRAINT uq_story_version UNIQUE(canonical_story_id, version)
);

-- Index for "latest version" queries
CREATE INDEX idx_story_versions_latest 
    ON ai_platform.canonical_story_versions(canonical_story_id, version DESC);
```

## 11.2 Version Increment Rules

| Change Type | Version Increment | Example |
|-------------|------------------|---------|
| Initial extraction | 1.0.0 | First extraction from transcript |
| Re-extraction (same prompt, same model) | Patch (+0.0.1) | Bug fix in extraction pipeline |
| Re-extraction (new prompt version) | Minor (+0.1.0) | Prompt updated from v3 to v4 |
| Re-extraction (new model) | Minor (+0.1.0) | Gemini → Claude |
| Manual correction by editor | Minor (+0.1.0) | Editor fixes entity name |
| Schema change (new fields) | Major (+1.0.0) | New `rituals` field added |

## 11.3 Version History Preservation

```sql
-- Get the latest version of a story
SELECT * FROM ai_platform.canonical_story_versions
WHERE canonical_story_id = 'c5d6e7f8-a9b0-1234-efab-345678901234'
ORDER BY version DESC
LIMIT 1;

-- Get full version history
SELECT version, change_reason, change_type, prompt_version, model_used, quality_score, created_at
FROM ai_platform.canonical_story_versions
WHERE canonical_story_id = 'c5d6e7f8-a9b0-1234-efab-345678901234'
ORDER BY version ASC;

-- Diff two versions (application level)
-- Compare story_json between version N and N-1
```

## 11.4 Downstream Version Pinning

Downstream artifacts (articles, graph projections, embeddings) pin the Canonical Story version they were generated from:

```sql
ALTER TABLE ai_platform.article_drafts 
    ADD COLUMN canonical_story_version INTEGER NOT NULL;

ALTER TABLE ai_platform.graph_projections 
    ADD COLUMN canonical_story_version INTEGER NOT NULL;

ALTER TABLE ai_platform.embeddings 
    ADD COLUMN canonical_story_version INTEGER NOT NULL;
```

This ensures:
- An article generated from v1 of a story is not invalidated when v2 is created.
- Graph projections can be traced to the exact story version.
- Embeddings can be regenerated on demand for specific versions.

---

# 12. Validation Rules

## 12.1 Required Fields

The following fields are **REQUIRED** for a Canonical Story to pass validation:

| Field Path | Reason | Failure Action |
|-----------|--------|---------------|
| `canonicalStoryId` | Identity | Reject |
| `sourceId` | Provenance | Reject |
| `transcriptId` | Provenance | Reject |
| `version` | Versioning | Reject |
| `story.title` | Minimum content | Reject |
| `story.summary` | Minimum content | Reject |
| `story.language` | Processing | Reject |
| `story.narrativeType` | Classification | Reject |
| `entities` (at least 1) | Knowledge extraction | Warning (if 0) |
| `claims` (at least 1) | Knowledge extraction | Warning (if 0) |
| `provenance.sourceId` | Provenance | Reject |
| `provenance.transcriptId` | Provenance | Reject |
| `provenance.extractionJobId` | Audit | Reject |
| `provenance.promptVersion` | Audit | Reject |
| `provenance.modelUsed` | Audit | Reject |
| `metadata.tenantId` | Multi-tenancy | Reject |
| `metadata.correlationId` | Tracing | Reject |
| `metadata.schemaVersion` | Schema evolution | Reject |

## 12.2 Optional Fields

The following fields are **OPTIONAL** but recommended:

| Field Path | Recommended If | Default |
|-----------|---------------|---------|
| `story.titleEn` | Language is not English | null |
| `story.culturalContext` | Cultural context is identifiable | null |
| `story.witnesses` | Witnesses are named | [] |
| `story.keyEvents` | Story has temporal structure | [] |
| `locations` | Locations are mentioned | [] |
| `events` | Broader events are relevant | [] |
| `beliefs` | Beliefs are expressed | [] |
| `rituals` | Rituals are described | [] |
| `traditions` | Traditions are referenced | [] |
| `themes` | Themes are identifiable | [] |
| `motifs` | Motifs are identifiable | [] |
| `contradictions` | Contradictions exist | [] |
| `researchGaps` | Gaps are identified | [] |
| `uncertainties` | Uncertainties exist | [] |

## 12.3 Quality Gates

| Gate | Condition | Pass | Fail |
|------|-----------|------|------|
| **Schema Validation** | JSON matches schema | Continue | REJECT (DLQ) |
| **Content Validation** | Required fields present | Continue | REJECT (DLQ) |
| **Evidence Validation** | Every claim has ≥1 evidence | Continue | WARNING + flag |
| **Entity Validation** | Every entity has ≥1 evidence | Continue | WARNING + flag |
| **Confidence Floor** | Extraction confidence ≥ 20 | Continue | FLAG for review |
| **Hallucination Check** | No provenance violations | Continue | REJECT (DLQ) |
| **Contradiction Check** | Contradictions explicitly marked | Continue | WARNING |
| **Quality Score** | Overall ≥ 0.6 | AUTO-PASS | MANUAL REVIEW |
| **Quality Score** | Overall ≥ 0.8 | AUTO-PASS | — |

## 12.4 Failure Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Empty `story.title` | CRITICAL | Reject extraction, DLQ |
| Zero entities AND zero claims | CRITICAL | Reject extraction, DLQ |
| All claims have zero evidence | CRITICAL | Reject extraction, DLQ |
| `sourceId` does not exist in database | CRITICAL | Reject extraction, DLQ |
| JSON schema violation | CRITICAL | Reject extraction, DLQ |
| Hallucination detected (provenance mismatch) | CRITICAL | Reject extraction, DLQ |
| Quality score < 0.3 | HIGH | Flag for manual review |
| Quality score 0.3-0.6 | MEDIUM | Flag for manual review |
| Missing optional fields | LOW | Warning, auto-pass |
| Single evidence per claim | LOW | Warning, auto-pass |
| Contradictions detected | INFO | Logged, auto-pass |

## 12.5 Validation Implementation

```python
def validate_canonical_story(story: dict) -> ValidationResult:
    errors = []
    warnings = []
    
    # 1. Schema validation
    try:
        jsonschema.validate(story, CANONICAL_STORY_SCHEMA)
    except ValidationError as e:
        return ValidationResult(passed=False, errors=[str(e)], warnings=[])
    
    # 2. Required field validation
    required_fields = [
        'canonicalStoryId', 'sourceId', 'transcriptId', 'version',
        'story.title', 'story.summary', 'story.language', 'story.narrativeType',
        'provenance.sourceId', 'provenance.transcriptId',
        'provenance.extractionJobId', 'provenance.promptVersion', 'provenance.modelUsed',
        'metadata.tenantId', 'metadata.correlationId', 'metadata.schemaVersion'
    ]
    for field in required_fields:
        if not get_nested_value(story, field):
            errors.append(f"Missing required field: {field}")
    
    # 3. Evidence validation
    for claim in story.get('claims', []):
        if not claim.get('evidence') or len(claim['evidence']) == 0:
            errors.append(f"Claim {claim['claimId']} has no evidence")
        elif len(claim['evidence']) == 1:
            warnings.append(f"Claim {claim['claimId']} has only 1 evidence segment")
    
    # 4. Entity validation
    for entity in story.get('entities', []):
        if not entity.get('evidence') or len(entity['evidence']) == 0:
            warnings.append(f"Entity {entity['entityId']} has no evidence")
    
    # 5. Confidence floor
    for claim in story.get('claims', []):
        if claim.get('confidence', 0) < 20:
            warnings.append(f"Claim {claim['claimId']} has very low confidence ({claim['confidence']})")
    
    # 6. Quality score
    quality_score = story.get('extractionMetadata', {}).get('qualityScore', 0)
    if quality_score < 0.3:
        errors.append(f"Quality score {quality_score} is below minimum threshold (0.3)")
    elif quality_score < 0.6:
        warnings.append(f"Quality score {quality_score} is below auto-approval threshold (0.6)")
    
    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        quality_score=quality_score,
        requires_review=quality_score < 0.6 or len(warnings) > 3
    )
```

---

# 13. Future Compatibility

## 13.1 Story DNA

Story DNA is the concept of representing a story as a **genetic sequence** of narrative elements — motifs, themes, entities, and their relationships — enabling computational analysis of cultural evolution.

**Canonical Story compatibility:**
- The `motifs` array provides the "genes" (narrative units).
- The `themes` array provides the "gene expression" (which themes are active).
- Entity relationships provide the "protein interactions" (how elements connect).
- Contradictions provide "mutations" (variations between versions).

**Future query:**
```cypher
// Find stories with similar DNA (same motif sequence)
MATCH (s1:Story)-[:HAS_MOTIF]->(m:Motif)
WITH s1, collect(m.name) AS motif_sequence
MATCH (s2:Story)-[:HAS_MOTIF]->(m2:Motif)
WHERE s1 <> s2
WITH s1, s2, motif_sequence, collect(m2.name) AS other_sequence
WHERE similarity(motif_sequence, other_sequence) > 0.8
RETURN s1.title, s2.title, similarity(motif_sequence, other_sequence) AS dna_similarity
```

## 13.2 Research Intelligence

Research intelligence uses Canonical Story data to identify patterns across the entire corpus:

| Research Question | Canonical Story Data Used |
|------------------|--------------------------|
| Which entities are most frequently mentioned? | `entities[].normalizedName` + frequency |
| Which themes co-occur most often? | `themes[].name` + story-level grouping |
| Where are contradictions most concentrated? | `contradictions[].type` + geographic distribution |
| Which claims have the lowest confidence? | `claims[].confidence` + `claims[].evidence` count |
| What research gaps exist? | `researchGaps[].type` + severity |

## 13.3 Adaptation Intelligence

Adaptation intelligence tracks how stories change across retellings, regions, and time periods.

**Canonical Story compatibility:**
- Multiple versions of the same story (same `canonicalStoryId`, different `version`) track evolution over time.
- Different sources about the same entity (same `entityId`, different `sourceId`) track regional variation.
- Contradictions explicitly encode divergent traditions.

**Future query:**
```cypher
// Track how a story changed across versions
MATCH (s:Story {canonicalStoryId: $storyId})
MATCH (s)-[:HAS_VERSION]->(v:StoryVersion)
RETURN v.version, v.title, v.summary, v.extractedAt
ORDER BY v.version ASC
```

## 13.4 Cultural Evolution

Cultural evolution models use Canonical Story data to study how cultural knowledge spreads, mutates, and is preserved.

**Data requirements met by Canonical Story:**
- **Temporal data:** `extractedAt`, `story.culturalContext.timePeriod`
- **Geographic data:** `story.culturalContext.region`, `locations[].latitude/longitude`
- **Lineage data:** Version history tracks changes over time
- **Variation data:** Contradictions encode divergent traditions
- **Transmission data:** Witness attribution tracks who tells which version

## 13.5 Schema Evolution Path

| Phase | Schema Version | New Capabilities |
|-------|---------------|-----------------|
| **Phase 1** | 1.0.0 | Core story, entities, claims, evidence, provenance |
| **Phase 2** | 1.1.0 | Themes, motifs, locations, beliefs, rituals |
| **Phase 3** | 1.2.0 | Contradictions, research gaps, uncertainties |
| **Phase 4** | 2.0.0 | Story DNA markers, narrative genome sequences |
| **Phase 5** | 2.1.0 | Adaptation tracking, cultural evolution metrics |
| **Phase 6** | 3.0.0 | Multi-modal (image, audio references), interactive narratives |

---

# References

- **PRD.md §6:** Canonical Story Extraction rules (never hallucinate, preserve uncertainty, preserve provenance)
- **PRD.md §4:** Processing Pipeline (Source → Metadata → Transcript → Canonical Story → Knowledge → ...)
- **docs/ai-platform/domain-event-catalog.md:** Events emitted during Canonical Story lifecycle
- **docs/ai-platform/ai-pipeline-state-machine-specification.md:** Pipeline state machine for story processing
- **docs/ai-platform/prompt-registry-governance-specification.md:** Prompt governance for extraction prompts
- **docs/architecture/knowledge-graph-modeling.md:** Neo4j graph model
- **docs/architecture/domain-event-catalog.md:** Backend event catalog
- **services/content-service:** Story.java, StoryVersion.java, StoryEvidence.java domain models
- **services/knowledge-service:** KnowledgeObject.java, Claim.java, Theme.java, Motif.java domain models
- **ai-platform/shared/src/ai_shared/prompts.py:** Story canonicalization prompt templates
- **ai-platform/shared/src/ai_shared/canonical_pipeline.py:** Canonical story extraction pipeline