# Product Requirements Document (PRD)

# AI Platform

## The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: AI Platform Team

---

# 1. Executive Summary

The AI Platform is responsible for transforming raw source materials into structured cultural knowledge, research assets, and publishable content.

The AI Platform is NOT a user-facing system.

The AI Platform does NOT expose public APIs.

The AI Platform operates entirely through asynchronous job processing driven by events and queues.

Primary responsibilities:

* Source processing
* Transcript processing
* Story extraction
* Knowledge extraction
* Knowledge normalization
* Knowledge validation
* Article generation
* Embedding generation
* Knowledge graph projection support

The AI Platform must be stateless, horizontally scalable, retryable, and idempotent.

---

# 2. Architectural Principles

## 2.1 Queue Driven Architecture

All AI operations are initiated by queue messages.

Forbidden:

Frontend → AI

Backend → AI REST Call

Synchronous AI execution

Required:

Backend → Queue → AI Worker

---

## 2.2 Event Driven Processing

Every AI stage produces events.

Example:

SourceSubmitted

SourceMetadataImported

TranscriptImported

TranscriptNormalized

CanonicalStoryExtracted

KnowledgeExtracted

KnowledgeNormalized

KnowledgeValidated

ArticleGenerated

EmbeddingGenerated

GraphProjected

---

## 2.3 Stateless Workers

Workers must not maintain internal state.

State must reside in:

* PostgreSQL
* Queue
* Object Storage

Workers must be replaceable at any time.

---

## 2.4 Idempotent Processing

Every job must support re-execution.

Repeated execution must produce identical results.

---

## 2.5 Model Agnostic

The platform must support:

* Gemini
* Claude
* OpenAI

Future:

* Local Models
* Fine Tuned Models

No business logic may depend on a specific provider.

---

# 3. Repository Structure

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

---

# 4. Processing Pipeline

Source

↓

Metadata

↓

Transcript

↓

Canonical Story Extraction

↓

Knowledge Extraction

↓

Knowledge Normalization

↓

Knowledge Validation

↓

Knowledge Persistence

↓

Article Generation

↓

Embedding Generation

↓

Projection Events

---

# 5. Services

---

# 5.1 Orchestration Service

Owner:

AI Platform

Purpose:

Coordinate processing pipelines.

Responsibilities:

* Job scheduling
* Retry management
* Pipeline state tracking
* Dead letter handling
* Progress tracking

Consumes:

SourceSubmitted

TranscriptImported

Produces:

ExtractionRequested

ArticleRequested

EmbeddingRequested

Requirements:

* Idempotent
* Retryable
* Distributed safe

---

# 5.2 Ingestion Service

Purpose:

Transform external source metadata into normalized internal records.

Responsibilities:

* Metadata extraction
* Transcript retrieval
* Transcript cleaning
* Metadata normalization

Input:

YouTube metadata

Podcast metadata

Manual uploads

Output:

Normalized transcript

Normalized metadata

---

# 5.3 Extraction Service

Purpose:

Convert transcript into canonical cultural knowledge.

Responsibilities:

* Story extraction
* Theme extraction
* Motif extraction
* Entity extraction
* Ritual extraction
* Belief extraction
* Claim extraction
* Contradiction extraction

Input:

Transcript

Metadata

Output:

Canonical Story JSON

Knowledge JSON

---

# 5.4 Normalization Service

Purpose:

Resolve ambiguity.

Responsibilities:

* Alias detection
* Duplicate detection
* Entity normalization
* Cultural normalization
* Folklore normalization

Examples:

Ponti

Pontianak

Kuntilanak

↓

Kuntilanak

Output:

Normalized Knowledge JSON

---

# 5.5 Validation Service

Purpose:

Assess knowledge quality.

Responsibilities:

* Schema validation
* Confidence scoring
* Missing data detection
* Contradiction review
* Research gap identification

Output:

Validation Report

Quality Score

Warnings

Issues

---

# 5.6 Article Service

Purpose:

Generate publication-ready articles.

Supported Articles:

Narrative Article

Knowledge Article

News Article

Creative Article

Input:

Validated Canonical Story

Output:

Markdown

Structured Article JSON

---

# 5.7 Embedding Service

Purpose:

Generate vector representations.

Responsibilities:

* Story embeddings
* Article embeddings
* Entity embeddings
* Knowledge embeddings

Output:

Embedding vectors

Embedding metadata

Projection events

---

# 6. Canonical Story Extraction

Purpose:

Transform transcripts into structured stories.

Input:

Transcript

Metadata

Output:

Story

Entities

Themes

Motifs

Claims

Beliefs

Traditions

Rituals

Events

Locations

Contradictions

Research Gaps

Rules:

Never hallucinate.

Never invent entities.

Preserve uncertainty.

Preserve provenance.

---

# 7. Job State Machine

SUBMITTED

↓

QUEUED

↓

PROCESSING

↓

COMPLETED

OR

FAILED

OR

CANCELLED

---

Pipeline States

METADATA_READY

↓

TRANSCRIPT_READY

↓

CANONICALIZED

↓

NORMALIZED

↓

VALIDATED

↓

ARTICLES_GENERATED

↓

EMBEDDINGS_GENERATED

↓

FINISHED

---

# 8. Queue Architecture

Recommended:

Redpanda

Topics:

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

publication.requested

publication.completed

---

# 9. AI Provider Layer

Required Providers:

Gemini

Claude

OpenAI

Architecture:

Provider Interface

↓

Gemini Adapter

Claude Adapter

OpenAI Adapter

Business logic must never call providers directly.

---

# 10. Retry Strategy

Retryable Failures:

Rate limit

Temporary outage

Timeout

Network failure

Strategy:

1 minute

5 minutes

15 minutes

1 hour

Dead Letter Queue

Maximum:

5 retries

---

# 11. Observability

Required:

Structured logs

Job tracing

Prompt tracing

Token tracking

Provider tracking

Cost tracking

Latency tracking

---

Metrics:

Jobs Processed

Jobs Failed

Average Latency

Average Cost

Token Usage

Provider Usage

Success Rate

---

# 12. Cost Governance

Every AI request must store:

Provider

Model

Prompt Version

Input Tokens

Output Tokens

Execution Cost

Execution Time

Purpose

Associated Job

The system must support future cost analytics.

---

# 13. Prompt Governance

Prompts are versioned assets.

Required:

Prompt Registry

Prompt Versioning

Prompt Audit Trail

Prompt Rollback

Prompt Testing

Never hardcode prompts inside services.

Store prompts separately.

---

# 14. Success Criteria

Phase 1

Transcript Processing

Canonical Story Extraction

Knowledge Extraction

Narrative Article

Knowledge Article

---

Phase 2

Knowledge Normalization

Knowledge Validation

Embedding Generation

Weaviate Sync

---

Phase 3

Story DNA

Narrative Genome

Adaptation Intelligence

Cultural Trend Intelligence

Research Gap Detection
