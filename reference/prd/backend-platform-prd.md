# Backend Platform PRD

## The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Platform Engineering

Last Updated: June 2026

---

# 1. Executive Summary

The Living Atlas of Indonesian Mystery Culture is a cultural intelligence platform designed to transform mystery-related content into structured knowledge.

The platform ingests:

* YouTube investigations
* Horror podcasts
* Folklore records
* Oral traditions
* Cultural interviews
* Historical narratives
* Community stories

The system transforms source material into:

* Stories
* Knowledge Objects
* Claims
* Research Assets
* Articles
* Knowledge Graphs
* Embeddings

The platform serves:

* General Readers
* Horror Communities
* Researchers
* Anthropologists
* Journalists
* Writers
* Production Houses
* Documentary Teams
* Game Studios
* Educational Institutions

---

# 2. Product Vision

Preserve, structure, and make discoverable the mystery culture of Indonesia.

The platform should become:

> The largest living knowledge graph of Indonesian mystery culture.

---

# 3. Architecture Principles

## 3.1 Modular Monolith First

The platform will initially use Modular Monolith architecture.

Reasoning:

* Small team
* Faster delivery
* Lower operational complexity
* Easier debugging
* Easier deployment

Microservices may be introduced later when justified.

---

## 3.2 Event Driven Architecture

All asynchronous operations must use events.

Examples:

* Story Created
* Transcript Imported
* Knowledge Extracted
* Article Published

Event transport:

* Redpanda

---

## 3.3 Queue Driven AI Platform

AI Platform is not user facing.

Forbidden:

* Frontend → AI
* Backend → AI REST

Required:

Backend

↓

Redpanda

↓

AI Workers

↓

PostgreSQL

---

## 3.4 PostgreSQL as Source of Truth

Ownership:

PostgreSQL

* Source of Truth

Neo4j

* Knowledge Graph Projection

Weaviate

* Vector Projection

Applications must never write directly to Neo4j or Weaviate.

---

## 3.5 Provenance First

Every knowledge object must be traceable.

Knowledge Object

↓

Claim

↓

Evidence

↓

Transcript Segment

↓

Transcript

↓

Source

---

## 3.6 Human Review Required

AI-generated outputs are never automatically published.

Required review:

* Knowledge Objects
* Claims
* Articles

---

## 3.7 Immutable Versioning

Updates create new versions.

Never overwrite:

* Stories
* Knowledge Objects
* Claims
* Articles

---

# 4. High Level Architecture

```text
Frontend Applications
        │
        ▼
Gateway Service
        │
        ▼
Domain Services
        │
        ▼
PostgreSQL
        │
        ├────────► Redpanda
        │              │
        │              ▼
        │       AI Platform
        │              │
        ▼              ▼
Projection Workers
        │
 ┌──────┴──────┐
 ▼             ▼

Neo4j      Weaviate
```

---

# 5. User Types

## Reader

Capabilities:

* Read stories
* Read articles
* Explore culture pages
* Explore graph

---

## Researcher

Capabilities:

* Create collections
* Annotate stories
* Save graph views
* Export datasets

---

## Editor

Capabilities:

* Review AI output
* Approve publication
* Merge knowledge

---

## Reviewer

Capabilities:

* Validate claims
* Validate evidence
* Approve knowledge

---

## Creator

Capabilities:

* Create stories
* Manage sources
* Submit content

---

## Tenant Admin

Capabilities:

* Workspace management
* User management
* Policy management

---

## System Admin

Capabilities:

* Global administration
* Platform governance

---

# 6. Functional Domains

---

# Identity Domain

Owner:

identity-service

Responsibilities:

* Authentication
* Authorization
* Users
* Roles
* Tenants
* Workspaces
* Policies
* API Keys

---

# Source Domain

Owner:

content-service

Responsibilities:

* Channels
* Sources
* Videos
* Episodes
* Metadata
* Transcripts
* Provenance

---

# Story Domain

Owner:

content-service

Responsibilities:

* Story Creation
* Story Versioning
* Story Relationships
* Story Publishing

Story Types:

* Investigation
* Folklore
* Urban Legend
* Personal Experience
* Historical
* Cultural Narrative

---

# Knowledge Domain

Owner:

knowledge-service

Responsibilities:

* Knowledge Objects
* Themes
* Motifs
* Rituals
* Beliefs
* Traditions
* Creatures
* Spirits
* Locations
* Claims
* Contradictions

---

# Article Domain

Owner:

content-service

Responsibilities:

