# AI Platform PRD

## The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: AI Platform Team

Last Updated: June 2026

---

# 1. Executive Summary

The AI Platform is responsible for transforming raw cultural source material into structured knowledge assets.

The platform processes:

* YouTube transcripts
* Podcast transcripts
* Interviews
* Folklore narratives
* Historical narratives
* Community stories

The AI Platform produces:

* Canonical Stories
* Knowledge Objects
* Claims
* Articles
* Embeddings
* Research Intelligence Assets

The AI Platform is not user-facing.

The AI Platform is an internal processing platform.

---

# 2. Product Vision

Transform unstructured cultural narratives into structured, verifiable, searchable, and reusable cultural knowledge.

The AI Platform should become:

> The cultural intelligence engine behind The Living Atlas of Indonesian Mystery Culture.

---

# 3. Architectural Principles

## 3.1 Queue Driven Architecture

The AI Platform does not expose APIs.

Forbidden:

Frontend → AI Platform

Backend → AI Platform REST

Required:

Backend

↓

Redpanda

↓

AI Workers

↓

PostgreSQL

All processing is asynchronous.

---

## 3.2 Event Driven Processing

Every AI operation must be triggered by events.

Examples:

* TranscriptImported
* CanonicalStoryExtractionRequested
* KnowledgeExtractionRequested
* ArticleGenerationRequested
* EmbeddingGenerationRequested

---

## 3.3 Stateless Workers

Workers must be stateless.

Worker state must never be stored in memory.

State must reside in:

* PostgreSQL
* Queue
* Object Storage (future)

Workers must be replaceable at any time.

---

## 3.4 Idempotent Processing

Every job must support re-execution.

Repeated execution must not corrupt data.

Duplicate messages must be safely ignored.

---

## 3.5 Model Agnostic Architecture

The platform must support:

* Gemini
* Claude
* OpenAI

Future:

* Local Models
* Fine Tuned Models
* Domain Models

Business logic must never depend on a specific provider.

---

## 3.6 Canonical Story First

All AI outputs must eventually conform to Canonical Story Specification.

Canonical Story becomes the contract between:

* Extraction
* Knowledge
* Articles
* Embeddings
* Graph

---

## 3.7 Human Review Required

AI generated outputs must not be automatically published.

Review is required for:

* Claims
* Knowledge Objects
* Articles

---

# 4. High Level Architecture

```text
Source Metadata
       │
       ▼
Transcript
       │
       ▼
Canonical Story Extraction
       │
       ▼
Knowledge Extraction
       │
       ▼
Knowledge Normalization
       │
       ▼
Knowledge Validation
       │
       ▼
Article Generation
       │
       ▼
Embedding Generation
       │
       ▼
Projection Events
```

---

# 5. Repository Structure

```text
ai-platform/

├── orchestration-service
├── ingestion-service
├── extraction-service
├── normalization-service
├── validation-service
├── article-service
├── embedding-service
├── common
├── workers
└── sdk
```

---

# 6. Service Responsibilities

---

# 6.1 Orchestration Service

Purpose:

Coordinate AI pipelines.

Responsibilities:

* Job Scheduling
* Pipeline Management
* Retry Management
* Dead Letter Handling
* Progress Tracking

Consumes:

* TranscriptImported

Produces:

* ExtractionRequested
* ArticleRequested
* EmbeddingRequested

---

# 6.2 Ingestion Service

Purpose:

Normalize source material.

Responsibilities:

* Metadata Normalization
* Transcript Normalization
* Language Detection
* Metadata Cleaning

Inputs:

* YouTube Metadata
* Podcast Metadata
* Manual Sources

Outputs:

* Normalized Metadata
* Normalized Transcript

---

# 6.3 Extraction Service

Purpose:

Transform transcript into structured knowledge.

Responsibilities:

* Story Extraction
* Entity Extraction
* Claim Extraction
* Theme Extraction
* Motif Extraction
* Ritual Extraction
* Belief Extraction
* Tradition Extraction
* Contradiction Detection

Input:

Transcript

Output:

Canonical Story

---

# 6.4 Normalization Service

Purpose:

Resolve ambiguity.

Responsibilities:

* Alias Resolution
* Entity Consolidation
* Duplicate Detection
* Folklore Normalization
* Cultural Normalization

Example:

Ponti

Pontianak

Kuntilanak

↓

Kuntilanak

---

# 6.5 Validation Service

Purpose:

Assess knowledge quality.

Responsibilities:

* Confidence Scoring
* Schema Validation
* Contradiction Review
* Missing Data Detection
* Research Gap Detection

Outputs:

* Validation Report
* Confidence Scores
* Warnings

---

# 6.6 Article Service

Purpose:

Generate publication-ready content.

Supported Outputs:

* Narrative Article
* Knowledge Article
* News Article
* Creative Article

Input:

Canonical Story

Validated Knowledge

Output:

Markdown

Structured Article JSON

---

# 6.7 Embedding Service

Purpose:

Generate vectors.

Supported Embeddings:

* Story Embedding
* Article Embedding
* Entity Embedding
* Knowledge Embedding
* Claim Embedding

Outputs:

Vectors

Metadata

Projection Events

---

# 7. AI Processing Pipeline

## Stage 1

Transcript

↓

Canonical Story

Mandatory

---

## Stage 2

Canonical Story

↓

Knowledge Objects

Mandatory

---

## Stage 3

Knowledge Objects

↓

Validation

Mandatory

---

## Stage 4

Validated Knowledge

↓

Articles

Mandatory

---

## Stage 5

Validated Knowledge

