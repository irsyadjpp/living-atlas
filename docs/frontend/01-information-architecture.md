# Information Architecture

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Product Design Team

Last Updated: June 2026

---

# Purpose

This document defines the Information Architecture (IA) for every frontend application within The Living Atlas ecosystem.

The IA describes **how knowledge is organized**, **how users mentally model the platform**, and **how information flows between pages**.

Unlike navigation, which determines how users move through the application, Information Architecture determines **what exists** and **how every piece of information relates to one another**.

The IA serves as the canonical blueprint for:

- Product Design
- UX Design
- Frontend Engineering
- Backend API Design
- Knowledge Graph Design
- AI Discovery
- Search
- Navigation

---

# Philosophy

Traditional websites organize information as pages.

The Living Atlas organizes information as knowledge.

Every page is merely one representation of an underlying knowledge object.

The platform therefore follows:

```
Knowledge

↓

Views

↓

Pages
```

rather than

```
Pages

↓

Navigation
```

Knowledge always comes first.

---

# Information Hierarchy

The platform is divided into six conceptual layers.

```
Platform

↓

Knowledge Domain

↓

Knowledge Object

↓

Representation

↓

Interaction

↓

Presentation
```

Each layer has a distinct responsibility.

---

# Layer 1 — Platform

Represents the entire Living Atlas ecosystem.

Contains:

- Public Atlas
- Research Workspace
- Editorial Workspace
- Future Studio

Users perceive a single product.

---

# Layer 2 — Knowledge Domains

Knowledge is grouped into domains.

Domains are not pages.

Domains represent conceptual groupings.

Core domains include:

Stories

Articles

Knowledge

Entities

Cultures

Regions

Beliefs

Rituals

Traditions

Historical Events

Themes

Motifs

Creators

Researchers

Collections

Evidence

Timeline

Media

Sources

Relationships

Claims

Annotations

Workspaces

Every future capability belongs to exactly one primary domain.

---

# Layer 3 — Knowledge Objects

Domains contain objects.

Example:

Stories

↓

Story

Story

Story

Knowledge

↓

Spirit

Ritual

Artifact

Belief

Region

↓

Province

Village

Mountain

Forest

River

Knowledge Objects represent canonical data.

---

# Layer 4 — Representations

Knowledge Objects may have multiple representations.

Example

Story

↓

Narrative Article

Knowledge Article

Timeline

Graph

Map

Transcript

Evidence

AI Summary

Research View

These are all different views of the same object.

No duplicate knowledge exists.

---

# Layer 5 — Interactions

Interactions define what users can do.

Examples:

Read

Explore

Compare

Bookmark

Annotate

Collect

Share

Export

Search

Visualize

Filter

Every interaction is independent of presentation.

---

# Layer 6 — Presentation

Presentation defines visual layout.

Examples:

Cards

Tables

Graph

Timeline

Map

Tree

Gallery

Reader

Presentation changes.

Knowledge remains stable.

---

# Knowledge Domains

The Living Atlas currently defines the following primary domains.

## Story Domain

Purpose

Narrative representation of an investigation or folklore.

Contains:

Story

Chapter

Scene

Investigation

Narrative Article

Knowledge Article

News Article

Creative Article

---

## Knowledge Domain

Purpose

Canonical structured knowledge.

Contains:

Entity

Belief

Ritual

Tradition

Artifact

Theme

Motif

Historical Event

Claim

Relationship

Evidence

---

## Culture Domain

Purpose

Regional cultural identity.

Contains:

Culture

Ethnic Group

Custom

Traditional Practice

Language

Regional Interpretation

---

## Geography Domain

Purpose

Spatial understanding.

Contains:

Province

City

Village

Mountain

Forest

River

Island

Region

Coordinates (optional)

Sensitive Location (protected)

---

## Creator Domain

Purpose

Content provenance.

Contains:

YouTube Creator

Researcher

Organization

Podcast

Production House

Interview Source

---

## Source Domain

Purpose

Original evidence.

Contains:

YouTube Video

Podcast

Book

Research Paper

Interview

Historical Record

Community Story

Photograph

Audio

Transcript

---

## Research Domain

Purpose

Professional research workflow.

Contains:

Collection

Workspace

Annotation

Research Note

Saved Graph

Comparison

---

# Relationships

Every domain connects with every other domain.

Example

```
Story

↓

mentions

↓

Spirit

↓

appears_in

↓

Region

↓

belongs_to

↓

Culture

↓

documents

↓

Belief

↓

supported_by

↓

Source
```

Relationships are primary navigation mechanisms.

---

# Information Ownership

Every knowledge object has exactly one owner.

Example

```
Story

Owner

Content Service

Entity

Owner

Knowledge Service

Research Note

Owner

Research Service

User

Owner

Identity Service
```

This mirrors backend bounded contexts.

---

# Canonical Object Identity

Every object must have one immutable identifier.

Example

```
Story

story_id

Entity

entity_id

Culture

culture_id

Source

source_id
```

Pages must never use mutable titles as identifiers.

---

# URL Philosophy

URLs represent knowledge.

Not implementation.

Example

```
/stories/the-house-of-bandung

/entities/kuntilanak

/cultures/sunda

/rituals/ruwatan

/regions/west-java

/sources/jurnal-risa-episode-120
```

Stable URLs preserve long-term references.

---

# Cross-Domain Navigation

Users should never become trapped inside one domain.

Example

Story

↓

Entity

↓

Culture

↓

Timeline

↓

Source

↓

Another Story

Every page must expose meaningful exits.

---

# Information Density

Different applications expose different levels of information.

Public Atlas

Low

Research Workspace

Medium

Editorial Workspace

High

Future Studio

High

The same knowledge object is reused.

Only presentation changes.

---

# Future Domains

The architecture intentionally supports future expansion.

Potential additions include:

Dream Interpretation

Traditional Medicine

Ancient Manuscripts

Museum Collections

Archaeological Sites

Religious Practices

Audio Archives

Digital Exhibitions

No architectural changes should be required when introducing new domains.

---

# Guiding Principle

The Living Atlas is not a collection of webpages.

It is a living knowledge system.

Pages, navigation, articles, maps, graphs, and timelines are simply different windows through which users observe the same interconnected cultural knowledge.