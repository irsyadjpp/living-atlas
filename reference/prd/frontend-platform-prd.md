# Executive Summary

## Document Information

| Field        | Value                                                    |
| ------------ | -------------------------------------------------------- |
| Document     | Frontend Platform PRD                                    |
| Product      | The Living Atlas of Indonesian Mystery Culture           |
| Version      | 1.0                                                      |
| Status       | Draft                                                    |
| Owner        | Frontend Engineering                                     |
| Stakeholders | Product, Engineering, Design, AI Platform, Research Team |
| Last Updated | June 2026                                                |

---

# Purpose

This document defines the architectural, technical, and user experience foundation for every frontend application within **The Living Atlas of Indonesian Mystery Culture**.

Rather than specifying the implementation details of an individual application, this document establishes the common principles, standards, and architectural contracts shared across all frontend products in the ecosystem.

The Frontend Platform exists to ensure that every application delivers a consistent, accessible, performant, and maintainable user experience while remaining scalable as the platform evolves.

This document serves as the primary engineering reference for frontend architecture, design consistency, navigation patterns, shared components, application behavior, and integration with backend services and AI-powered capabilities.

---

# Background

Indonesia possesses one of the richest collections of folklore, oral traditions, supernatural beliefs, rituals, myths, and local mystery narratives in the world.

However, most of this knowledge exists in fragmented forms:

* YouTube investigations
* Horror podcasts
* Personal experiences
* Local community stories
* Oral traditions
* Books
* Historical documents
* Research papers
* Interviews
* Documentary videos

These sources are:

* difficult to search,
* difficult to compare,
* poorly interconnected,
* rarely preserved in structured formats,
* and often disappear over time.

The Living Atlas of Indonesian Mystery Culture aims to preserve these narratives by transforming them into structured cultural knowledge while preserving provenance, uncertainty, and regional diversity.

The frontend platform becomes the primary medium through which this knowledge is explored, understood, researched, and experienced.

Unlike conventional content platforms, users are not only reading articles—they are exploring relationships between stories, places, beliefs, rituals, entities, historical events, and cultural traditions.

The frontend therefore functions not merely as a website, but as an interactive knowledge exploration platform.

---

# Vision

The frontend should become the world's most immersive digital interface for exploring Indonesian mystery culture.

Rather than presenting isolated articles or videos, it should provide an experience where users naturally move between:

* Stories
* Knowledge
* Places
* Cultural traditions
* Historical events
* Supernatural entities
* Rituals
* Themes
* Motifs
* Researchers
* Creators
* Evidence
* Relationships

Every interaction should encourage exploration rather than simple navigation.

The experience should resemble exploring an evolving cultural atlas rather than browsing a traditional content website.

---

# Product Philosophy

The platform is built around five core principles.

## 1. Knowledge Before Content

The platform is not designed to maximize page views.

Instead, it is designed to maximize understanding.

Articles are one representation of knowledge.

The underlying knowledge graph is the true product.

Every interface should expose meaningful relationships instead of isolated pages.

---

## 2. Exploration Before Navigation

Traditional websites encourage users to navigate menus.

The Living Atlas encourages discovery.

Users should constantly encounter:

* related stories,
* connected entities,
* nearby traditions,
* alternative interpretations,
* historical context,
* similar investigations,
* regional variations.

Exploration should feel organic.

---

## 3. Evidence Before Opinion

Every knowledge object presented to users must be traceable.

The frontend should always communicate:

* where information originates,
* how confident the platform is,
* whether information has been reviewed,
* whether contradictions exist.

The system never claims certainty when uncertainty exists.

---

## 4. Culture Before Entertainment

Although the platform contains horror-related content, it is fundamentally a cultural preservation project.

The interface should communicate respect toward:

* traditions,
* local beliefs,
* oral history,
* communities,
* regional identity.

The visual language should avoid sensationalism.

---

## 5. Calm Technology

The platform should not compete for user attention.

There should be:

* no unnecessary animations,
* no aggressive notifications,
* no distracting advertisements,
* no infinite scrolling addiction patterns,
* no clickbait.

The interface should encourage focused exploration.

---

# Product Scope

The Frontend Platform provides the foundation for multiple applications.

Current applications include:

## Web Atlas

Public-facing experience.

Supports:

* Readers
* Students
* Creators
* Journalists
* Researchers
* General public

---

## Web Admin

Editorial workspace.

Supports:

* Editors
* Moderators
* Reviewers
* Knowledge Curators
* Administrators

---

## Web Research

Professional research workspace.

Supports:

* Anthropologists
* Historians
* Universities
* Documentary Teams
* Production Houses
* Cultural Researchers

---

## Future Applications

Future products may include:

* Mobile Applications
* Writer Studio
* Research API Portal
* Educational Portal
* Museum Kiosk Interface
* Interactive Exhibition Displays

All future applications must follow the architectural standards defined in this document.

---

# Platform Objectives

The frontend platform aims to achieve the following objectives.

## Unified Experience

Every application should feel like part of a single ecosystem.

Users should never feel they are switching between separate products.

---

## Shared Design Language

All applications must share:

* typography,
* spacing,
* iconography,
* colors,
* motion,
* interaction patterns,
* accessibility behaviors.

Consistency reduces learning effort and improves maintainability.

---

## Shared Component Architecture

Components should be reusable across applications.

Examples include:

* Entity Cards
* Story Cards
* Timeline Components
* Graph Visualizations
* Maps
* Search Components
* Knowledge Panels
* Citation Blocks
* Evidence References
* Review Badges
* Relationship Views

A single implementation should serve all frontend applications.

---

## Scalability

The platform must remain maintainable as new features and products are introduced.

Adding a new frontend application should primarily involve composition rather than duplication.

---

## Accessibility

Knowledge should be accessible to the widest possible audience.

The platform must comply with modern accessibility standards and remain usable regardless of device, input method, or user ability.

Accessibility is treated as a core requirement rather than an enhancement.

---

## Performance

Exploration should feel immediate.

Users should not experience noticeable delays when navigating between:

* stories,
* entities,
* graph views,
* articles,
* knowledge pages.

Performance should remain consistent even as the knowledge base grows significantly.

---

# Relationship with Backend Platform

The frontend platform does not own business rules.

Business logic resides within backend services.

The frontend is responsible for:

* presentation,
* interaction,
* workflow orchestration,
* client-side state,
* offline experience,
* rendering,
* visualization.

Business validation, authorization, and persistence remain backend responsibilities.

---

# Relationship with AI Platform

The frontend never communicates directly with AI workers.

All AI interactions occur through backend services.

The frontend submits user requests to backend APIs.

Backend services publish events to Redpanda.

AI workers process those events asynchronously.

The frontend observes progress through backend APIs and real-time notifications.

This architecture ensures:

* security,
* loose coupling,
* provider independence,
* scalability,
* auditability.

---

# Design Inspiration

The user experience draws inspiration from products that prioritize clarity, focus, and exploration.

Key influences include:

* Apple Human Interface Guidelines (clarity, hierarchy, restraint)
* Notion (structured information architecture)
* Arc Browser (contextual navigation)
* Linear (speed and consistency)
* Obsidian (knowledge linking)
* Wikipedia (interconnected knowledge)
* Google Arts & Culture (immersive cultural exploration)

The goal is not to imitate these products visually, but to adopt the principles that make complex information approachable.

---

# Success Definition

The success of the frontend platform is not measured solely by traffic or engagement metrics.

Success is achieved when users can:

* understand complex cultural relationships,
* discover previously unknown connections,
* trust the provenance of information,
* navigate effortlessly across interconnected knowledge,
* transition naturally between narrative and structured data,
* conduct meaningful research,
* and contribute to the preservation of Indonesian cultural heritage.

Ultimately, the frontend should feel less like a conventional website and more like a living, evolving atlas—one that invites curiosity, supports rigorous research, and preserves cultural knowledge for future generations.

---

# Vision

## Vision Statement

**The Living Atlas of Indonesian Mystery Culture** is not intended to become another horror website, article portal, or video index.

Its vision is to become **the world's most comprehensive digital atlas of Indonesian mystery culture**, where stories, folklore, traditions, beliefs, historical narratives, places, rituals, supernatural entities, and cultural interpretations are interconnected into a living body of knowledge.

The frontend is the primary medium through which this knowledge becomes understandable, explorable, and meaningful for every type of user.

The experience should encourage curiosity, critical thinking, cultural appreciation, and long-term learning rather than passive content consumption.

---

# Long-Term Vision

The frontend should evolve through several stages.

## Phase 1 — Reading Platform

Users primarily consume:

* Narrative Articles
* Knowledge Articles
* News Articles
* Story Pages

The experience resembles a modern editorial website.

Primary objective:

Make mystery culture easy to read.

---

## Phase 2 — Knowledge Explorer

Users begin exploring relationships.

Examples:

Story

↓

Entity

↓

Tradition

↓

Region

↓

Historical Event

↓

Another Story

Knowledge becomes interconnected.

Users no longer navigate pages.

They navigate knowledge.

---

## Phase 3 — Living Atlas

The platform becomes an interactive atlas.

Users can explore:

* Regions
* Beliefs
* Rituals
* Historical timelines
* Cultural evolution
* Story lineage
* Creator relationships

The homepage itself becomes an exploration experience.

---

## Phase 4 — Cultural Intelligence Platform

The frontend evolves into a research-grade workspace.

Capabilities include:

* Comparative analysis
* Cultural similarity exploration
* Timeline comparison
* Entity evolution
* Folklore migration
* Regional interpretation comparison

This stage serves:

* Universities
* Researchers
* Production Houses
* Documentary Teams
* Museums

---

# Experience Vision

The experience should feel like entering a museum rather than browsing a news website.

Users should naturally ask:

> "What else is related?"

instead of

> "What should I read next?"

The interface should reward curiosity.

Every page should contain meaningful paths to continue exploration.

---

# Product Personality

The frontend should embody the following personality traits.

## Calm

No visual noise.

No aggressive animations.

No unnecessary popups.

No distracting advertisements.

The interface should encourage focus.

---

## Intelligent

The system understands relationships.

Instead of simply listing related articles, it explains why they are related.

Example:

"This ritual also appears in three other investigations."

"This belief originated from the same cultural region."

"This location appears in multiple folklore traditions."

---

## Respectful

Mystery culture is treated as cultural heritage.

The interface avoids:

* sensationalism,
* fear marketing,
* exaggerated horror aesthetics.

Respect toward communities is more important than entertainment.

---

## Curious

The interface continuously encourages exploration.

Instead of ending a story, it opens new questions.

Examples:

* Similar beliefs
* Alternative interpretations
* Regional differences
* Historical influences
* Related entities

---

## Trustworthy

Every important statement should be traceable.

Users should know:

* where information originated,
* whether AI participated,
* whether editors verified it,
* whether contradictory evidence exists.

Trust is built through transparency.

---

# Design Vision

The frontend should embody "Invisible Complexity."

Internally, the platform may contain:

* millions of entities,
* hundreds of millions of relationships,
* multiple AI pipelines,
* several databases,
* knowledge graphs,
* vector search,
* editorial workflows.

Users should never feel this complexity.

The interface should feel:

Simple.

Predictable.

Elegant.

Fast.

---

# User Experience Vision

The experience should support three levels of exploration.

## Level 1 — Reading

The user simply wants to enjoy a story.

The interface should disappear.

Reading should become immersive.

---

## Level 2 — Learning

The user wants to understand.

The interface gradually introduces:

* entities,
* traditions,
* evidence,
* historical context.

Knowledge appears naturally.

---

## Level 3 — Research

The user wants to investigate.

The interface exposes advanced tools.

Examples:

* Graph visualization
* Filters
* Timelines
* Source comparison
* Evidence explorer
* Relationship explorer

Complexity is progressively disclosed.

---

# Product Principles

The frontend should satisfy the following principles.

## Stories are Entry Points

Stories attract users.

Knowledge retains users.

Research empowers users.

Stories should never become isolated pages.

---

## Knowledge is Primary

Articles are views.

Stories are views.

Maps are views.

Graphs are views.

Everything ultimately represents the same underlying knowledge.

---

## Relationships are First-Class Citizens

Relationships deserve the same importance as entities.

Example:

Instead of only displaying:

Kuntilanak

Display:

Kuntilanak

↓

Appears In

↓

Story

↓

Related Belief

↓

Ritual

↓

Region

↓

Historical Record

The relationship itself carries meaning.

---

## Exploration Never Ends

Every page should answer two questions:

"What is this?"

