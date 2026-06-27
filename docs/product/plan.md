Saya justru ingin mengubah sedikit struktur **Phase 1 (Product)**.

Kalau saya menjadi VP Product di Apple, saya tidak akan memulai dari *Product Vision*.

Saya akan memulai dari **Product Overview**, karena seluruh orang yang baru masuk ke project harus bisa memahami proyek ini dalam waktu ±30 menit.

Kemudian baru turun ke vision, principles, users, dan seterusnya.

Saya juga akan menambahkan satu file lagi.

Jadi Product menjadi:

```text
docs/product/

00-product-overview.md
01-product-vision.md
02-product-principles.md
03-target-users.md
04-business-model.md
05-roadmap.md
06-success-metrics.md
07-product-glossary.md
README.md
```

---

# Phase 1 — Product

Tujuan layer ini adalah menjawab pertanyaan:

> **"Apa yang sedang kita bangun?"**

Bukan:

> "Bagaimana cara membangunnya?"

Tidak ada pembahasan React.

Tidak ada Spring.

Tidak ada Database.

Tidak ada AI.

Semuanya fokus ke produk.

---

# 00-product-overview.md

Ini adalah dokumen yang akan dibaca pertama kali oleh semua orang.

Target pembaca:

* CEO
* CTO
* Engineer baru
* Designer
* Investor
* Researcher
* Penulis
* AI Engineer

Isi lengkapnya:

```text
Executive Summary

Problem Statement

Current Industry Landscape

Why Existing Platforms Fail

Vision Summary

Product Definition

Core Concepts

What The Living Atlas Is

What The Living Atlas Is NOT

Knowledge Platform Philosophy

Target Audience Overview

Platform Capabilities

Knowledge Types

Primary User Journeys

Long-term Vision (10 Years)

Success Definition

Project Scope

Out of Scope

Technology Independence

Documentation Structure

Reading Guide
```

Target sekitar

**25–35 halaman**

---

# 01-product-vision.md

Menjelaskan masa depan produk.

Isi:

```text
Vision Statement

Mission Statement

Purpose

Why This Product Exists

Cultural Preservation Vision

Knowledge Democratization

AI Vision

Creator Economy Vision

Research Vision

Education Vision

Museum Vision

Global Vision

Ten-Year Vision

Twenty-Year Vision

North Star

Product Values

Success Looks Like
```

Target:

20 halaman

---

# 02-product-principles.md

Menurut saya ini dokumen paling penting.

Semua keputusan produk harus mengikuti prinsip ini.

Contoh:

```text
Knowledge First

Evidence Before Opinion

Culture Before Entertainment

Preserve Context

One Source of Truth

Graph Native

Human + AI Collaboration

Reader First

Research Grade

Progressive Disclosure

Explainability

Transparency

Immutable Knowledge

Version Everything

AI Assists

Humans Decide

Open Standards

Long-term Thinking

Offline Friendly

Accessibility by Default
```

Setiap principle memiliki:

```text
Name

Statement

Motivation

Examples

Anti-pattern

Implementation Impact
```

Target:

40 halaman

---

# 03-target-users.md

Ini bukan Persona biasa.

Karena user platform sangat banyak.

Saya akan membuat:

```text
Reader

Horror Fans

Podcast Audience

Folklore Enthusiast

Researcher

Anthropologist

Historian

Journalist

Film Director

Producer

Writer

Game Studio

Comic Artist

Museum

School

University

Government

Community

Content Creator

AI Agent
```

Setiap user memiliki:

```text
Goals

Pain Points

Knowledge Level

Workflow

Daily Activities

Discovery Journey

Search Behaviour

Expected Features

KPIs
```

Target:

50 halaman

---

# 04-business-model.md

Bukan hanya monetisasi.

Tetapi bagaimana platform berkembang.

Isi:

```text
Market Opportunity

Current Competitors

Differentiation

Platform Strategy

Knowledge Strategy

Creator Economy

Licensing

Academic Partnerships

Museum Partnerships

Publishing

Film Industry

TV

Games

Documentary

Premium Features

Enterprise

API

Future Marketplace

Open Data Strategy

Revenue Streams

Cost Structure

Growth Flywheel
```

Target:

30 halaman

---

# 05-roadmap.md

Roadmap

bukan

Sprint.

Tetapi

3 tahun.

Contoh

```text
Phase 0

Foundation

↓

Phase 1

Knowledge Platform

↓

Phase 2

Atlas

↓

Phase 3

Research Workspace

↓

Phase 4

Creator Studio

↓

Phase 5

Public API

↓

Phase 6

Museum

↓

Phase 7

Education

↓

Phase 8

AI Agent Platform
```

Setiap phase memiliki

```text
Objectives

Major Features

Dependencies

Risks

Exit Criteria
```

Target

25 halaman

---

# 06-success-metrics.md

Bagaimana kita tahu produk berhasil?

Bukan hanya:

```text
DAU

MAU
```

Tetapi

```text
Knowledge Growth

Graph Density

Knowledge Quality

Evidence Coverage

Relationship Coverage

Transcript Coverage

Creator Participation

Research Usage

Citation Rate

Search Success

Discovery Success

Reading Completion

Knowledge Completion

Atlas Usage

AI Discovery Usage

Community Contribution

Editorial Accuracy

Extraction Accuracy
```

Target

20 halaman

---

# 07-product-glossary.md

Menurut saya ini wajib.

Karena nanti akan ada istilah:

```text
Story

Narrative

Knowledge Article

News Article

Knowledge Object

Knowledge Graph

Evidence

Transcript

Source

Creator

Culture

Region

Motif

Theme

Archetype

Folklore

Entity

Relationship

Canonical Story

Knowledge Layer

Knowledge Card

Atlas

Workspace

Discovery

Annotation

Collection

Extraction

Enrichment

Embedding

Projection

Lineage

Confidence
```

Semuanya harus memiliki definisi resmi.

Target

15 halaman

---

# README.md

Ini menjadi pintu masuk folder Product.

Isinya:

```text
Purpose

Reading Order

Dependencies

Related Documents

Document Ownership

Contribution Guidelines

Versioning Policy
```

---

# Estimasi Total Phase 1

| File               |             Estimasi |
| ------------------ | -------------------: |
| README             |          3–5 halaman |
| Product Overview   |        25–35 halaman |
| Product Vision     |           20 halaman |
| Product Principles |        35–40 halaman |
| Target Users       |        45–50 halaman |
| Business Model     |        25–30 halaman |
| Roadmap            |        20–25 halaman |
| Success Metrics    |        15–20 halaman |
| Product Glossary   |        15–20 halaman |
| **Total**          | **≈210–245 halaman** |

## Mengapa Phase 1 dibuat sedetail ini?

Dokumen Product adalah fondasi yang akan digunakan oleh seluruh disiplin: UX, frontend, backend, AI, data, dan bisnis. Jika Product sudah jelas, maka keputusan pada layer berikutnya akan lebih konsisten dan minim revisi. Untuk platform seperti **The Living Atlas of Indonesian Mystery Culture**, investasi terbesar sebaiknya dilakukan pada kejelasan visi, ruang lingkup, prinsip, dan definisi domain sejak awal, karena seluruh arsitektur pengetahuan bergantung pada keputusan-keputusan tersebut.