* Narrative Article
* Knowledge Article
* News Article
* Creative Article

---

## Narrative Article

Source-based storytelling.

Must follow transcript evidence.

---

## Knowledge Article

Structured educational content.

Derived from verified knowledge objects.

---

## News Article

Journalistic format.

Generated from source knowledge.

---

## Creative Article

Entertainment-only content.

Not canonical.

Not used by graph.

Not used by knowledge extraction.

---

# Research Domain

Owner:

research-service

Responsibilities:

* Collections
* Annotations
* Notes
* Exports
* Comparisons

---

# Workflow Domain

Owner:

workflow-service

Responsibilities:

* Review
* Approval
* Publishing
* Moderation

---

# 7. Multi Tenant Architecture

Model:

Shared Database

Shared Schema

Tenant Isolation:

* tenant_id
* workspace_id

All queries must be tenant-scoped.

---

# 8. Authorization Model

RBAC + ABAC

RBAC:

* Reader
* Researcher
* Editor
* Reviewer
* Creator
* Admin

ABAC Dimensions:

* Tenant
* Workspace
* Ownership
* Status
* Classification

---

# 9. State Machines

## Story

DRAFT

↓

REVIEW

↓

APPROVED

↓

PUBLISHED

↓

ARCHIVED

---

## Knowledge

EXTRACTED

↓

REVIEW_REQUIRED

↓

VERIFIED

↓

PUBLISHED

↓

ARCHIVED

---

## Article

DRAFT

↓

REVIEW

↓

APPROVED

↓

PUBLISHED

↓

ARCHIVED

---

# 10. Event Architecture

Required Events:

* SourceRegistered
* SourceMetadataImported
* TranscriptImported
* TranscriptNormalized
* StoryCreated
* StoryVersionCreated
* CanonicalStoryExtracted
* KnowledgeExtracted
* KnowledgeValidated
* ArticleGenerated
* ArticlePublished
* EmbeddingGenerated
* GraphProjectionRequested
* GraphProjected

Event Backbone:

Redpanda

---

# 11. Database Strategy

## PostgreSQL

Purpose:

Transactional data

Stores:

* Sources
* Stories
* Knowledge
* Claims
* Articles
* Workflows
* Audit Logs

---

## Neo4j

Purpose:

Knowledge Graph

Stores:

* Nodes
* Relationships
* Graph Projections

Read only.

---

## Weaviate

Purpose:

Semantic Search

Stores:

* Embeddings
* Chunks
* Search Metadata

Read only.

---

# 12. Audit Requirements

Every business table must contain:

```sql
created_at
created_by

updated_at
updated_by

deleted_at
deleted_by

version

tenant_id
workspace_id
```

Where applicable.

---

# 13. Observability

Required:

* Structured Logging
* Metrics
* Tracing
* Audit Logging
* Cost Tracking

Stack:

* OpenTelemetry
* Prometheus
* Grafana
* Loki

---

# 14. Security Requirements

Authentication:

* JWT
* OAuth2

Authorization:

* RBAC
* ABAC

Encryption:

* At Rest
* In Transit

Required:

* Audit Trail
* Security Events
* API Rate Limiting

---

# 15. Internal Service Structure

All Spring Boot services use Domain Driven Design modules.

Example:

content-service

story/
article/
source/
review/

knowledge-service

knowledge/
claim/
entity/
folklore/

Rules:

* Domain does not depend on Infrastructure
* Module communication through Application Layer
* No shared entities
* No direct cross-module persistence access

---

# 16. Non Functional Requirements

Availability:

99.5%

---

API Performance:

p95 < 300ms

p99 < 1 second

Excluding AI workloads.

---

Scalability Target:

100,000 Stories

10,000,000 Transcript Segments

1,000,000 Knowledge Objects

100,000,000 Graph Relationships

---

# 17. Success Criteria

## Phase 1

* User Management
* Source Management
* Transcript Import
* Story Management
* Knowledge Extraction
* Narrative Article
* Knowledge Article

---

## Phase 2

* Editorial Workflow
* Review System
* Publishing System
* Neo4j Projection
* Weaviate Projection

---

## Phase 3

* Research Workspace
* Story DNA
* Cultural Intelligence
* Adaptation Intelligence
* Cultural Evolution Analytics

---

# 18. Out of Scope (Current Phase)

Not included in MVP:

* Microservices
* Local LLM Hosting
* GPU Inference
* Real-time Collaboration
* Public Knowledge API
* Story Recommendation Engine
* Cultural Prediction Engine

These may be introduced in future phases.
