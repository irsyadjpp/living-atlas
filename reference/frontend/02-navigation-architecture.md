# Navigation Architecture

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Product Design Team

Last Updated: June 2026

---

# Purpose

This document defines how users navigate throughout The Living Atlas ecosystem.

Navigation is more than moving between pages.

It is the mechanism through which users explore relationships, discover new knowledge, and gradually build understanding.

Unlike traditional websites where navigation is primarily hierarchical, The Living Atlas combines:

* Hierarchical Navigation
* Contextual Navigation
* Knowledge Navigation
* Exploratory Navigation
* Semantic Navigation

The objective is to make every interaction feel like exploring a living atlas rather than browsing disconnected webpages.

---

# Navigation Philosophy

Navigation should encourage curiosity.

Users should continuously discover new knowledge through meaningful relationships instead of manually searching for everything.

Traditional websites follow:

```
Home

↓

Category

↓

Article
```

Living Atlas follows:

```
Story

↓

Spirit

↓

Belief

↓

Region

↓

Culture

↓

Timeline

↓

Evidence

↓

Another Story
```

The platform is designed around **continuous exploration**.

---

# Navigation Principles

## Principle 1 — Knowledge Before Menu

Primary navigation should expose knowledge domains instead of website sections.

Avoid:

```
Articles

Videos

Gallery

About
```

Prefer:

```
Stories

Knowledge

Cultures

Regions

Timeline

Atlas

Research
```

Users navigate concepts.

Not content types.

---

## Principle 2 — Contextual Navigation

Every page should expose navigation based on the current context.

Example:

Story

↓

Related Entities

↓

Related Rituals

↓

Related Regions

↓

Related Stories

↓

Timeline

↓

Creator

Navigation adapts to content.

---

## Principle 3 — Progressive Navigation

Navigation complexity increases gradually.

Reader

↓

Simple

Researcher

↓

Advanced

Editor

↓

Professional

The interface never overwhelms new users.

---

## Principle 4 — Multiple Paths

Every important object should be reachable through multiple routes.

Example:

Kuntilanak

Reachable from:

Story

Search

Knowledge

Atlas

Region

Timeline

Culture

Relationship Explorer

No information should depend on a single navigation path.

---

# Global Navigation

Visible throughout the platform.

Primary Items

```
Home

Stories

Knowledge

Atlas

Cultures

Regions

Timeline

Creators

Research
```

Persistent utilities:

```
Search

Bookmarks

Notifications

Profile

Settings
```

Global navigation never changes.

---

# Local Navigation

Every domain owns a secondary navigation.

Example:

Stories

```
Latest

Popular

Investigations

Folklore

Collections
```

Knowledge

```
Entities

Beliefs

Rituals

Traditions

Artifacts

Claims
```

Research

```
Collections

Annotations

Saved Queries

Graph Workspace

Exports
```

Local navigation changes by domain.

---

# Context Navigation

Displayed inside detail pages.

Example:

Story Detail

```
Overview

Narrative

Knowledge

Evidence

Timeline

Related Stories

Sources

Comments (Future)
```

Entity Detail

```
Overview

History

Relationships

Stories

Evidence

Regional Variants

Timeline
```

The current object determines available sections.

---

# Breadcrumb Strategy

Breadcrumbs reflect knowledge hierarchy rather than URL hierarchy.

Example

```
Stories

↓

Jurnal Risa

↓

Rumah Tua Bandung
```

Not

```
Home

↓

Stories

↓

Page

↓

Detail
```

Breadcrumbs answer:

"Where am I within the knowledge?"

---

# Search-Centric Navigation

Search is a first-class navigation mechanism.

Users may navigate directly through search without using menus.

Supported search types:

* Story Search
* Entity Search
* Region Search
* Culture Search
* Ritual Search
* Creator Search
* Evidence Search
* Knowledge Search

Search becomes another navigation layer.

---

# Knowledge Navigation

Every knowledge object exposes:

```
Related Stories

Related Knowledge

Related Entities

Related Rituals

Related Beliefs

Related Regions

Related Cultures

Related Timeline

Related Evidence
```

Users move through relationships instead of categories.

---

# Relationship Navigation

Relationships themselves are clickable.

Example:

```
Kuntilanak

Appears In

↓

Story

Shared Theme

↓

Another Story

Historical Variant

↓

Pontianak
```

Relationships are treated as navigable objects.

---

# Atlas Navigation

Atlas is not a page.

Atlas is an exploration mode.

Users begin from:

Region

↓

Culture

↓

Belief

↓

Story

↓

Evidence

↓

Timeline

↓

Another Region

Atlas navigation encourages spatial exploration.

---

# Timeline Navigation

Timeline enables temporal navigation.

Example:

```
Historical Event

↓

Traditional Practice

↓

Modern Investigation

↓

Current Interpretation
```

Users navigate through time.

---

# Creator Navigation

Creators become exploration hubs.

Creator

↓

Stories

↓

Knowledge

↓

Regions

↓

Collaborators

↓

Appearances

↓

Referenced Sources

Creators are part of the knowledge graph.

---

# AI Discovery Navigation

AI Discovery supplements—not replaces—traditional navigation.

Capabilities:

* Similar stories
* Related entities
* Semantic search
* Suggested explorations
* Hidden relationships

AI recommendations always explain *why* an item is suggested.

---

# Graph Navigation

Graph navigation supports exploratory research.

Capabilities:

* Expand node
* Collapse node
* Filter relationships
* Highlight paths
* Compare nodes
* Traverse graph

Graph interactions never replace traditional navigation.

They complement it.

---

# Keyboard Navigation

The platform must support keyboard-first navigation.

Examples:

```
/

Focus Search

G then S

Stories

G then K

Knowledge

G then A

Atlas

G then T

Timeline

Esc

Close overlays
```

Keyboard navigation improves accessibility and productivity.

---

# Mobile Navigation

Navigation adapts to touch.

Primary navigation:

Bottom Navigation

Secondary navigation:

Slide-over Panels

Knowledge exploration:

Gesture-friendly cards

Graph interaction:

Simplified touch controls

Complex research tools remain desktop-first.

---

# Navigation Persistence

The platform remembers:

Recently visited stories

Recent searches

Recent entities

Expanded graph nodes

Open collections

Current filters

Users should feel continuity across sessions.

---

# Deep Linking

Every meaningful state should be shareable.

Examples:

Story

Entity

Knowledge Object

Atlas View

Timeline Position

Research Collection

Saved Search

Future:

Graph State

Annotation

Comparison

URLs become portable knowledge references.

---

# Navigation Analytics

Navigation should continuously improve.

Metrics include:

Search Success Rate

Navigation Depth

Knowledge Exploration Rate

Relationship Click Rate

Dead-End Rate

Breadcrumb Usage

Atlas Usage

Timeline Usage

These metrics measure understanding—not engagement.

---

# Anti-Patterns

The platform intentionally avoids:

* Mega menus
* Infinite nested navigation
* Hover-only navigation
* Hidden navigation
* Content silos
* Dead-end pages
* Clickbait recommendations

Navigation should remain predictable, discoverable, and purposeful.

---

# Guiding Principle

Navigation is not about helping users find pages.

It is about helping users discover knowledge.

Every navigation decision should answer one question:

> "What meaningful connection can the user discover next?"

The Living Atlas should always feel like an evolving cultural landscape where every destination naturally leads to another layer of understanding.
