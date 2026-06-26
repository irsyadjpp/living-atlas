# Search Experience

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Product Design Team

Last Updated: June 2026

---

# Purpose

Search is the primary entry point into The Living Atlas.

Unlike traditional websites where search returns a list of documents, The Living Atlas treats search as a knowledge exploration experience.

Users are not searching for pages.

Users are searching for knowledge.

The search experience should help users:

* discover
* learn
* connect
* compare
* investigate
* understand

Search should continuously encourage exploration rather than terminate after displaying results.

---

# Search Philosophy

Traditional Search

```
Query

↓

Matching Documents

↓

End
```

Living Atlas Search

```
Query

↓

Knowledge Understanding

↓

Relevant Objects

↓

Relationships

↓

Evidence

↓

Recommendations

↓

Further Exploration
```

Search becomes the beginning of discovery.

---

# Search Principles

## Knowledge First

The search engine indexes knowledge objects rather than webpages.

Users may search for:

Stories

Entities

Beliefs

Rituals

Cultures

Regions

Creators

Historical Events

Claims

Evidence

Articles

Media

Transcript Segments

Timeline Events

Collections

Annotations

Everything participates in search.

---

## Explain Results

Every recommendation should explain why it appears.

Example

```
Kuntilanak

Appears in 42 stories

Mentioned by 7 creators

Found in 12 regions

Associated with 5 rituals

Referenced by 3 historical documents
```

Transparency builds trust.

---

## Multiple Search Strategies

The platform combines:

Keyword Search

Semantic Search

Graph Search

Relationship Search

Vector Search

Hybrid Search

No single algorithm is sufficient.

---

# Search Entry Points

Global Search

Always visible.

Quick Search

Keyboard shortcut.

Atlas Search

Spatial search.

Research Search

Advanced search.

AI Discovery

Conversational exploration.

Every search shares the same backend capability.

---

# Universal Search

The search bar should understand natural language.

Examples

```
kuntilanak

rumah tua

ritual kematian

cerita dari Bandung

podcast Nadia Omara

penampakan gunung

cerita berdasarkan perang

tradisi sunda

mitos laut selatan

kisah rumah sakit
```

Users should never need to know internal terminology.

---

# Search Scope

Results may include multiple object types.

Stories

Knowledge Articles

Narrative Articles

Entities

Cultures

Regions

Creators

Videos

Podcast Episodes

Evidence

Transcript Segments

Timeline Events

Research Collections

Each result clearly displays its type.

---

# Result Prioritization

Search relevance considers:

Text relevance

Semantic similarity

Relationship strength

Evidence quality

Editorial review

Popularity (low weight)

Freshness (when appropriate)

The platform prioritizes knowledge quality over popularity.

---

# Search Result Layout

Desktop

```
Search Input

↓

Suggested Queries

↓

Filters

↓

Result Groups

↓

Relationship Summary

↓

AI Discovery

↓

Continue Exploring
```

The search page should never feel like a plain list.

---

# Result Cards

Every result card contains:

Title

Object Type

Summary

Evidence Count

Relationship Count

Source Count

Confidence Indicator

Quick Actions

Users should understand why the object matters before opening it.

---

# Search Filters

Supported filters:

Object Type

Creator

Region

Culture

Theme

Motif

Date

Language

Evidence Quality

Review Status

Media Type

Article Type

Multiple filters may be combined.

---

# Search Facets

Facets summarize the knowledge landscape.

Example

```
Kuntilanak

Stories

127

Knowledge Objects

9

Regions

17

Cultures

8

Creators

14

Evidence

94
```

Users immediately understand available knowledge.

---

# Semantic Search

Semantic search uses embeddings stored in Weaviate.

Users may ask:

```
stories similar to rumah tua bandung

ghosts related to water

rituals associated with childbirth

podcasts discussing abandoned hospitals

creatures appearing during rain
```

Results are based on meaning rather than exact keywords.

---

# Knowledge Graph Search

Graph search traverses relationships.

Example

```
Kuntilanak

↓

Appears In

↓

Story

↓

Investigated By

↓

Creator

↓

Visited Region

↓

Related Belief
```

Graph traversal complements semantic search.

---

# AI Discovery Search

AI Discovery interprets user intent and expands exploration.

Example

Query

```
female ghost
```

The platform may suggest:

Kuntilanak

Sundel Bolong

Wewe Gombel

Regional Variants

Stories

Beliefs

Historical References

The AI should never fabricate knowledge.

Every recommendation must reference existing knowledge objects.

---

# Search Suggestions

Suggestions include:

Recent Searches

Popular Searches

Trending Knowledge

Seasonal Topics

Related Queries

Knowledge Recommendations

Suggestions evolve with user activity.

---

# Search History

Remember:

Recent queries

Visited entities

Visited stories

Visited regions

Bookmarked knowledge

History remains private to the user.

---

# Transcript Search

Users may search inside transcripts.

Example

```
suara perempuan

jam 3 pagi

bau melati

kursi goyang
```

Results jump directly to the corresponding transcript segment.

---

# Evidence Search

Researchers may search evidence.

Example

```
audio evidence

photo evidence

historical evidence

eyewitness interview

community report
```

Evidence becomes searchable independently.

---

# Relationship Explorer

Every search result exposes:

Related Stories

Related Knowledge

Related Entities

Related Cultures

Related Regions

Related Timeline

Related Sources

Related Creators

Relationship exploration encourages continuous discovery.

---

# Search State

Search state includes:

Current Query

Filters

Sort

Selected Result

Expanded Relationships

Workspace Context

The state is shareable via URL.

---

# Keyboard Experience

```
/

Focus Search

↑↓

Navigate Suggestions

Enter

Open Result

Esc

Close

Cmd+K

Global Search

Ctrl+Shift+F

Advanced Search
```

Search should feel instantaneous.

---

# Empty Results

No search should terminate with:

"No Results Found"

Instead provide:

Related Knowledge

Alternative Spellings

Nearby Concepts

Similar Stories

Suggested Searches

Graph Neighbors

The platform always offers another path.

---

# AI Assistance

AI may:

Summarize results

Cluster similar objects

Explain relationships

Suggest next exploration

Compare concepts

AI never invents unsupported information.

---

# Performance

Target response times:

Autocomplete

<100 ms

Keyword Search

<300 ms

Hybrid Search

<700 ms

Semantic Search

<1000 ms

Graph Expansion

<1000 ms

Perceived speed is essential.

---

# Accessibility

Search must support:

Keyboard navigation

Screen readers

Voice input (future)

High contrast

Reduced motion

Large text

Every interaction must be fully accessible.

---

# Search Analytics

Measure:

Search Success Rate

Search Abandonment

Refinement Rate

Relationship Click Rate

Knowledge Discovery Rate

Average Exploration Depth

Entity Discovery

Bookmark Rate

Collection Creation

The goal is not maximizing searches.

The goal is maximizing understanding.

---

# Future Capabilities

Planned enhancements include:

Cross-language Search

Image Search

Audio Search

Visual Similarity Search

Geographic Search

Timeline Search

Voice Search

Knowledge Gap Detection

Research Recommendations

Collaborative Search

The architecture must accommodate these without redesign.

---

# Guiding Principle

Search is not a tool for finding pages.

Search is the primary interface for exploring the living knowledge of Indonesian mystery culture.

Every search should leave the user knowing more than they originally intended to discover.