"What should I explore next?"

Users should never reach a dead end.

---

## Context Before Detail

Before showing detailed information, users should understand context.

Example:

Before displaying:

A supernatural entity

Show:

Region

↓

Culture

↓

Belief System

↓

Historical Context

↓

Entity

Understanding improves interpretation.

---

## Narrative and Knowledge Coexist

The platform maintains two complementary perspectives.

Narrative View

Designed for immersion.

Knowledge View

Designed for understanding.

Users should switch between these seamlessly.

---

## AI Should Feel Invisible

AI assists users.

AI should never dominate the interface.

Users interact with:

Knowledge.

Not AI.

The platform avoids chatbot-centric experiences.

Instead, AI enhances:

* Search
* Recommendations
* Connections
* Summaries
* Discovery

without constantly reminding users that AI is involved.

---

## Cultural Diversity is Preserved

Different regions may describe the same phenomenon differently.

The frontend should preserve these variations rather than forcing a single interpretation.

Contradictions are valuable.

Regional perspectives are valuable.

Minority traditions are valuable.

The platform documents differences instead of eliminating them.

---

## Future Vision

Ten years from now, the frontend should still feel modern because its foundation is built around timeless principles:

* clarity,
* knowledge,
* relationships,
* provenance,
* accessibility,
* exploration.

Technologies will change.

Frameworks will change.

Design trends will change.

But the experience of exploring human culture through interconnected knowledge should remain relevant for decades.

---

# Product Goals

The Frontend Platform exists to transform a complex cultural knowledge platform into an intuitive, accessible, and immersive experience.

Unlike conventional content platforms, success is not measured solely by page views or session duration.

Success is measured by how effectively users discover, understand, connect, validate, and preserve cultural knowledge.

The following goals define the long-term direction of the frontend platform.

---

# Goal 1 — Make Complex Knowledge Feel Simple

The Living Atlas contains multiple knowledge domains:

* Stories
* Articles
* Knowledge Objects
* Claims
* Evidence
* Regions
* Traditions
* Rituals
* Beliefs
* Historical Events
* Creatures
* Spirits
* Researchers
* Creators
* Relationships

Most users should never feel overwhelmed by this complexity.

The interface should progressively reveal information.

Simple questions should have simple interfaces.

Complex research should have powerful tools.

Complexity must remain optional.

---

## Success Indicators

Users can:

* Understand a story within seconds.
* Discover related knowledge naturally.
* Explore without reading documentation.
* Navigate intuitively.
* Learn while browsing.

---

# Goal 2 — Transform Passive Reading into Exploration

Traditional content platforms end when an article ends.

The Living Atlas begins when an article ends.

Every page should encourage exploration.

Example:

Story

↓

Ghost Entity

↓

Related Ritual

↓

Historical Record

↓

Regional Difference

↓

Research Collection

↓

Timeline

↓

Another Story

The platform should continuously expose meaningful connections.

---

## Design Principle

Every page answers three questions:

"What am I reading?"

"What is related?"

"Where should I go next?"

---

# Goal 3 — Build Trust Through Transparency

Mystery culture contains:

* folklore
* oral history
* personal experiences
* myths
* historical records
* religious beliefs
* conflicting interpretations

The platform should never present uncertain information as objective fact.

Every important statement should expose:

Evidence

Confidence

Source

Review Status

Contradictions

Users should always understand why something appears on the page.

---

## Trust Indicators

Display:

Verified

AI Generated

Human Reviewed

Multiple Sources

Regional Variant

Historical Interpretation

Research Gap

Unknown

Transparency increases credibility.

---

# Goal 4 — Preserve Cultural Diversity

Indonesia consists of hundreds of cultures.

The same phenomenon may have:

Different names.

Different rituals.

Different interpretations.

Different historical origins.

The frontend must preserve diversity.

It should never collapse different traditions into a single universal truth.

---

Example:

Kuntilanak

West Java

↓

Different interpretation

↓

South Kalimantan

↓

Different belief

↓

North Sumatra

↓

Different ritual

The UI should visualize differences rather than hide them.

---

# Goal 5 — Become the Best Research Interface

Researchers should not need external tools to begin exploration.

The platform should provide:

Relationship navigation

Knowledge filtering

Evidence exploration

Timeline visualization

Regional comparison

Source comparison

Entity comparison

Knowledge lineage

Research begins inside the platform.

---

# Goal 6 — Support Multiple User Journeys

Different users have different expectations.

The frontend should adapt naturally.

---

Reader

Goal:

Enjoy stories.

Needs:

Beautiful reading experience.

Minimal distractions.

---

Researcher

Goal:

Investigate knowledge.

Needs:

Evidence.

Relationships.

Advanced filtering.

Exports.

---

Creator

Goal:

Understand previous investigations.

Needs:

Knowledge graph.

Timeline.

Entity history.

Source relationships.

---

Editor

Goal:

Review AI output.

Needs:

Comparison tools.

Approval workflow.

Evidence viewer.

Confidence indicators.

---

Administrator

Goal:

Maintain platform health.

Needs:

Operational dashboards.

Moderation.

Governance.

Audit logs.

---

# Goal 7 — Encourage Long-Term Learning

The platform should reward returning users.

Examples:

Saved Collections

Bookmarks

Research Workspace

Knowledge History

Recently Explored

Learning Progress

Users gradually build personal knowledge.

---

# Goal 8 — Scale Without Redesign

The frontend architecture should support future growth.

Future capabilities may include:

Museum Mode

Interactive Maps

Educational Mode

Public APIs

Story DNA Explorer

Creator Studio

Adaptation Intelligence

Research Intelligence

The architecture should support these without fundamental redesign.

---

# Goal 9 — Keep AI Invisible

The Living Atlas is not an AI product.

It is a cultural knowledge platform enhanced by AI.

Users should not constantly interact with prompts.

Instead AI quietly improves:

Search

Recommendations

Relationship discovery

Summaries

Classification

Entity linking

Knowledge extraction

The user experiences better knowledge—not more AI.

---

# Goal 10 — Deliver Apple-Level Product Quality

Every interaction should feel intentional.

No accidental layouts.

No inconsistent spacing.

No visual clutter.

No confusing navigation.

The frontend should prioritize:

Clarity

Precision

Consistency

Performance

Craftsmanship

Every screen should feel designed rather than assembled.

---

