# Prinsip Arsitektur

Saya akan menggunakan:

```text
Monorepo
Modular Monolith First
Event-Driven Ready
```

Bukan microservice sejak awal.

Karena:

```text
User sekarang:
100
1000
5000

Microservice:
Overkill
```

Tetapi struktur harus siap dipecah nanti.

---

# Repository Structure

```text
living-atlas/

├── apps/
├── services/
├── packages/
├── infrastructure/
├── data-platform/
├── ai-platform/
├── docs/
└── scripts/
```

---

# Apps

User-facing applications.

```text
apps/

├── web-atlas/
├── web-admin/
├── web-research/
├── web-studio/
├── mobile/
```

---

## web-atlas

Public website.

Stack:

```text
React
Next.js
TypeScript
```

Features:

```text
Homepage

Story Detail

Knowledge Article

Atlas Visualization

AI Discovery Search

Creator Pages

Culture Pages
```

---

## web-admin

Editorial CMS.

```text
React
Next.js
```

Features:

```text
Source Review

Article Review

Knowledge Review

Workflow Approval

AI Extraction Review
```

---

## web-research

Workspace.

```text
Research Collections

Annotations

Saved Graphs

Comparisons

Exports
```

---

## web-studio

Future.

```text
Creative Stories

Story Generation

Writer Workspace
```

---

# Services

Business layer.

---

## gateway-service

```text
Spring Boot
```

Responsibilities:

```text
Authentication

Authorization

API Aggregation

Rate Limiting
```

---

## identity-service

```text
Spring Boot
```

Domain:

```text
Users

Tenants

Workspace

RBAC

ABAC
```

---

## content-service

```text
Spring Boot
```

Domain:

```text
Stories

Articles

Publishing

Versioning
```

---

## knowledge-service

```text
Spring Boot
```

Domain:

```text
Themes

Motifs

Archetypes

Folklore

Culture
```

---

## research-service

```text
Spring Boot
```

Domain:

```text
Collections

Annotations

Research Notes
```

---

## workflow-service

```text
Spring Boot
```

Domain:

```text
Review

Approval

Publishing Workflow
```

---

# AI Platform

Ini saya pisahkan.

---

```text
ai-platform/

├── ingestion-service
├── extraction-service
├── enrichment-service
├── embedding-service
├── article-service
├── orchestration-service
```

---

## ingestion-service

Python.

Karena YT-DLP.

```text
Python

YT-DLP

FFmpeg
```

Responsibilities:

```text
Channel Crawl

Playlist Crawl

Video Crawl

Metadata Capture
```

---

## extraction-service

Python.

Responsibilities:

```text
WhisperX

Pyannote

Transcript

Speaker Extraction
```

---

## enrichment-service

Python.

Responsibilities:

```text
Theme Extraction

Motif Extraction

Story Extraction

Knowledge Extraction
```

Models:

```text
Gemini

Claude

OpenAI
```

---

## embedding-service

Python.

Responsibilities:

```text
Vector Creation

Weaviate Sync
```

---

## article-service

Python.

Responsibilities:

```text
Narrative Article

Knowledge Article

News Article

Creative Article
```

---

## orchestration-service

Python.

Responsibilities:

```text
Pipeline Execution

Retry

Queue Management

Scheduling
```

---

# Data Platform

---

```text
data-platform/

├── neo4j-sync
├── weaviate-sync
├── analytics
├── lineage
```

---

## neo4j-sync

Spring Boot atau Python.

Responsibilities:

```text
Knowledge Graph Projection
```

---

## weaviate-sync

Responsibilities:

```text
Embedding Sync

Chunk Sync
```

---

## analytics

Future.

```text
Creator Intelligence

Trend Analysis

Cultural Evolution
```

---

# Packages

Shared code.

---

```text
packages/

├── ui
├── design-system
├── api-client
├── shared-types
├── shared-events
├── shared-security
```

---

## design-system

Sangat penting.

```text
Tailwind

Radix

Shadcn
```

Atau design system custom.

---

# Infrastructure

---

```text
infrastructure/

├── docker
├── kubernetes
├── terraform
├── monitoring
├── observability
```

---

# Docs

---

```text
docs/

├── architecture
├── database
├── api
├── workflows
├── adr
```

---

Gunakan:

```text
ADR
Architecture Decision Records
```

untuk semua keputusan penting.

---

# Spring Boot Internal Structure

Saya tidak akan memakai:

```text
controller
service
repository
entity
```

untuk seluruh aplikasi.

Gunakan DDD modular.

---

Contoh:

```text
content-service/

src/main/java/

com.livingatlas.content

├── story
│   ├── api
│   ├── application
│   ├── domain
│   ├── infrastructure
│   └── projection
│
├── article
│   ├── api
│   ├── application
│   ├── domain
│   ├── infrastructure
│   └── projection
```

---

# Event Architecture

Sejak hari pertama.

---

Shared Events:

```text
packages/shared-events/

StoryCreated

StoryUpdated

ArticlePublished

VideoIngested

TranscriptGenerated

KnowledgeExtracted

EmbeddingCreated
```

---

Gunakan:

```text
Kafka
```

atau

```text
Redpanda
```

Saya lebih memilih Redpanda.

---

# Database Ownership

Sangat penting.

---

```text
PostgreSQL
=
Source of Truth

Neo4j
=
Projection

Weaviate
=
Projection
```

Jangan pernah:

```text
Update Neo4j langsung

Update Weaviate langsung
```

Semua perubahan harus berasal dari PostgreSQL.

---

# Struktur Monorepo Final

```text
living-atlas/

apps/
 ├── web-atlas
 ├── web-admin
 ├── web-research
 └── web-studio

services/
 ├── gateway-service
 ├── identity-service
 ├── content-service
 ├── knowledge-service
 ├── research-service
 └── workflow-service

ai-platform/
 ├── ingestion-service
 ├── extraction-service
 ├── enrichment-service
 ├── embedding-service
 ├── article-service
 └── orchestration-service

data-platform/
 ├── neo4j-sync
 ├── weaviate-sync
 ├── analytics
 └── lineage

packages/
 ├── design-system
 ├── api-client
 ├── shared-types
 ├── shared-events
 └── shared-security

infrastructure/
docs/
scripts/
```

Untuk visi jangka panjang, ini jauh lebih aman dibanding membuat satu Spring Boot besar atau langsung lompat ke puluhan microservice. Anda mendapatkan **modular monolith untuk domain bisnis**, **Python untuk AI/data pipeline**, dan **event-driven boundary** yang memungkinkan pemecahan menjadi microservice ketika jumlah data, tim, dan traffic benar-benar membutuhkannya.