↓

Embeddings

Mandatory

---

## Stage 6

Projection Events

↓

Neo4j

↓

Weaviate

Mandatory

---

# 8. Canonical Story Extraction

Purpose:

Create a structured story representation.

Input:

* Transcript
* Metadata

Output:

* Story
* Entities
* Locations
* Events
* Claims
* Themes
* Motifs
* Rituals
* Beliefs
* Traditions
* Contradictions
* Research Gaps

Rules:

Never hallucinate.

Never invent entities.

Preserve uncertainty.

Preserve evidence.

Preserve provenance.

---

# 9. Knowledge Extraction

Supported Objects:

* Spirit
* Ghost
* Creature
* Folklore Character
* Belief
* Ritual
* Tradition
* Artifact
* Location
* Historical Event
* Cultural Practice

Supported Relationships:

* Appears In
* Related To
* Derived From
* Contradicts
* Influenced By
* Located In

---

# 10. Job State Machine

SUBMITTED

↓

QUEUED

↓

PROCESSING

↓

WAITING_PROVIDER

↓

RETRYING

↓

MANUAL_REVIEW

↓

COMPLETED

OR

FAILED

OR

CANCELLED

---

# 11. Pipeline State Machine

TRANSCRIPT_READY

↓

CANONICAL_STORY_READY

↓

KNOWLEDGE_READY

↓

VALIDATED

↓

ARTICLES_GENERATED

↓

EMBEDDINGS_GENERATED

↓

PROJECTION_READY

↓

FINISHED

---

# 12. Queue Architecture

Event Backbone:

Redpanda

Required Topics:

source.submitted

source.metadata.imported

transcript.imported

transcript.normalized

story.extraction.requested

story.extracted

knowledge.extraction.requested

knowledge.extracted

knowledge.normalization.requested

knowledge.normalized

knowledge.validation.requested

knowledge.validated

article.generation.requested

article.generated

embedding.generation.requested

embedding.generated

graph.projection.requested

graph.projected

review.requested

review.approved

review.rejected

---

# 13. AI Provider Layer

Architecture:

Provider Interface

↓

Gemini Adapter

Claude Adapter

OpenAI Adapter

Business logic must never call providers directly.

---

# 14. Provider Strategy

Primary:

Gemini

Fallback:

Claude

Secondary Fallback:

OpenAI

Failover Conditions:

* Rate Limit
* Timeout
* Service Unavailable
* Provider Error

---

# 15. Prompt Architecture

Prompts are managed assets.

Required Components:

* Prompt Registry
* Prompt Versioning
* Prompt Approval Workflow
* Prompt Rollback
* Prompt Audit Trail

Prompts must never be hardcoded.

---

# 16. Prompt Categories

CANONICAL_STORY_V1

KNOWLEDGE_EXTRACTION_V1

KNOWLEDGE_NORMALIZATION_V1

KNOWLEDGE_VALIDATION_V1

NARRATIVE_ARTICLE_V1

KNOWLEDGE_ARTICLE_V1

NEWS_ARTICLE_V1

CREATIVE_ARTICLE_V1

EMBEDDING_ENRICHMENT_V1

---

# 17. Cost Governance

Every execution must store:

* Provider
* Model
* Prompt Version
* Input Tokens
* Output Tokens
* Cost
* Execution Time
* Tenant
* Workspace
* Job

Supported Analytics:

* Cost Per Story
* Cost Per Article
* Cost Per Tenant
* Cost Per Workspace
* Cost Per Provider

---

# 18. Retry Strategy

Retryable:

* Timeout
* Rate Limit
* Temporary Provider Failure
* Network Failure

Retry Schedule:

1 Minute

↓

5 Minutes

↓

15 Minutes

↓

1 Hour

↓

Dead Letter Queue

Maximum:

5 Retries

---

# 19. Human Review Workflow

AI Output

↓

Review Required

↓

Approved

OR

Rejected

If Rejected:

↓

Reprocess

↓

Review Again

Publication is blocked until approval.

---

# 20. Observability

Required:

* Structured Logging
* Prompt Tracing
* Job Tracing
* Token Tracking
* Cost Tracking
* Provider Tracking

Metrics:

* Jobs Processed
* Jobs Failed
* Retry Rate
* Average Cost
* Average Latency
* Token Usage
* Provider Usage

---

# 21. Security Requirements

Required:

* Tenant Isolation
* Workspace Isolation
* Prompt Access Control
* Audit Logging
* Secret Management

Provider Keys:

Stored in secure secret manager.

Never hardcoded.

---

# 22. Non Functional Requirements

Availability:

99.5%

---

Latency:

Not user-facing.

Optimize for reliability over speed.

---

Scalability Target:

100,000 Stories

10,000,000 Transcript Segments

1,000,000 Knowledge Objects

100,000,000 Embeddings

---

# 23. Success Criteria

## Phase 1

* Transcript Processing
* Canonical Story Extraction
* Knowledge Extraction
* Narrative Article Generation
* Knowledge Article Generation

---

## Phase 2

* Knowledge Normalization
* Knowledge Validation
* Embedding Generation
* Neo4j Projection
* Weaviate Projection

---

## Phase 3

* Story DNA
* Cultural Intelligence
* Adaptation Intelligence
* Research Intelligence
* Cultural Evolution Analytics

---

# 24. Out of Scope

Not included in MVP:

* Local LLM Hosting
* GPU Inference
* Fine Tuning
* Agent Frameworks
* Autonomous Agents
* Multi Agent Systems
* Real Time AI Chat

These may be introduced in future phases.