# Product Success Metrics

The platform measures success using four dimensions.

---

## Knowledge Success

Can users understand the subject?

Metrics:

Knowledge Exploration Rate

Relationship Navigation Rate

Entity Discovery Rate

Evidence Interaction Rate

Collection Creation Rate

---

## User Success

Can users accomplish their goals?

Metrics:

Task Completion

Reading Completion

Research Session Length

Return Visits

Search Success Rate

---

## Product Quality

Does the interface feel reliable?

Metrics:

Performance

Accessibility

Error Rate

Consistency

User Satisfaction

---

## Platform Success

Can the frontend scale?

Metrics:

Component Reuse

Shared Component Coverage

Design Token Adoption

Feature Development Time

Cross-Application Consistency

---

# Non-Goals

The frontend is NOT intended to become:

A social media platform.

A horror news portal.

A streaming platform.

A chatbot interface.

A recommendation feed driven by engagement.

A clickbait website.

An advertising platform.

These may exist as integrations, but they are not core objectives.

---

# Guiding Product Statement

If a design decision increases engagement but reduces understanding, choose understanding.

If a design decision increases page views but weakens cultural authenticity, choose authenticity.

If a design decision simplifies implementation but sacrifices provenance, choose provenance.

If a design decision favors novelty over clarity, choose clarity.

Every decision should reinforce the platform's mission:

**to preserve, connect, and make discoverable the living knowledge of Indonesian mystery culture for generations to come.**

---

# Design Principles

The frontend of **The Living Atlas of Indonesian Mystery Culture** is built upon a set of enduring principles rather than temporary design trends.

These principles guide every decision—from information architecture and interaction design to component implementation and engineering trade-offs.

Every new feature, screen, and interaction must be evaluated against these principles.

If a feature violates multiple principles, the implementation should be reconsidered regardless of technical feasibility.

---

# Principle 1 — Knowledge First

## Philosophy

The platform exists to preserve and communicate knowledge.

Stories, articles, videos, maps, timelines, and graphs are simply different ways of presenting the same underlying knowledge.

Knowledge is the product.

Content is one representation.

---

## Implications

The UI should never isolate content.

Every piece of information should expose its surrounding context.

Example:

Instead of showing only:

```text
Kuntilanak
```

The interface should naturally expose:

```text
Kuntilanak

Appears In
↓

Story

Believed By
↓

Culture

Recorded In
↓

Historical Document

Associated With
↓

Ritual

Located In
↓

Region
```

Knowledge should feel interconnected.

---

## Engineering Rules

Every major page should include:

Related Entities

Related Stories

Related Traditions

Related Articles

Related Regions

Related Claims

Evidence

Timeline

Relationship Explorer

---

# Principle 2 — Progressive Disclosure

## Philosophy

Users should never experience unnecessary complexity.

Simple tasks remain simple.

Complex functionality appears only when needed.

---

Example

A casual reader opens a story.

They should primarily see:

Title

Reading content

Images

Related stories

Nothing more.

---

A researcher opens the same story.

The interface additionally reveals:

Evidence

Transcript

Claim list

Knowledge objects

Timeline

Relationships

Contradictions

Source comparison

The same underlying data supports multiple levels of complexity.

---

## Engineering Rules

Never display advanced controls by default.

Never overwhelm first-time users.

Advanced tools belong behind explicit interaction.

---

# Principle 3 — Context Before Detail

Knowledge without context leads to misunderstanding.

Every object should first explain:

What it is.

Why it matters.

How it relates.

Only afterwards should detailed information appear.

---

Example

Incorrect:

Spirit

↓

Large technical specification

Correct:

Spirit

↓

Summary

↓

Cultural Context

↓

Historical Context

↓

Regional Interpretation

↓

Evidence

↓

Detailed Metadata

---

# Principle 4 — Relationships Are First-Class Objects

Traditional websites prioritize pages.

The Living Atlas prioritizes relationships.

Relationships carry meaning.

Example:

Rather than:

Story A

Related Story B

Display:

Story A

↓

Inspired

↓

Story B

The relationship itself becomes visible.

---

Relationship examples

Appears In

Contradicts

Derived From

Influenced By

Mentioned Together

Shares Motif

Shares Theme

Regional Variant

Ancestor Of

Descendant Of

Historical Evolution

Every relationship should be explorable.

---

# Principle 5 — Provenance Everywhere

Trust begins with transparency.

Every significant knowledge object should answer:

Where did this come from?

Who said this?

Which source supports this?

Has it been reviewed?

Can I verify it?

---

The frontend should expose provenance naturally.

Example

Knowledge Object

↓

Evidence

↓

Transcript Segment

↓

Video

↓

Creator

↓

Publication Date

↓

Source Link

The user should never need to guess.

---

# Principle 6 — Preserve Uncertainty

Many cultural narratives do not have objective answers.

The platform should preserve ambiguity.

Example:

Instead of:

"This spirit originates from West Java."

Display:

Known Regional Interpretations

West Java

Central Java

East Java

Supporting Evidence

Contradicting Evidence

Unknown Origins

The frontend communicates uncertainty honestly.

---

# Principle 7 — Narrative and Knowledge Coexist

There are two valid ways to experience the platform.

Narrative Mode

Immersive.

Designed for reading.

Knowledge Mode

Analytical.

Designed for understanding.

Neither replaces the other.

Users may freely transition between them.

---

Example

Story

↓

Knowledge View

↓

Graph View

↓

Timeline

↓

Story

The transition should feel seamless.

---

# Principle 8 — Exploration Is Continuous

The interface should eliminate dead ends.

Every page should answer:

Where can I continue?

---

Example

Story Page

↓

Related Stories

↓

Entities

↓

Rituals

↓

Timeline

↓

Map

↓

Creator

↓

Research Collections

↓

Knowledge Articles

Users continuously discover.

---

# Principle 9 — Calm Interfaces

The platform intentionally avoids attention-maximizing design.

Avoid:

Infinite scrolling

Auto-playing media

Aggressive notifications

Flashy animations

Overly saturated colors

Large promotional banners

Pop-up interruptions

The interface should create focus.

---

Animation should communicate meaning rather than attract attention.

Examples:

Panel expansion

Relationship highlighting

Map transitions

Timeline progression

Everything else remains subtle.

---

# Principle 10 — Visual Hierarchy Before Decoration

