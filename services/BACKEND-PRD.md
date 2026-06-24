Untuk kebutuhan Anda, saya tidak akan membuat PRD level "fitur". Saya akan membuat **Platform Backend PRD** level Principal Engineer / Staff Engineer yang menjadi kontrak implementasi seluruh backend team.

Dokumen ini harus menjadi referensi untuk:

* Backend Engineers
* AI Engineers
* Data Engineers
* DBA
* DevOps
* Solution Architect
* Technical Lead

---

# Backend Platform PRD

## The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Platform Engineering

Target Stack:

```text
Java 25
Spring Boot 4.x
PostgreSQL 18
Neo4j 5.26
Weaviate 1.37
Python 3.14
React 19
Next.js 16
Redpanda
Docker
Kubernetes (Future)
```

---

# 1. Executive Summary

The Living Atlas of Indonesian Mystery Culture is a knowledge platform designed to transform mystery-related content from podcasts, YouTube channels, folklore archives, interviews, and cultural records into a structured, searchable, and verifiable cultural knowledge system.

The platform consists of:

```text
Content Platform
Knowledge Platform
Research Platform
AI Processing Platform
Data Platform
Publishing Platform
```

The system must support:

* Multi-tenancy
* Event-driven architecture
* Knowledge graph generation
* AI-assisted knowledge extraction
* Editorial workflows
* Research workspaces
* Long-term cultural preservation

---

# 2. Architecture Principles

## 2.1 Monorepo First

All services reside in a single repository.

Reason:

```text
Small team
Shared domain model
Rapid iteration
Reduced operational complexity
```

---

## 2.2 Modular Monolith First

Each service is internally modular.

Avoid:

```text
controller
service
repository
entity
```

at application level.

Prefer:

```text
bounded context modules
```

Example:

```text
story
article
review
workflow
knowledge
```

---

## 2.3 Event Driven Ready

Every important state transition emits domain events.

Initial deployment:

```text
Transactional Outbox
```

Future:

```text
Redpanda
Kafka
```

---

## 2.4 PostgreSQL Is Source of Truth

Ownership:

```text
PostgreSQL
    Source of Truth

Neo4j
    Read Projection

Weaviate
    Search Projection
```

Forbidden:

```text
Write Neo4j directly

Write Weaviate directly
```

---

# 3. Functional Domains

---

# Identity Domain

Owner:

```text
identity-service
```

Responsibilities:

```text
Authentication

Authorization

Tenants

Workspaces

Roles

ABAC Policies

User Preferences

API Keys
```

---

## Functional Requirements

### Users

Capabilities:

```text
Register
Login
Deactivate
Invite
Suspend
Delete
```

---

### Tenants

Capabilities:

```text
Create Tenant

Update Tenant

Archive Tenant

Workspace Isolation
```

---

### Roles

Capabilities:

```text
System Admin

Tenant Admin

Researcher

Editor

Reviewer

Creator

Reader
```

---

### ABAC

Policy Dimensions:

```text
Tenant

Workspace

Resource

Ownership

Status

Classification
```

Example:

```text
Researcher

Can View:
Knowledge Objects

Where:
tenant_id = current_tenant

AND

status != archived
```

---

# Source Domain

Owner:

```text
content-service
```

Responsibilities:

```text
Channel Registry

Video Registry

Transcript Registry

Metadata Registry

Source Provenance
```

---

## Functional Requirements

### Channel Management

Support:

```text
YouTube
Podcast
RSS
Manual Sources
```

---

### Metadata Collection

Store:

```text
Title

Description

Tags

Categories

Published Date

Creator

Playlist

Channel
```

---

### Transcript Management

Support:

```text
Manual Transcript

YouTube Captions

Imported Transcript
```

---

### Provenance

Every knowledge object must trace back to:

```text
Knowledge Object

↓

Evidence

↓

Transcript Segment

↓

Transcript

↓

Source
```

---

# Knowledge Domain

Owner:

```text
knowledge-service
```

Responsibilities:

```text
Knowledge Objects

Themes

Motifs

Folklore

Beliefs

Traditions

Claims

Contradictions
```

---

## Functional Requirements

### Knowledge Objects

Capabilities:

```text
Create

Update

Merge

Split

Archive

Version
```

---

### Entity Types

Support:

```text
Spirit

Ghost

Folklore

Location

Character

Person

Belief

Tradition

Ritual

Artifact

Creature
```

---

### Claim Management

Store:

```text
Claim

Evidence

Confidence

Sources

Reviewer Notes
```

---

### Contradictions

Support:

```text
Conflicting Claims

Multiple Versions

Regional Variations

Historical Variations
```

---

# Story Domain

Owner:

```text
content-service
```

Responsibilities:

```text
Stories

Story Versions

Story Evidence

Story Relationships
```

---

## Story Types

Support:

```text
Investigation

Folklore

Urban Legend

Personal Experience

Historical

Cultural
```

---

### Versioning

Requirement:

```text
Immutable Versions
```

Never overwrite.

Always create new version.

---

# Article Domain

Owner:

```text
content-service
```

Responsibilities:

```text
Narrative Articles

Knowledge Articles

News Articles

Creative Articles
```

---

## Article Types

### Narrative

Rule:

```text
Must follow source
```

---

### Knowledge

Rule:

```text
Structured
Research-focused
```

---

### News

Rule:

```text
Journalistic style
```

---

### Creative

Rule:

```text
Not canonical

Not used for graph
```

---

# Research Domain

Owner:

```text
research-service
```

Responsibilities:

```text
Collections

Annotations

Notes

Saved Queries

Exports
```

---

## Collections

Capabilities:

```text
Create Collection

Add Story

Add Knowledge Object

Share Collection
```

---

## Annotations

Support:

```text
Story Annotation

Entity Annotation

Transcript Annotation
```

---

# Workflow Domain

Owner:

```text
workflow-service
```

Responsibilities:

```text
Review

Approval

Publishing

Moderation
```

---

## State Machine

### Story

```text
DRAFT

↓

REVIEW

↓

APPROVED

↓

PUBLISHED

↓

ARCHIVED
```

---

### Knowledge

```text
EXTRACTED

↓

REVIEW_REQUIRED

↓

VERIFIED

↓

PUBLISHED
```

---

# 4. AI Integration Requirements

AI services run outside Spring Boot.

Communication:

```text
REST

Events

Job Queue
```

---

## Canonical Extraction

Input:

```text
Transcript
Metadata
```

Output:

```text
Canonical Story JSON
```

---

## Knowledge Extraction

Output:

```text
Themes

Motifs

Claims

Beliefs

Entities
```

---

## Article Generation

Output:

```text
Narrative

Knowledge

News

Creative
```

---

# 5. Event Architecture

Required Events:

```text
SourceRegistered

TranscriptImported

StoryCreated

StoryVersionCreated

KnowledgeObjectCreated

KnowledgeObjectMerged

ClaimCreated

ArticleGenerated

ArticlePublished

ReviewApproved

ReviewRejected
```

---

# 6. Non Functional Requirements

---

## Performance

Target:

```text
API p95 < 300ms

API p99 < 1 second
```

excluding AI operations.

---

## Availability

Target:

```text
99.5%
```

MVP

---

## Scalability

Target:

```text
100k stories

10M transcript segments

1M knowledge objects
```

---

## Security

Requirements:

```text
JWT

OAuth2

ABAC

Audit Trail

Encryption At Rest

Encryption In Transit
```

---

# 7. Audit Requirements

Every table must include:

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

where applicable.

---

# 8. Observability

Required:

```text
Structured Logging

Distributed Tracing Ready

Metrics

Health Checks

Audit Logs
```

Stack:

```text
OpenTelemetry

Prometheus

Grafana

Loki
```

---

# 9. Internal Service Structure

Example:

```text
knowledge-service

knowledge
├── api
├── application
├── domain
├── infrastructure
├── projection

claims
├── api
├── application
├── domain
├── infrastructure
├── projection

folklore
├── api
├── application
├── domain
├── infrastructure
├── projection
```

Rules:

```text
Module communicates through Application Layer.

Domain must not depend on Infrastructure.

No cross-module database access.

No shared entities.
```

---

# 10. Success Criteria

Phase 1 Success:

```text
User Management

Tenant Management

Transcript Import

Story Creation

Knowledge Extraction

Narrative Article

Knowledge Article
```

Phase 2 Success:

```text
Workflow

Review

Publishing

Neo4j Projection

Weaviate Projection
```

Phase 3 Success:

```text
Research Workspace

Knowledge Intelligence

Story DNA

Adaptation Scoring

Cultural Evolution Analytics
```

---

Jika saya menjadi Principal Architect proyek ini, dokumen berikutnya yang harus dibuat setelah PRD Backend adalah:

1. **ADR-001 sampai ADR-020** (keputusan arsitektur inti)
2. **Domain Event Catalog**
3. **Bounded Context Map**
4. **API Contract Specification (OpenAPI 3.1)**
5. **Database Ownership Matrix**
6. **State Machine Specification**
7. **Multi-Tenant & ABAC Design Document**
8. **AI Pipeline PRD**
9. **Knowledge Graph Modeling Specification**
10. **Deployment & Environment Strategy (Local, Dev, Staging, Production)**

Dokumen-dokumen tersebut akan jauh lebih menentukan keberhasilan implementasi dibanding DDL atau endpoint API individual.
