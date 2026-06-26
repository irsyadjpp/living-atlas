# Routing Specification

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Frontend Platform Team

Last Updated: June 2026

---

# Purpose

This document defines the canonical routing architecture for every frontend application within The Living Atlas ecosystem.

Routing is not merely URL mapping.

Every route represents a stable knowledge address.

A route should remain valid for many years regardless of frontend implementation, backend architecture, or technology stack.

URLs become permanent references that may appear in:

- Search engines
- Academic citations
- Research papers
- Bookmarks
- AI responses
- Knowledge Graph
- QR Codes
- Museum installations
- Public APIs

Therefore URL stability is considered a platform requirement.

---

# Routing Philosophy

The platform routes to knowledge.

Not pages.

Incorrect

```

/page/123

/content?id=123

/article/582

```

Correct

```

/stories/rumah-tua-bandung

/entities/kuntilanak

/cultures/sunda

/regions/bandung

```

Users should understand URLs without documentation.

---

# Routing Principles

## Principle 1

Human Readable

Good

```

/stories/rumah-tua-bandung

```

Bad

```

/story?id=918372

```

---

## Principle 2

Stable

Titles may change.

Slugs should rarely change.

IDs never change.

The canonical identifier remains immutable.

---

## Principle 3

Resource Based

URLs represent resources.

Not actions.

Incorrect

```

/getStory

/createStory

/deleteStory

```

Correct

```

/stories

/stories/{slug}

/stories/{slug}/timeline

```

---

## Principle 4

Plural Collections

Collections are plural.

```

/stories

/articles

/entities

/cultures

/regions

```

Individual objects use singular slugs.

---

## Principle 5

No Technology Leakage

Never expose:

```

/v1/

/api/

/react/

/next/

/index.php

```

Frontend technology must remain invisible.

---

# Route Categories

The platform defines six routing categories.

```
Public

Workspace

Authentication

System

API

Deep Link
```

---

# Public Routes

Homepage

```
/
```

Stories

```
/stories
```

Story

```
/stories/{slug}
```

Knowledge Articles

```
/knowledge
```

Knowledge Detail

```
/knowledge/{slug}
```

Entities

```
/entities
```

Entity

```
/entities/{slug}
```

Cultures

```
/cultures
```

Culture

```
/cultures/{slug}
```

Regions

```
/regions
```

Region

```
/regions/{slug}
```

Creators

```
/creators
```

Creator

```
/creators/{slug}
```

Timeline

```
/timeline
```

Atlas

```
/atlas
```

Search

```
/search
```

---

# Story Routes

Story Detail

```
/stories/{slug}
```

Narrative View

```
/stories/{slug}/read
```

Knowledge View

```
/stories/{slug}/knowledge
```

Timeline

```
/stories/{slug}/timeline
```

Evidence

```
/stories/{slug}/evidence
```

Sources

```
/stories/{slug}/sources
```

Transcript

```
/stories/{slug}/transcript
```

Relationships

```
/stories/{slug}/relationships
```

Media

```
/stories/{slug}/media
```

---

# Knowledge Routes

```
/knowledge/{slug}
```

Overview

```
/knowledge/{slug}
```

Evidence

```
/knowledge/{slug}/evidence
```

Claims

```
/knowledge/{slug}/claims
```

Relationships

```
/knowledge/{slug}/relationships
```

Timeline

```
/knowledge/{slug}/timeline
```

Sources

```
/knowledge/{slug}/sources
```

---

# Entity Routes

```
/entities/{slug}
```

Overview

History

Stories

Knowledge

Relationships

Timeline

Evidence

Variants

Each receives its own route.

---

# Atlas Routes

Atlas Home

```
/atlas
```

Region

```
/atlas/regions/{slug}
```

Culture

```
/atlas/cultures/{slug}
```

Knowledge

```
/atlas/knowledge/{slug}
```

Entity

```
/atlas/entities/{slug}
```

Future

```
/atlas/graph

/atlas/map

/atlas/timeline
```

---

# Search Routes

Global Search

```
/search
```

Query

```
/search?q=kuntilanak
```

Filtered

```
/search?q=kuntilanak&type=entity
```

Research

```
/search?workspace=research
```

---

# Creator Routes

```
/creators/{slug}
```

Sections

Stories

Knowledge

Timeline

Media

Collaborations

Playlists

Statistics

---

# Region Routes

```
/regions/{slug}
```

Contains

Stories

Knowledge

Culture

Timeline

Map

Beliefs

Rituals

---

# Research Routes

Workspace

```
/research
```

Collections

```
/research/collections
```

Collection

```
/research/collections/{id}
```

Annotations

```
/research/annotations
```

Workspace

```
/research/workspaces/{id}
```

Graph

```
/research/graph
```

Comparison

```
/research/compare
```

Exports

```
/research/export
```

---

# Editorial Routes

Dashboard

```
/admin
```

Stories

Knowledge

Sources

Review Queue

Publishing

Workflow

Audit

AI Review

Prompt Registry

---

# Authentication

```
/login

/logout

/register

/forgot-password

/reset-password

/profile

/settings
```

---

# Deep Linking

Every significant state should be shareable.

Examples

Story

```
/stories/rumah-tua-bandung
```

Specific Section

```
/stories/rumah-tua-bandung#timeline
```

Knowledge Node

```
/entities/kuntilanak
```

Timeline Event

```
/timeline/event/183
```

Future

Graph State

Collection State

Search State

Comparison State

---

# URL Parameters

Only use parameters for transient state.

Examples

Sorting

Filtering

Pagination

Search

Incorrect

```
/stories/page/2
```

Correct

```
/stories?page=2
```

---

# Slug Rules

Slug requirements:

Lowercase

ASCII

Hyphen separated

Immutable after publication

Example

```
rumah-tua-bandung

penampakan-gunung-salak

kuntilanak

ritual-ruwatan
```

Never use spaces.

Never use underscores.

---

# Canonical IDs

Every object contains:

UUID

Slug

The frontend always routes by slug.

The backend resolves slug to UUID.

UUIDs are never exposed publicly unless required for APIs.

---

# Redirect Policy

Old URLs remain valid.

Slug changes create:

Permanent Redirect (301)

Never return 404 after editorial slug changes.

---

# SEO Strategy

Every route includes:

Canonical URL

OpenGraph

Twitter Card

JSON-LD

Structured Data

Breadcrumb

Meta Description

Title

Robots

Hreflang (future)

---

# Internationalization

Future support

```
/id/stories/...

/en/stories/...
```

Knowledge identifiers remain unchanged.

Only translated slugs may differ if necessary.

---

# Access Control

Public routes

Accessible without login.

Research routes

Require authentication.

Editorial routes

Require authorization.

Permissions originate from Identity Service.

Frontend never performs authorization logic independently.

---

# Routing Ownership

Frontend owns:

Route rendering

Navigation

Prefetching

Breadcrumbs

Backend owns:

Resource existence

Permissions

Canonical data

State transitions

---

# Future Expansion

Routing architecture intentionally supports future capabilities.

Examples

Museum

```
/museum
```

Education

```
/education
```

API Explorer

```
/developer
```

Creative Studio

```
/studio
```

Digital Archive

```
/archive
```

None of these require changes to existing routes.

---

# Guiding Principle

A URL is a permanent cultural reference.

It should remain meaningful, human-readable, stable, and trustworthy for decades.

Every route should represent knowledge—not implementation.