Decoration never replaces structure.

Hierarchy should primarily rely on:

Typography

Spacing

Alignment

Grouping

Contrast

Scale

Color becomes a supporting element.

---

Example

Good hierarchy:

Heading

↓

Section

↓

Paragraph

↓

Evidence

↓

Metadata

Bad hierarchy:

Many colors

Many borders

Many icons

Many shadows

The interface should remain visually quiet.

---

# Principle 11 — Consistency Over Creativity

Creative layouts increase cognitive load.

Users should immediately understand:

Buttons

Cards

Lists

Tables

Dialogs

Navigation

Every interaction should behave consistently across applications.

---

Engineering implication

Shared components must never be duplicated.

Behavior is standardized.

Visual language is standardized.

Interaction is standardized.

---

# Principle 12 — Accessibility Is Fundamental

Accessibility is not an enhancement.

It is part of the definition of done.

The platform must support:

Keyboard navigation

Screen readers

Reduced motion

High contrast

Large text

Color blindness

Touch interaction

Accessibility should be considered from the beginning.

---

# Principle 13 — Performance Feels Like Design

Users perceive speed as quality.

Performance influences trust.

Every interaction should minimize waiting.

Strategies include:

Streaming rendering

Optimistic updates

Prefetching

Skeleton loading

Lazy loading

Virtualization

Caching

Background fetching

Fast interfaces encourage exploration.

---

# Principle 14 — AI Is Invisible

Users interact with knowledge.

Not AI.

AI should improve:

Search

Recommendations

Relationship discovery

Knowledge extraction

Summaries

Entity linking

without constantly exposing prompts or model names.

The frontend avoids chatbot-first experiences.

---

# Principle 15 — Design for Growth

The knowledge graph will continue expanding indefinitely.

The interface must gracefully accommodate:

Millions of entities

Hundreds of millions of relationships

Multiple article types

Future visualization modes

Additional research tools

New cultural domains

No component should assume small datasets.

Pagination, virtualization, filtering, and progressive loading are mandatory considerations.

---

# Principle 16 — Components Are Products

Every reusable component should be treated as a product.

Each component requires:

Clear purpose

API contract

Accessibility support

Loading state

Empty state

Error state

Responsive behavior

Documentation

Examples

Breaking changes must be versioned.

---

# Principle 17 — Frontend as a Knowledge Explorer

The frontend is not merely a presentation layer.

It is an exploratory interface for a living knowledge system.

Every interaction should reinforce the feeling that the user is navigating an interconnected cultural atlas rather than a collection of independent webpages.

Whether the user begins with a story, a ritual, a location, or a historical event, every path should ultimately lead to deeper understanding, broader context, and new discoveries.

---

# Design Decision Checklist

Before implementing any feature, every team should ask:

* Does this increase understanding?
* Does this expose meaningful relationships?
* Does this preserve provenance?
* Does this respect cultural diversity?
* Does this avoid unnecessary complexity?
* Does this improve exploration?
* Is it accessible?
* Is it reusable?
* Is it consistent with the design system?
* Will it still work when the platform contains millions of knowledge objects?

If the answer to multiple questions is "No", the design should be revised before implementation.

These principles are not recommendations—they are the architectural foundation of the entire frontend platform and should guide product, design, and engineering decisions throughout the lifetime of The Living Atlas of Indonesian Mystery Culture.

---

# Frontend Architecture

---

# Purpose

The Frontend Platform is responsible for delivering a unified user experience across all applications within **The Living Atlas of Indonesian Mystery Culture**.

Its responsibility is **presentation, interaction, and client-side orchestration**.

The frontend **does not contain business logic**.

Business rules belong exclusively to Backend Services.

AI processing belongs exclusively to the AI Platform.

The frontend is an intelligent client that visualizes knowledge rather than computes it.

---

# Architectural Philosophy

The frontend architecture follows six fundamental principles.

## Thin Client

Business logic stays in backend services.

Frontend responsibilities:

* Rendering
* User Interaction
* Client State
* Navigation
* Accessibility
* Animation
* Visualization
* Client-side Validation
* Optimistic UI
* Offline Experience (future)

The frontend never becomes a second backend.

---

## API First

Every capability originates from Backend APIs.

Frontend never:

* accesses PostgreSQL
* accesses Neo4j
* accesses Weaviate
* communicates with AI Workers

All communication passes through:

```text
Frontend

↓

Gateway Service

↓

Backend Services
```

This provides:

* security
* consistency
* versioning
* auditability

---

## Component First

Pages are composed from reusable components.

Never build:

```text
Page

↓

Custom UI
```

Instead:

```text
Page

↓

Layouts

↓

Sections

↓

Components

↓

Primitives
```

Every UI element should eventually become reusable.

---

## Knowledge First Rendering

The frontend renders knowledge rather than documents.

Example:

Traditional website

```text
Article

↓

Render HTML
```

Living Atlas

```text
Story

↓

Knowledge Objects

↓

Relationships

↓

Evidence

↓

Timeline

↓

Render Experience
```

Pages become compositions of knowledge.

---

## Progressive Hydration

Not every component should hydrate immediately.

Priority:

Critical

↓

Visible

↓

Interactive

↓

Background

The interface should become usable before every component loads.

---

## Progressive Enhancement

The application should remain useful even when advanced capabilities are unavailable.

Examples:

If Graph Visualization fails:

↓

Fallback

Relationship List

If AI Search unavailable:

↓

Fallback

Traditional Search

Graceful degradation is mandatory.

---

# High-Level Architecture

```text
                 Browser
                     │
                     ▼
          React + Next.js Application
                     │
      ┌──────────────┼───────────────┐
      ▼              ▼               ▼
Presentation     State Layer     Data Layer
      │              │               │
      └──────────────┼───────────────┘
                     ▼
             API Client Package
                     │
                     ▼
            Gateway Service
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
Backend Services          Authentication
                     │
                     ▼
PostgreSQL / Neo4j / Weaviate
```

---

# Application Layers

The frontend is divided into clearly separated layers.

---

## Layer 1

Presentation Layer

Responsibilities:

* UI
* Layout
* Typography
* Components
* Animation
* Accessibility

Contains:

Pages

Components

Icons

Design System

No API calls.

---

## Layer 2

Application Layer

Coordinates user interactions.

Responsibilities:

Navigation

Forms

Commands

Workflow

Dialog orchestration

Optimistic updates

No rendering logic.

No business logic.

---

## Layer 3

State Layer

Stores client state.

Examples:

Current user

Theme

Filters

Search state

Selected entity

Workspace

Collections

Sidebar state

No business rules.

---

## Layer 4

Data Layer

Responsibilities:

API Requests

Caching

Revalidation

Pagination

Infinite loading

Optimistic mutations

Streaming

Error recovery

---

## Layer 5

Infrastructure Layer

Responsibilities:

Analytics

Feature Flags

Logging

Monitoring

Error Reporting

Performance Metrics

---

# Application Composition

Applications are composed from independent feature modules.

Example:

```text
Story

├── Story Header

├── Story Metadata

├── Story Reader

├── Story Timeline

├── Related Stories

├── Related Entities

├── Evidence Panel

├── Knowledge Sidebar

└── Comments (Future)
```

Each module should remain independently testable.

---

# Rendering Strategy

Different pages require different rendering.

---

## Static Rendering

Suitable for:

Homepage

About

Static documentation

SEO landing pages

---

## Server Rendering

Suitable for:

Story Detail

Knowledge Detail

Entity Detail

Article Detail

Reason:

SEO

Fast first paint

Metadata generation

---

## Streaming Rendering

Suitable for:

Large story pages.

Load:

Header

↓

Story

↓

Knowledge

↓

Timeline

↓

Graph

↓

Recommendations

Users should begin reading immediately.

---

## Client Rendering

Suitable for:

Graph Explorer

Research Workspace

Atlas Visualization

Interactive Timeline

AI Discovery

These experiences require rich client interactions.

---

# Data Flow

The frontend follows unidirectional data flow.

```text
User

↓

Interaction

↓

Application Layer

↓

API Client

↓

Gateway

↓

Backend

↓

Response

↓

Cache

↓

UI
```

Never mutate server state directly.

---

# API Communication

All communication occurs through a shared API Client.

Never:

```text
fetch(...)
```

inside components.

Instead:

```text
Component

↓

Application Hook

↓

API Client

↓

Gateway
```

Benefits:

Consistency

Authentication

Retry

Logging

Caching

Error Handling

---

# State Management Philosophy

Different state types require different solutions.

---

## Server State

Owned by backend.

Examples:

Stories

Articles

Knowledge

Graph

Search

Never duplicate permanently.

---

## Client State

Owned by frontend.

Examples:

Theme

Sidebar

Tabs

Sorting

Filters

Dialog

Selections

---

## Session State

Temporary.

Examples:

Current search

Graph position

Zoom

Draft annotation

---

## Persistent State

Stored locally.

Examples:

Bookmarks

Recent Searches

Reading Preferences

Theme

Sidebar width

---

# Routing Philosophy

Routing should reflect knowledge.

Examples:

```text
/story/{slug}

/entity/{slug}

/knowledge/{slug}

/region/{slug}

/creator/{slug}

/culture/{slug}
```

Readable.

Predictable.

Stable.

Avoid exposing implementation details.

---

# Search Architecture

Search is central.

Every search uses a common architecture.

```text
Search Box

↓

Search Context

↓

API

↓

Result Types

↓

Unified Result Renderer
```

Result types:

Stories

Knowledge

Entities

Articles

Creators

Regions

Cultures

Rituals

Themes

Search becomes a platform capability rather than a page-specific feature.

---

# Visualization Architecture

Complex visualizations are isolated.

Modules:

Knowledge Graph

Timeline

Map

Relationship Viewer

Comparison View

Evidence Viewer

Each visualization should function independently.

---

# Error Handling

Errors should be categorized.

Network

Authentication

Authorization

Validation

Unexpected

AI unavailable

Each error has:

Dedicated UI

Recovery action

Logging

Telemetry

Users should always understand:

What happened.

What can be done next.

---

# Performance Strategy

Performance is a product feature.

Mandatory techniques:

Server Components

Streaming

Code Splitting

Lazy Loading

Image Optimization

Virtual Lists

Partial Rendering

Prefetch

Background Fetching

Route-based Bundles

Performance budgets will be enforced during development.

---

# Frontend Boundaries

The frontend must never:

Contain business rules.

Generate knowledge.

Resolve permissions.

Validate domain workflows.

Process AI prompts.

Modify graph projections.

Write directly to databases.

Invoke AI workers.

Its sole responsibility is to present knowledge and facilitate user interaction.

---

# Evolution Strategy

The architecture is intentionally modular.

New products such as:

* Mobile applications
* Museum kiosks
* Educational portals
* Public APIs
* Interactive installations
* AR/VR experiences

should be able to reuse the same design system, API client, shared types, and domain concepts without redesigning the frontend foundation.

The architecture therefore optimizes for **longevity**, **consistency**, and **maintainability**, ensuring that The Living Atlas can evolve for many years while remaining coherent across every user-facing experience.

---

# Monorepo Structure

---

# Purpose

The frontend ecosystem is expected to grow from a single public website into multiple independent applications that share the same design language, domain model, and engineering standards.

The monorepo exists to maximize:

* Code Reuse
* Design Consistency
* Type Safety
* Developer Experience
* Build Efficiency
* Long-Term Maintainability

The goal is **not** to reduce the number of repositories, but to create a single source of truth for every reusable frontend asset.

---

# Monorepo Philosophy

The frontend should behave like a product platform rather than a collection of unrelated applications.

Every application is simply another consumer of the same platform.

Instead of:

```text
Application
    owns
Components
```

We build:

```text
Platform

↓

Shared Components

↓

Shared Features

↓

Applications
```

Applications compose capabilities.

They do not reimplement them.

---

# High-Level Repository Structure

```text
apps/

├── web-atlas/
├── web-admin/
├── web-research/
└── web-studio/ (future)

packages/

├── design-system/
├── ui/
├── api-client/
├── shared-types/
├── shared-hooks/
├── shared-utils/
├── shared-security/
├── shared-config/
├── shared-icons/
├── shared-assets/
├── shared-testing/
└── shared-i18n/
```

---

# Architectural Dependency Rules

Applications may depend on packages.

Packages may depend on other packages.

Packages may never depend on applications.

Correct:

```text
web-atlas

↓

design-system

↓

shared-icons
```

Incorrect:

```text
design-system

↓

web-atlas
```

Applications remain replaceable.

---

# Applications

Every application has a distinct responsibility.

---

## web-atlas

Public-facing application.

Audience:

* Readers
* Students
* Researchers
* Creators
* Journalists
* General Public

Primary capabilities:

* Story Reading
* Knowledge Reading
* Entity Explorer
* Atlas Visualization
* Timeline
* AI Discovery
* Search
* Regional Explorer
* Creator Profiles

---

## web-admin

Editorial workspace.

Audience:

* Editors
* Moderators
* Administrators
* Knowledge Curators

Primary capabilities:

* Review Queue
* Article Editor
* Knowledge Editor
* AI Review
* Publishing
* Workflow
* Prompt Monitoring
* Audit

---

## web-research

Professional workspace.

Audience:

* Universities
* Anthropologists
* Historians
* Production Houses

Primary capabilities:

* Collections
* Annotation
* Graph Workspace
* Timeline Comparison
* Evidence Viewer
* Source Comparison
* Research Export

---

## web-studio (Future)

Creative production workspace.

Audience:

* Novel Writers
* Documentary Teams
* Screenwriters
* Game Writers

Primary capabilities:

* Story Studio
* Narrative Builder
* World Building
* Story DNA
* Creative AI

---

# Package Strategy

Packages are divided into layers.

---

## Foundation Packages

Lowest dependency level.

Examples:

```text
shared-types

shared-utils

shared-config

shared-icons
```

These packages contain no React components.

---

## UI Foundation

Reusable primitives.

```text
ui/

Button

Input

Select

Dialog

Toast

Tabs

Badge

Card

Tooltip

Popover
```

No business knowledge.

---

## Design System

Composes primitives into Atlas-specific components.

Examples:

```text
Story Card

Knowledge Card

Entity Card

Relationship Card

Timeline Card

Evidence Card

Creator Card

Culture Card
```

These understand Living Atlas concepts.

---

## API Layer

```text
api-client
```

Contains:

REST Client

Authentication

Interceptors

Retry

Caching

Serialization

No UI.

---

## Hooks Layer

```text
shared-hooks
```

Examples:

useStory()

useKnowledge()

useEntity()

useSearch()

useAtlas()

useTimeline()

Hooks abstract API details.

---

## Security Layer

Contains:

Permission Guards

Feature Guards

Workspace Guards

Tenant Guards

Authentication Helpers

Applications should never implement authorization manually.

---

## Testing Layer

Shared utilities.

Examples:

Mock API

Fixtures

Test Providers

Accessibility Helpers

Rendering Utilities

---

# Package Dependency Diagram

```text
Applications

↓

Design System

↓

UI Components

↓

Shared Hooks

↓

API Client

↓

Shared Types

↓

Utilities
```

Dependency direction must always point downward.

Circular dependencies are forbidden.

---

# Internal Structure of Applications

Each application follows Feature-Based Architecture.

Example:

```text
web-atlas/

src/

app/

features/

components/

layouts/

providers/

hooks/

lib/

styles/

types/
```

---

# Feature Organization

Example:

```text
features/

story/

entity/

knowledge/

search/

timeline/

atlas/

profile/

bookmark/
```

Each feature owns:

API Hooks

Components

Routes

Types

Utilities

Tests

Documentation

No feature should access another feature's internal implementation.

---

# Component Organization

Components are classified by scope.

---

## Primitive Components

Examples:

Button

Input

Badge

Avatar

Card

Dialog

No business knowledge.

---

## Composite Components

Examples:

StoryCard

KnowledgeCard

TimelineCard

SearchPanel

GraphNode

These combine primitives.

---

## Feature Components

Examples:

StoryReader

KnowledgeExplorer

EntitySidebar

EvidenceViewer

TimelineExplorer

RelationshipViewer

These belong to one feature.

---

## Page Components

Responsible only for layout composition.

Never contain business logic.

---

# Shared Domain Types

Every application must use identical domain models.

Examples:

Story

Article

Entity

KnowledgeObject

Relationship

Timeline

Creator

Culture

Region

Evidence

Claim

Duplicating these interfaces is forbidden.

---

# Configuration Strategy

Environment-specific values belong in configuration packages.

Examples:

API Endpoint

Feature Flags

Analytics Keys

Build Metadata

Never hardcode environment values.

---

# Asset Management

Shared assets include:

Icons

Logos

Illustrations

Maps

Empty State Graphics

Fonts

Applications reference assets rather than duplicating them.

---

# Documentation Strategy

Every reusable package must include:

README

Usage Examples

Public API

Migration Guide

Version History

Design Notes

The package itself should be understandable without opening its source code.

---

# Versioning Strategy

Packages evolve independently.

Breaking changes require:

Version Increment

Migration Notes

Compatibility Review

Deprecation Window

Applications upgrade intentionally rather than automatically.

---

# Engineering Standards

Every package must satisfy:

Unit Tests

Accessibility Tests

Type Safety

Storybook Examples (future)

Performance Review

Lint Rules

Formatting Rules

Documentation Coverage

Code ownership should be explicit.

---

# Future Scalability

The monorepo is expected to support future applications without structural changes.

Potential additions include:

* Mobile (React Native)
* Desktop (Tauri)
* Museum Kiosk
* Digital Exhibition
* Interactive Installation
* Public Widget SDK
* Educational Portal

These applications should consume existing packages rather than creating new foundations.

The monorepo is therefore designed as a **frontend platform**, not merely a source code repository.

It is the long-term engineering foundation that enables every user-facing experience within The Living Atlas ecosystem to evolve consistently while minimizing duplication and maximizing maintainability.

---

# Technology Stack

---

# Purpose

The technology stack defines the engineering foundation for every frontend application within The Living Atlas ecosystem.

Technology choices are made based on the following priorities:

1. Long-term maintainability
2. Developer productivity
3. Performance
4. Accessibility
5. Scalability
6. Type safety
7. Community maturity
8. Ecosystem stability

Technology should remain stable for many years.

Framework trends should never dictate architecture.

---

# Guiding Principles

Technology serves architecture.

Architecture serves the product.

The product serves users.

Therefore:

Never introduce a technology simply because it is popular.

Every dependency must justify its existence.

---

# Core Technology Stack

| Category          | Technology                                       |
| ----------------- | ------------------------------------------------ |
| Language          | TypeScript                                       |
| Runtime           | Node.js LTS                                      |
| Framework         | Next.js 16 (App Router)                          |
| UI                | React 19                                         |
| Styling           | Tailwind CSS 4                                   |
| Component Library | Custom Atlas Design System                       |
| UI Primitives     | Radix UI                                         |
| Icons             | Lucide Icons + Custom Atlas Icons                |
| Forms             | React Hook Form                                  |
| Validation        | Zod                                              |
| Data Fetching     | TanStack Query                                   |
| State Management  | Zustand                                          |
| Tables            | TanStack Table                                   |
| Visualization     | React Flow + Cytoscape.js + D3 (where necessary) |
| Maps              | MapLibre GL                                      |
| Charts            | Apache ECharts                                   |
| Markdown          | MDX                                              |
| Authentication    | JWT + OAuth2/OIDC                                |
| Testing           | Vitest + Playwright                              |
| Linting           | ESLint                                           |
| Formatting        | Prettier                                         |
| Package Manager   | pnpm                                             |
| Build System      | Turborepo                                        |

---

# Why TypeScript

JavaScript is not sufficient for a platform expected to evolve over many years.

TypeScript provides:

* Strong typing
* IDE support
* Refactoring safety
* Better onboarding
* Better documentation
* Reduced runtime errors

Rule:

Every application must compile with strict mode enabled.

```json
{
  "strict": true
}
```

The use of `any` is prohibited unless explicitly justified.

---

# Why Next.js

Next.js provides capabilities essential for this platform.

These include:

* App Router
* React Server Components
* Streaming Rendering
* SEO
* Metadata API
* Route Groups
* Partial Prerendering
* Edge-ready architecture
* Image Optimization

The Living Atlas is content-heavy.

SEO is a primary requirement.

Server rendering significantly improves discoverability.

---

# Why React

React remains the most mature ecosystem for building large knowledge applications.

Reasons:

* Stable ecosystem
* Large community
* Excellent tooling
* Strong TypeScript support
* Flexible architecture
* Long-term viability

The frontend architecture must remain compatible with future React releases.

---

# Styling Strategy

Styling uses Tailwind CSS.

Reason:

Utility-first styling provides:

* consistency
* smaller CSS bundles
* predictable spacing
* easier maintenance

However:

Tailwind should never become the design system.

Tailwind is only an implementation detail.

The Design System defines appearance.

---

# Component Strategy

Radix UI provides:

* Accessibility
* Keyboard support
* Focus management
* ARIA behavior

Atlas Design System provides:

* visual identity
* spacing
* typography
* interaction patterns
* knowledge-specific components

---

# Icons

Primary library:

Lucide

Reasons:

* Open source
* Consistent
* Lightweight
* Tree-shakeable

Atlas-specific concepts receive custom icons.

Examples:

Story

Folklore

Spirit

Ritual

Tradition

Knowledge

Evidence

Relationship

Timeline

---

# Forms

Forms use:

React Hook Form

Validation uses:

Zod

Benefits:

Minimal re-renders

Excellent TypeScript integration

Reusable schemas

Server/client consistency

---

# Data Fetching

The frontend separates:

Server Rendering

and

Client Synchronization.

TanStack Query manages:

Caching

Retry

Background Refresh

Pagination

Mutation

Optimistic Update

Applications must never manually implement caching.

---

# Client State

Zustand stores only client state.

Examples:

Sidebar

Theme

Filters

Workspace

Dialogs

Current Graph Selection

Never store server state inside Zustand.

---

# Server State

Server state belongs to TanStack Query.

Examples:

Stories

Knowledge

Articles

Graph

Search Results

Timeline

This separation prevents synchronization problems.

---

# Visualization Libraries

Different visualizations require different technologies.

Relationship Graph

↓

Cytoscape.js

Interactive Workflow

↓

React Flow

Statistical Charts

↓

Apache ECharts

Custom SVG

↓

D3 (only when required)

No single visualization library should solve every problem.

---

# Maps

MapLibre GL is selected.

Reasons:

Open Source

No vendor lock-in

Offline capable

Vector tiles

Future GIS compatibility

Potential future integrations:

Historical Maps

Custom Atlas Layers

Cultural Regions

Story Density

---

# Markdown

Narrative Articles

Knowledge Articles

Documentation

should all support MDX.

Benefits:

Rich components

Interactive callouts

Embedded knowledge cards

Timeline blocks

Citation blocks

Entity references

---

# Authentication

Frontend authentication relies on Backend Identity Service.

Supported methods:

Email

OAuth

Future SSO

The frontend never validates permissions.

Permissions always originate from backend.

---

# Testing Strategy

Every application requires:

Unit Tests

Component Tests

Integration Tests

End-to-End Tests

Accessibility Tests

Visual Regression Tests (future)

Testing is part of feature completion.

---

# Build System

Package Manager:

pnpm

Reasons:

Workspace support

Fast installation

Disk efficiency

Excellent monorepo support

Repository orchestration:

Turborepo

Benefits:

Incremental builds

Remote cache

Parallel execution

Dependency graph awareness

---

# Performance Requirements

The frontend should target:

First Contentful Paint:

< 1.5s

Largest Contentful Paint:

< 2.5s

Interaction to Next Paint:

< 200ms

CLS:

< 0.1

Bundle budgets should be monitored continuously.

---

# Dependency Governance

Before introducing any dependency, engineers must answer:

* Does this solve a recurring problem?
* Is it actively maintained?
* Is it TypeScript-first?
* Does it support SSR?
* Is it tree-shakeable?
* Is it compatible with React Server Components?
* Is the community mature?
* Can we replace it if necessary?

If the answer to multiple questions is "No", the dependency should not be introduced.

---

# Upgrade Strategy

Dependencies are classified:

Core

React

Next.js

TypeScript

Updated cautiously.

Platform

Tailwind

TanStack

Radix

Updated quarterly.

Utility

Minor libraries

Updated regularly.

Breaking changes require:

Architecture review

Compatibility testing

Migration guide

---

# Future-Proofing

The chosen technology stack should comfortably support:

* Millions of knowledge objects
* Hundreds of thousands of stories
* Rich graph visualizations
* AI-assisted discovery
* Collaborative research
* Mobile applications
* Desktop applications
* Interactive museum installations

without requiring a fundamental rewrite.

Technology decisions should optimize for the next decade, not merely the next release cycle.

---

