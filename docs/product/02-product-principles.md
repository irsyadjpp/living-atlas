# Product Principles

**Document Version:** 1.0  
**Status:** Canonical  
**Owner:** Product Architecture  
**Applies To:** Entire Living Atlas Platform

---

# Introduction

## Purpose of This Document

This document defines the fundamental principles that govern every decision made throughout the lifetime of The Living Atlas.

Unlike feature specifications, implementation documents, or technical designs, these principles are intended to remain stable for many years.

Technologies will evolve.

Programming languages will change.

Artificial intelligence models will improve.

Frameworks will be replaced.

Databases may eventually migrate.

User interfaces will continuously evolve.

The principles contained within this document should remain largely unchanged.

They represent the philosophical foundation of the platform rather than its implementation.

---

## The Constitution of The Living Atlas

This document should be regarded as the constitutional foundation of the entire project.

Every architectural decision, product requirement, editorial workflow, AI pipeline, database schema, user experience, and operational process must ultimately align with the principles defined here.

Whenever documentation appears to conflict, this document has higher authority.

For example:

```
PRD
↓
Frontend Specification
↓
Backend Specification
↓
AI Platform Specification
↓
Database Design
↓
Implementation
```

If implementation contradicts a Product Principle, the implementation should be reconsidered.

Likewise, if a future Product Requirement conflicts with these principles, the requirement itself should be challenged before development begins.

The goal is not rigid compliance for its own sake.

The goal is long-term consistency.

---

## Why Principles Matter

Software projects often fail not because teams lack technical skill, but because decisions become inconsistent over time.

Different engineers optimize for different objectives.

Different product owners prioritize different outcomes.

Artificial intelligence introduces new implementation possibilities.

Business requirements evolve.

Without stable principles, every decision becomes subjective.

Small inconsistencies accumulate until the overall system becomes difficult to understand, maintain, and evolve.

Product principles provide a stable decision-making framework that survives organizational growth, technological change, and increasing system complexity.

---

## Principles Are Not Features

A feature describes **what** the platform should do.

A principle explains **how decisions should be made** when building those features.

For example:

Feature:

```
Support AI-generated articles.
```

Principle:

```
AI Assists.
Humans Decide.
```

The feature may evolve over time.

The principle should remain stable.

---

## Principles Outlive Technology

The Living Atlas intentionally avoids tying its long-term philosophy to any specific technology.

Examples:

Today:

- PostgreSQL
- Neo4j
- Weaviate
- Spring Boot
- Python
- React
- Gemini
- Claude
- OpenAI

Twenty years from now, these technologies may no longer exist.

The platform may adopt entirely different databases, programming languages, AI models, or interaction paradigms.

However, principles such as:

- Knowledge First
- Evidence Before Opinion
- Preserve Context
- Version Everything
- Human + AI Collaboration

should remain equally valid regardless of implementation.

This separation between philosophy and technology is essential for long-term sustainability.

---

## Principles Apply Everywhere

These principles apply equally across all platform layers.

Including:

- Product Strategy
- User Experience
- Design System
- Frontend
- Backend
- AI Platform
- Knowledge Modeling
- Editorial Workflow
- Database Design
- Search
- Knowledge Graph
- Embeddings
- Infrastructure
- Security
- Analytics
- Future Services

No team is exempt.

---

## Long-Term Stability

Changing a Product Principle should be considered an exceptional event.

Unlike product requirements, principles are expected to remain stable for years.

Changes should occur only when:

- the existing principle is fundamentally incorrect;
- two principles are found to be contradictory;
- the platform's mission changes significantly;
- new knowledge demonstrates that the current principle causes systemic harm.

Principles should never change merely because implementation becomes inconvenient.

Implementation exists to serve principles.

Not the opposite.

---

# How To Use This Document

## Intended Audience

This document is written for everyone who contributes to The Living Atlas.

Including:

- Product Managers
- UX Designers
- UI Designers
- Software Architects
- Backend Engineers
- Frontend Engineers
- AI Engineers
- Data Engineers
- Editorial Teams
- Researchers
- QA Engineers
- DevOps Engineers
- Future Contributors

Although different teams will focus on different principles, every contributor should understand the complete document.

---

## When To Read This Document

The document should be consulted whenever significant decisions are made.

Examples include:

Before creating a new feature.

Before changing the database schema.

Before introducing a new AI model.

Before modifying editorial workflows.

Before designing APIs.

Before adding search capabilities.

Before optimizing performance.

Before introducing breaking architectural changes.

Before adopting new technologies.

If uncertainty exists, begin here.

---

## How To Read Individual Principles

Every principle follows the same structure.

```
Name

Statement

Motivation

Why This Matters

Examples

Anti-patterns

Implementation Impact

Related Principles

Decision Checklist
```

Each section serves a specific purpose.

### Statement

Defines the principle in one concise declaration.

### Motivation

Explains why the principle exists.

### Why This Matters

Describes long-term strategic importance.

### Examples

Illustrates behaviors that align with the principle.

### Anti-patterns

Shows common mistakes that violate the principle.

### Implementation Impact

Explains consequences across Product, UX, Backend, AI, Database, and Architecture.

### Related Principles

Links complementary principles.

### Decision Checklist

Provides practical questions for evaluating implementation decisions.

---

## Principles Are Decision Tools

These principles are not intended to be inspirational slogans.

They exist to resolve difficult trade-offs.

Examples:

Should performance be prioritized over provenance?

Should AI publish automatically?

Should conflicting cultural interpretations be merged?

Should old versions be deleted?

Should convenience override transparency?

The correct answer should emerge naturally by applying the relevant principles.

---

## Multiple Principles May Apply

Many decisions involve several principles simultaneously.

Example:

Publishing AI-generated knowledge.

Relevant principles include:

- AI Assists
- Humans Decide
- Evidence Before Opinion
- Version Everything
- Transparency
- Research Grade

Decisions should consider the entire set rather than relying on a single principle in isolation.

---

## Principles Over Preferences

Engineering preferences are valuable.

Product intuition is valuable.

Editorial judgment is valuable.

However, individual preferences should never override established principles without explicit discussion.

The purpose of this document is to minimize subjective decision-making by establishing shared foundations.

---

# Decision Hierarchy

## Why Hierarchy Exists

Not every rule within The Living Atlas has equal authority.

Some decisions are foundational.

Others are implementation details.

A clear hierarchy ensures that lower-level documents cannot accidentally contradict higher-level intent.

---

## Decision Hierarchy

The Living Atlas follows the following decision hierarchy.

```
Vision

↓

Product Principles

↓

Product Requirements

↓

Experience Specifications

↓

Architecture

↓

Domain Model

↓

Workflow Specifications

↓

Backend Specifications

↓

AI Platform Specifications

↓

Database Specifications

↓

API Contracts

↓

Implementation

↓

Operational Configuration
```

Each layer refines the layer above it.

No lower layer may contradict a higher layer.

---

## Practical Example

Vision:

```
Knowledge should remain trustworthy.
```

↓

Principle:

```
Evidence Before Opinion
```

↓

Backend:

```
Every claim references supporting evidence.
```

↓

Database:

```
claim_evidence table.
```

↓

Implementation:

```
Reject publication without evidence.
```

Every implementation decision can therefore be traced back to a stable philosophical foundation.

---

## Conflict Resolution

When two implementation proposals conflict:

Do not begin by comparing technologies.

Instead:

1. Review the Product Vision.
2. Review the Product Principles.
3. Identify applicable principles.
4. Evaluate trade-offs.
5. Select the option that best satisfies the highest-level principles.

Technology is evaluated last.

Mission is evaluated first.

---

## Escalation Rules

If implementation cannot satisfy one or more principles:

1. Reconsider the implementation.
2. Reconsider the architecture.
3. Reconsider the feature design.
4. Escalate to architectural review.

Changing a Product Principle should always be the final option rather than the first.

---

## Living Governance

This hierarchy establishes long-term governance for The Living Atlas.

It ensures that as the platform grows, every feature, service, database, AI workflow, and future technology remains aligned with the same enduring vision and principles.

Consistency is achieved not through rigid control, but through shared understanding.

---

# Knowledge Principles

The Living Atlas is fundamentally a knowledge platform.

Unlike traditional content management systems that organize pages, articles, or media, the primary asset of this platform is structured knowledge.

Every architectural decision, editorial workflow, AI capability, database schema, user interface, and future technology must ultimately strengthen the quality, integrity, and longevity of that knowledge.

Knowledge Principles therefore have the highest priority among all Product Principles.

Whenever another principle appears to conflict with a Knowledge Principle, the Knowledge Principle should generally take precedence unless a deliberate architectural decision explicitly states otherwise.

---

# Principle 1 — Knowledge First

---

## Statement

Knowledge is the primary product of The Living Atlas.

Everything else—including articles, user interfaces, artificial intelligence, APIs, databases, visualizations, and workflows—exists solely to create, preserve, organize, explain, and distribute knowledge.

If a decision improves software but weakens knowledge, it is considered the wrong decision.

Knowledge always comes first.

---

## Motivation

Many digital platforms mistake content for knowledge.

They optimize publishing workflows.

They optimize page views.

They optimize engagement.

They optimize media management.

Eventually the system becomes excellent at managing documents while remaining poor at preserving understanding.

The Living Atlas intentionally rejects this approach.

An article is not the product.

A video is not the product.

A transcript is not the product.

A database record is not the product.

Knowledge is the product.

Everything else is merely a representation of that knowledge.

This distinction fundamentally changes every architectural decision throughout the platform.

---

## Why This Matters

Knowledge has a significantly longer lifespan than software.

User interfaces change.

Frameworks become obsolete.

Programming languages evolve.

Artificial intelligence models improve.

Even databases may eventually be replaced.

Knowledge should survive all of those transitions.

Therefore the platform must always optimize for preserving knowledge rather than preserving implementation.

Every feature should ultimately answer one question:

> Does this increase the quality, accessibility, longevity, or understanding of knowledge?

If the answer is no, the feature should be reconsidered.

---

## Knowledge Before Content

Traditional systems typically organize information like this:

```
Website

↓

Article

↓

Media

↓

Comments
```

The Living Atlas instead organizes information as:

```
Knowledge

↓

Relationships

↓

Evidence

↓

Stories

↓

Articles

↓

User Experience
```

Articles are generated from knowledge.

Knowledge is never generated from articles.

---

## Knowledge Is an Asset

Knowledge should be treated as a permanent organizational asset.

Characteristics include:

* reusable
* searchable
* explainable
* versioned
* interconnected
* evidence-backed
* machine-readable
* human-readable
* technology independent

Every improvement to knowledge increases the value of the entire platform.

---

## Examples

### Good

Creating a canonical entity instead of embedding information directly inside an article.

Adding provenance before publishing knowledge.

Capturing relationships between stories.

Versioning cultural interpretations.

Improving evidence quality.

Normalizing duplicate entities.

Linking folklore across regions.

Preserving conflicting interpretations.

---

### Bad

Publishing articles without canonical knowledge.

Duplicating information across pages.

Embedding factual information directly into HTML.

Deleting previous knowledge versions.

Optimizing UI while reducing provenance.

Treating AI-generated summaries as canonical knowledge.

---

## Anti-patterns

The following behaviors violate this principle.

### Content First

Designing features around articles instead of knowledge.

---

### Engagement First

Publishing simplified information solely to increase traffic.

---

### AI First

Accepting AI-generated output as authoritative.

---

### UI First

Building interfaces before defining the underlying knowledge model.

---

### Database First

Allowing schema limitations to dictate the knowledge model.

---

## Implementation Impact

### Product

Features are evaluated based on their contribution to knowledge quality rather than engagement metrics.

---

### UX

Interfaces expose evidence, provenance, relationships, and historical evolution.

---

### Backend

Business logic revolves around canonical knowledge rather than presentation objects.

---

### AI Platform

AI produces derived knowledge only.

Canonical knowledge remains under editorial governance.

---

### Database

PostgreSQL stores canonical knowledge.

Neo4j projects relationships.

Weaviate projects semantic representations.

---

### Architecture

Services communicate about knowledge, not pages.

Events describe knowledge evolution.

---

## Related Principles

* One Source of Truth
* Graph Native
* Immutable Knowledge
* Version Everything
* Research Grade

---

## Decision Checklist

Before approving a feature ask:

* Does this improve knowledge?
* Does this preserve context?
* Does this improve discoverability?
* Does this strengthen relationships?
* Does this make future understanding easier?

If the answer is mostly "No", the implementation should be redesigned.

---

# Principle 2 — One Source of Truth

---

## Statement

Every piece of canonical knowledge shall exist in exactly one authoritative location.

Derived representations may exist in many places.

Canonical truth exists only once.

Duplication of canonical knowledge is considered a design failure.

---

## Motivation

Duplicated knowledge inevitably diverges.

Small inconsistencies become larger over time.

Editors unknowingly update only one copy.

AI systems consume outdated information.

Users receive contradictory answers.

Research becomes unreliable.

The Living Atlas therefore adopts a strict Single Source of Truth philosophy.

There must always be one authoritative representation for every canonical concept.

---

## Canonical Before Derived

Every object belongs to one of two categories.

### Canonical

Authoritative knowledge.

Examples:

* Story
* Entity
* Ritual
* Place
* Person
* Creature
* Theme
* Motif
* Source
* Claim
* Evidence

Canonical objects are editable only through approved workflows.

---

### Derived

Generated from canonical knowledge.

Examples:

* Articles
* AI summaries
* Search indexes
* Neo4j graph
* Weaviate vectors
* Timeline views
* Atlas visualization
* Recommendations
* Reading lists

Derived data may be regenerated at any time.

Canonical data may not.

---

## The Database Rule

The Living Atlas follows one fundamental ownership rule.

```
PostgreSQL

↓

Canonical Knowledge
```

Everything else is projection.

```
Neo4j

↓

Knowledge Relationships
```

```
Weaviate

↓

Semantic Projection
```

```
Articles

↓

Narrative Projection
```

```
Search

↓

Retrieval Projection
```

```
API DTO

↓

Presentation Projection
```

No projection may become authoritative.

---

## Update Flow

Every modification follows the same lifecycle.

```
Editor

↓

Backend

↓

PostgreSQL

↓

Domain Event

↓

Queue

↓

Projection

↓

Neo4j

↓

Weaviate

↓

Search

↓

Frontend
```

The direction never reverses.

Neo4j never updates PostgreSQL.

Vectors never update canonical knowledge.

Generated articles never overwrite stories.

This guarantees consistency across the platform.

---

## Examples

### Good

Updating a Story once.

Publishing events.

Rebuilding graph projection.

Regenerating embeddings.

Refreshing search indexes.

Recreating AI articles.

---

### Bad

Editing Neo4j directly.

Editing vector metadata.

Allowing frontend to update graph nodes.

Treating search indexes as primary storage.

Updating generated articles without changing canonical knowledge.

---

## Anti-patterns

### Multiple Truths

Different databases containing conflicting canonical values.

---

### Hidden State

Business logic existing only inside projections.

---

### Manual Projection Edits

Developers fixing Neo4j data directly.

---

### AI Overrides

LLM-generated information replacing canonical knowledge without editorial approval.

---

## Implementation Impact

### Product

Editors always edit canonical knowledge.

---

### Backend

Every aggregate owns exactly one canonical representation.

---

### AI Platform

AI reads canonical knowledge.

AI never owns canonical knowledge.

---

### Database

PostgreSQL is authoritative.

Neo4j is disposable.

Weaviate is disposable.

Search indexes are disposable.

---

### Architecture

Every downstream system must be rebuildable solely from PostgreSQL plus immutable events.

---

## Related Principles

* Knowledge First
* Immutable Knowledge
* Version Everything
* Graph Native
* AI Assists

---

## Decision Checklist

Before introducing new storage ask:

* Does this create another source of truth?
* Can this data be regenerated?
* Can it be safely deleted and rebuilt?
* Who owns this data?
* Where is the canonical representation?

If ownership cannot be clearly identified, the design should be rejected.

---

# Principle 3 — Graph Native

---

## Statement

Knowledge does not exist in isolation.

Every piece of knowledge derives meaning from its relationships with other knowledge.

The Living Atlas therefore models knowledge as a connected graph rather than a collection of independent documents.

Relationships are first-class citizens.

---

## Motivation

Traditional content platforms organize information around documents.

Examples include:

- articles
- pages
- blog posts
- media files

Relationships are usually represented by hyperlinks, tags, or categories.

These mechanisms are useful for navigation but insufficient for representing knowledge.

Knowledge itself is inherently relational.

A story belongs to multiple cultures.

A ritual appears across multiple regions.

A creature exists in different folklore traditions.

A historical event influences later narratives.

An author documents multiple stories.

Every entity participates in a much larger network.

The graph is therefore the natural representation of knowledge.

---

## Knowledge Before Documents

The Living Atlas does not model articles.

It models relationships.

For example:

Story

↓

Character

↓

Location

↓

Historical Event

↓

Belief

↓

Source

↓

Research Note

↓

Article

The article is merely one possible representation.

The relationships are the knowledge.

---

## Relationships Are First-Class

Relationships must be treated with the same importance as entities.

Examples include:

- appears in
- inspired by
- contradicts
- documents
- translated from
- originated in
- influenced
- references
- derived from
- located within
- practiced during
- recorded by

Relationships possess their own metadata.

Including:

- provenance
- confidence
- temporal validity
- editorial review
- evidence
- version history

Relationships are never "just foreign keys."

---

## Graph Thinking

Every feature should begin by asking:

"What relationships exist?"

instead of

"What page should contain this information?"

This changes how engineers design APIs.

It changes how AI extracts knowledge.

It changes how users discover information.

It changes how databases evolve.

---

## Neo4j Is Not The Principle

Graph Native does **not** mean Neo4j is the source of truth.

Neo4j is only one implementation.

The principle remains valid even if Neo4j is replaced in the future.

The graph exists conceptually.

Technology implements it.

---

## Examples

### Good

Linking stories across regions.

Representing conflicting interpretations.

Modeling ritual evolution.

Connecting creators to evidence.

Discovering indirect relationships.

Visualizing historical influence.

---

### Bad

Duplicating information across pages.

Embedding relationships inside article text.

Using tags instead of semantic relationships.

Treating hyperlinks as knowledge.

Ignoring provenance of relationships.

---

## Anti-patterns

- Document-centric architecture.
- Category-first thinking.
- Flat taxonomies.
- Relationship duplication.
- Hidden graph logic inside application code.

---

## Implementation Impact

### Product

Features emphasize exploration instead of navigation.

### Frontend

Graph visualization becomes a natural interface.

### Backend

Relationships become domain objects.

### Database

PostgreSQL stores canonical relationships.

Neo4j projects them.

### AI Platform

Entity extraction includes relationship extraction.

### Architecture

Every domain evolves as a graph.

---

## Related Principles

- Knowledge First
- One Source of Truth
- Immutable Knowledge
- Version Everything

---

## Decision Checklist

Before implementing any feature ask:

- Does this introduce meaningful relationships?
- Can relationships be queried independently?
- Can relationships evolve?
- Are relationships explainable?
- Are relationships supported by evidence?

---

# Editorial Principles

Knowledge has little value if its origin, reliability, and editorial process cannot be understood.

The Living Atlas is not merely a publishing platform.

It is a knowledge platform whose credibility depends on transparent editorial practices.

Editorial Principles define how knowledge is collected, evaluated, verified, revised, and published.

Unlike social media platforms where popularity determines visibility, or traditional content platforms where authorship alone establishes authority, The Living Atlas prioritizes evidence, provenance, explainability, and editorial accountability.

Every published knowledge object should answer three fundamental questions:

* Why should this information be trusted?
* Where did this information come from?
* How did this information become part of the platform?

These principles ensure that trust is earned through transparent processes rather than assumed authority.

---

# Principle 6 — Evidence Before Opinion

---

## Statement

Every published knowledge claim must be supported by identifiable evidence.

Interpretation is valuable.

Opinion is valuable.

Hypothesis is valuable.

However, they must never be presented as established knowledge without clearly distinguishing their evidentiary basis.

Evidence always precedes interpretation.

---

## Motivation

Culture is inherently interpretative.

Different regions preserve different traditions.

Researchers often disagree.

Historical records may conflict.

Eyewitness accounts may contradict each other.

Rather than forcing a single authoritative narrative, The Living Atlas preserves evidence first, allowing multiple interpretations to coexist when appropriate.

Readers should be able to examine the supporting material and understand how conclusions were reached.

The platform therefore values evidence over certainty.

---

## Evidence Is Broader Than Scientific Proof

Evidence within The Living Atlas includes multiple forms.

Examples include:

Primary Sources

* historical manuscripts
* archival documents
* inscriptions
* official records

Oral Tradition

* interviews
* community elders
* local storytellers
* recorded testimonies

Academic Sources

* journals
* books
* theses
* conference papers

Media Sources

* documentaries
* recorded interviews
* verified reporting

Field Research

* photographs
* observations
* site documentation
* expedition notes

Editorial Analysis

* comparative analysis
* source synthesis
* historical comparison

Each type carries different strengths and limitations.

The platform records provenance rather than assigning universal superiority.

---

## Claims Require Evidence

Every canonical claim should reference one or more supporting evidence objects.

For example:

Claim

"The ritual originated during the late colonial period."

↓

Supporting Evidence

* Academic Paper A
* Historical Archive B
* Oral Interview C

Readers should always be able to navigate from conclusions back to supporting material.

---

## Interpretation Must Remain Explicit

The platform distinguishes between:

Observed Fact

Interpretation

Speculation

Hypothesis

Community Belief

Legend

Myth

Editorial Conclusion

These categories must never be silently merged.

The reader deserves to understand which statements describe observable evidence and which represent interpretation.

---

## AI Does Not Produce Evidence

Artificial Intelligence can:

* summarize
* classify
* compare
* organize
* infer relationships
* identify patterns

AI cannot create evidence.

Generated text is never considered evidence by itself.

Every AI-generated statement must ultimately trace back to evidence stored within the platform.

---

## Examples

### Good

Publishing multiple interpretations alongside their supporting evidence.

Recording confidence levels.

Separating folklore from historical documentation.

Showing conflicting academic opinions.

Referencing interview transcripts.

Linking every claim to source material.

---

### Bad

Publishing unsupported factual statements.

Removing contradictory evidence.

Allowing AI-generated summaries to become canonical.

Presenting speculation as historical fact.

Quoting anonymous internet sources without provenance.

---

## Anti-patterns

The following behaviors violate this principle.

### Citation Without Verification

Listing references that have not actually been reviewed.

---

### Opinion Presented as Fact

Editorial conclusions lacking supporting evidence.

---

### Evidence Laundering

Repeating AI-generated statements until they appear authoritative.

---

### Selective Evidence

Ignoring contradictory material to strengthen a preferred narrative.

---

### Popularity Bias

Assuming widely repeated stories are automatically accurate.

---

## Implementation Impact

### Product

Editorial workflows require evidence before publication.

---

### Backend

Every Claim references Evidence through explicit relationships.

---

### Database

Evidence exists as canonical domain objects.

Claims and Evidence are independently versioned.

---

### AI Platform

Extraction pipelines preserve provenance.

Summaries inherit source references.

Generated content stores traceability metadata.

---

### Frontend

Readers can inspect evidence directly from every knowledge object.

Confidence indicators and provenance remain visible.

---

### Search

Evidence becomes searchable independently from articles.

Researchers can search for evidence rather than only narratives.

---

## Related Principles

* Knowledge First
* One Source of Truth
* Transparency
* Explainability
* Research Grade
* Human + AI Collaboration

---

## Decision Checklist

Before publishing any knowledge ask:

* What evidence supports this claim?
* Can readers inspect the evidence?
* Is interpretation clearly separated from observation?
* Are contradictory sources represented?
* Can the conclusion be independently verified?

If these questions cannot be answered, publication should be delayed.

---

# Principle 7 — Transparency

---

## Statement

Users should never be asked to trust the platform blindly.

Every significant piece of knowledge should be accompanied by sufficient context to understand where it came from, how it was produced, who reviewed it, and why it should be considered trustworthy.

Transparency is the foundation of credibility.

---

## Motivation

Many knowledge systems expose conclusions while hiding the process that produced them.

Readers are expected to accept information without understanding:

* its origin,
* its editorial history,
* its confidence,
* its limitations,
* or its evolution.

This creates unnecessary dependence on institutional authority.

The Living Atlas adopts a different philosophy.

Rather than asking readers to trust us, the platform should provide enough information for readers to build informed trust themselves.

Trust is earned through visibility, not obscurity.

---

## Transparency Is Not Information Overload

Transparency does not require displaying every technical detail by default.

Instead, information should be progressively disclosed.

Casual readers may only need:

* summary,
* provenance,
* confidence.

Researchers may inspect:

* evidence,
* revisions,
* editorial discussions,
* AI outputs,
* workflow history,
* relationship changes.

Transparency means the information is available, not necessarily visible all at once.

---

## What Must Be Transparent

Every canonical knowledge object should expose, either directly or through progressive disclosure:

### Provenance

Where did this information originate?

---

### Evidence

What supports this claim?

---

### Editorial History

Who reviewed it?

When?

Why?

---

### Version History

How has the knowledge evolved?

---

### Confidence

How certain is the current understanding?

---

### AI Participation

Which parts involved AI?

Which model?

Which prompt version?

Was the output modified by editors?

---

### Relationships

How is this knowledge connected to other knowledge?

---

### Limitations

What remains uncertain?

What evidence is missing?

Where do disagreements exist?

---

## Transparency Builds Trust

Transparency acknowledges uncertainty rather than hiding it.

Examples include:

"We have limited evidence."

"Researchers disagree."

"This interpretation is widely accepted but contested."

"This relationship has medium confidence."

"This summary was initially generated by AI and subsequently reviewed by editors."

Such statements increase credibility because they accurately represent the state of knowledge.

---

## Examples

### Good

Displaying provenance.

Showing editorial history.

Publishing confidence scores.

Providing AI disclosure.

Exposing version history.

Recording reviewer comments.

Allowing readers to inspect evidence.

---

### Bad

Publishing anonymous content.

Hiding AI involvement.

Removing historical revisions.

Suppressing conflicting interpretations.

Presenting uncertain knowledge as definitive.

---

## Anti-patterns

### Black Box Knowledge

Readers cannot determine where information originated.

---

### Hidden AI

AI-generated content is indistinguishable from human-authored work.

---

### Invisible Editorial Decisions

Review actions are not recorded.

---

### Silent Corrections

Knowledge changes without visible history.

---

### Confidence Concealment

The platform implies certainty where uncertainty exists.

---

## Implementation Impact

### Product

Editorial transparency becomes a core product capability rather than an optional feature.

---

### Frontend

Every knowledge page provides access to provenance, evidence, confidence, version history, and editorial metadata through progressive disclosure.

---

### Backend

All editorial actions are auditable.

Every workflow transition is recorded.

---

### Database

Version history, provenance, workflow events, reviewer identities, and AI execution metadata are preserved as first-class records.

---

### AI Platform

Every generated artifact records:

* model,
* prompt version,
* execution identifier,
* source documents,
* confidence,
* processing timestamp.

---

### Architecture

Transparency is designed into the platform rather than added later through logging or documentation.

---

## Related Principles

* Evidence Before Opinion
* Explainability
* Version Everything
* Immutable Knowledge
* Human + AI Collaboration

---

## Decision Checklist

Before releasing any feature ask:

* Can users understand where this knowledge originated?
* Can they inspect supporting evidence?
* Can they determine whether AI participated?
* Can they view previous versions?
* Can they understand the level of confidence?
* Are important uncertainties clearly communicated?

If users must simply "trust the system," the implementation does not satisfy this principle.

---

# Principle 8 — Explainability

---

## Statement

Every published knowledge object, editorial decision, AI-generated output, and relationship within The Living Atlas should be explainable.

The platform must never ask users to accept conclusions without providing a reasonable path to understand how those conclusions were reached.

Explainability is a fundamental property of trustworthy knowledge.

---

## Motivation

Knowledge without explanation quickly becomes authority without accountability.

Readers may accept conclusions.

Researchers may cite them.

AI systems may consume them.

Yet if nobody can explain why those conclusions exist, trust eventually collapses.

Explainability transforms knowledge from static information into understandable reasoning.

The Living Atlas therefore prioritizes understanding over mere correctness.

---

## Explainability Is Different From Transparency

Transparency answers:

> "What happened?"

Explainability answers:

> "Why did it happen?"

For example:

Transparency

```
Claim approved on 2026-07-01 by Editor A.
```

Explainability

```
Claim approved because three independent sources supported the interpretation while one contradictory source lacked sufficient provenance.
```

Both are necessary.

Transparency exposes history.

Explainability exposes reasoning.

---

## Explainability Across The Entire Platform

Explainability applies to far more than AI.

It includes:

Editorial decisions

Knowledge extraction

Entity resolution

Relationship creation

Conflict resolution

Search ranking

Recommendation generation

Knowledge graph relationships

Confidence calculation

Version changes

Workflow transitions

Whenever the platform performs an action that affects knowledge, users should be able to understand why.

---

## AI Explainability

Artificial Intelligence should never behave as an opaque oracle.

Every AI-generated artifact should retain:

* source documents
* supporting evidence
* prompt version
* model identifier
* extraction pipeline version
* confidence metadata
* review status

Editors should be able to reproduce the reasoning process.

Readers should understand which parts were generated and which were reviewed.

---

## Explainability Does Not Mean Perfect Certainty

Some cultural knowledge cannot be explained with complete certainty.

Instead, the platform should explain uncertainty.

Examples include:

"We currently lack primary historical evidence."

"This conclusion is based primarily on oral tradition."

"Researchers remain divided."

"This relationship is inferred rather than directly documented."

Explaining uncertainty increases trust.

Hiding uncertainty decreases trust.

---

## Examples

### Good

Showing why two entities were merged.

Displaying confidence explanations.

Providing reasoning for editorial rejection.

Explaining relationship confidence.

Showing AI evidence chains.

---

### Bad

Returning search results without ranking rationale.

Creating graph relationships without explanation.

Publishing AI summaries without provenance.

Rejecting submissions without editorial reasoning.

---

## Anti-patterns

### Black Box AI

Models produce conclusions without traceable reasoning.

---

### Hidden Editorial Logic

Approval decisions cannot be explained.

---

### Magic Relationships

Graph edges exist without evidence.

---

### Confidence Without Justification

Scores exist but nobody understands how they were calculated.

---

## Implementation Impact

### Product

Explainability becomes a first-class product capability.

---

### Frontend

Knowledge pages expose reasoning through progressive disclosure.

---

### Backend

Every automated decision records explanatory metadata.

---

### Database

Explanation metadata is versioned and preserved.

---

### AI Platform

All pipelines generate reproducible reasoning artifacts.

---

### Architecture

Explainability is built into workflows rather than added as documentation later.

---

## Related Principles

* Transparency
* Evidence Before Opinion
* Research Grade
* Version Everything
* Human Review

---

## Decision Checklist

Before introducing any automation ask:

* Can users understand why this happened?
* Can editors reproduce the reasoning?
* Can researchers inspect supporting evidence?
* Is uncertainty clearly explained?
* Would future contributors understand this decision five years from now?

If the answer is no, the implementation should be redesigned.

---

# Principle 9 — Research Grade

---

## Statement

Every canonical knowledge object should satisfy standards appropriate for serious research rather than casual content publishing.

The Living Atlas is designed to support researchers, educators, creators, and future AI systems.

Its knowledge must therefore be structured, traceable, and academically defensible.

---

## Motivation

Many platforms prioritize readability.

Others prioritize engagement.

Few prioritize long-term research value.

The Living Atlas intentionally chooses research quality as its editorial baseline.

This does not mean every article must resemble an academic paper.

It means every underlying knowledge object should possess sufficient structure, provenance, and traceability to support rigorous analysis.

Readable content is generated from research-grade knowledge.

Not the opposite.

---

## Characteristics Of Research Grade Knowledge

Research-grade knowledge should possess:

* identifiable provenance
* explicit evidence
* stable identifiers
* canonical entities
* relationship metadata
* confidence assessment
* editorial history
* version history
* reproducibility
* citation capability

Knowledge lacking these characteristics may still be valuable, but should not become canonical until editorial review is complete.

---

## Research Before Narrative

The platform distinguishes between:

Narrative Layer

Readable for general audiences.

Knowledge Layer

Structured for researchers.

Evidence Layer

Primary supporting material.

This layered architecture allows casual readers to enjoy accessible content while researchers inspect deeper levels.

---

## AI Requires Research Grade Data

Future AI systems will increasingly rely on structured knowledge rather than isolated documents.

Research-grade knowledge therefore benefits both humans and machines.

Structured evidence improves:

semantic search,

knowledge graph quality,

relationship extraction,

retrieval-augmented generation,

future model evaluation,

and long-term preservation.

---

## Examples

### Good

Stable entity identifiers.

Evidence-backed claims.

Structured relationships.

Citable knowledge objects.

Explicit confidence levels.

---

### Bad

Anonymous facts.

Unstructured summaries.

Broken provenance.

Inconsistent terminology.

Narrative-only storage.

---

## Anti-patterns

### Content Without Metadata

---

### Evidence Without Structure

---

### Non-reproducible Research

---

### Editorial Shortcuts

---

### Citation Dead Ends

---

## Implementation Impact

### Product

Research becomes a primary platform capability.

---

### Frontend

Researchers can inspect deep metadata.

---

### Backend

Knowledge objects expose canonical identifiers.

---

### Database

Schemas prioritize normalization and provenance.

---

### AI Platform

Extraction pipelines produce structured outputs suitable for future analysis.

---

### Search

Evidence and relationships become independently searchable.

---

## Related Principles

* Knowledge First
* Evidence Before Opinion
* Explainability
* Transparency
* Version Everything

---

## Decision Checklist

Before publishing canonical knowledge ask:

* Could another researcher independently verify this?
* Is provenance complete?
* Are identifiers stable?
* Can this object be cited?
* Will this remain useful ten years from now?

If not, additional editorial work is required.

---

# Principle 10 — Human Review

---

## Statement

Artificial Intelligence accelerates knowledge production.

Humans remain responsible for canonical knowledge.

No AI-generated knowledge becomes authoritative without appropriate human review.

Editorial responsibility cannot be delegated to software.

---

## Motivation

Large Language Models are powerful assistants.

They summarize.

Extract.

Translate.

Classify.

Compare.

Infer.

Generate.

However, they also hallucinate, omit context, misunderstand cultural nuance, and inherit biases from training data.

Because The Living Atlas preserves cultural knowledge for long-term use, final editorial responsibility must always remain with qualified human reviewers.

---

## Human Review Is Not Human Rewriting

Editorial review does not require humans to rewrite every AI output.

Instead, reviewers evaluate:

accuracy,

provenance,

completeness,

context,

cultural sensitivity,

relationship correctness,

confidence,

and evidence quality.

AI performs the repetitive work.

Humans perform the critical thinking.

---

## Levels Of Review

Different artifacts require different review depth.

Low Risk

Formatting

Translation

Metadata normalization

Medium Risk

Entity extraction

Relationship extraction

Classification

High Risk

Canonical claims

Historical interpretation

Editorial publication

Knowledge approval

The greater the impact on canonical knowledge, the greater the required level of human oversight.

---

## Human Accountability

Every published knowledge object should identify:

* approving editor
* review timestamp
* workflow version
* editorial decision
* AI participation
* supporting evidence

Responsibility must always be attributable.

---

## Examples

### Good

AI proposes.

Editor approves.

AI extracts entities.

Researcher validates relationships.

AI summarizes.

Historian reviews interpretation.

---

### Bad

Publishing AI output automatically.

Removing editorial approval.

Allowing AI to overwrite canonical knowledge.

Treating AI confidence as editorial approval.

---

## Anti-patterns

### Autonomous Publishing

---

### AI As Authority

---

### Rubber Stamp Reviews

---

### Missing Accountability

---

### Unreviewed Canonical Updates

---

## Implementation Impact

### Product

Editorial workflows require explicit review states.

---

### Frontend

Review interfaces compare AI suggestions with canonical knowledge.

---

### Backend

Workflow engines enforce approval gates before publication.

---

### Database

Approval records, reviewer identities, and workflow history are permanently preserved.

---

### AI Platform

All generated outputs are considered proposals until accepted by editorial workflows.

---

### Architecture

Human review becomes an architectural guarantee rather than an operational habit.

---

## Related Principles

* AI Assists
* Humans Decide
* Evidence Before Opinion
* Transparency
* Explainability

---

## Decision Checklist

Before allowing AI to influence canonical knowledge ask:

* Has a qualified reviewer examined the result?
* Is supporting evidence available?
* Can the reviewer reject or modify the output?
* Is accountability recorded?
* Would the platform still be trustworthy if AI were wrong?

If the answer to any question is no, the workflow must include additional human review.

---

# AI Principles

Artificial Intelligence is one of the most powerful capabilities within The Living Atlas.

It accelerates ingestion.

It organizes knowledge.

It discovers relationships.

It generates summaries.

It assists research.

It reduces repetitive editorial work.

However, AI is not the owner of knowledge.

AI serves the platform.

The platform does not serve AI.

The purpose of these principles is to ensure that AI strengthens human knowledge without replacing human responsibility.

Knowledge remains a human endeavor.

AI expands human capability.

---

# Principle 11 — AI Assists

---

## Statement

Artificial Intelligence exists to assist humans in creating, organizing, understanding, and preserving knowledge.

AI is an augmentation system.

It is never the primary author, editor, reviewer, or owner of canonical knowledge.

The purpose of AI is to reduce repetitive work while allowing humans to focus on judgment, interpretation, and critical thinking.

---

## Motivation

Modern AI systems excel at repetitive cognitive tasks.

Examples include:

* transcription
* translation
* summarization
* classification
* entity extraction
* relationship extraction
* clustering
* semantic search
* similarity detection
* metadata generation

These tasks consume significant editorial time but require relatively little domain judgment.

Conversely, AI remains limited in areas such as:

* historical interpretation
* cultural sensitivity
* contextual nuance
* ethical evaluation
* conflicting evidence analysis
* editorial prioritization
* community representation

The Living Atlas therefore assigns AI to areas where automation increases efficiency while preserving human authority over meaning.

---

## AI Is A Knowledge Accelerator

Within the platform, AI performs work that enables humans to produce higher-quality knowledge more efficiently.

Typical responsibilities include:

### Knowledge Extraction

Extract entities, places, people, rituals, motifs, themes, timelines, references, and relationships from transcripts and documents.

---

### Knowledge Enrichment

Suggest missing metadata.

Infer possible relationships.

Recommend classifications.

Detect duplicate entities.

Suggest confidence levels.

---

### Knowledge Organization

Generate tags.

Cluster related content.

Recommend collections.

Normalize terminology.

Resolve aliases.

---

### Content Generation

Draft narrative articles.

Generate educational summaries.

Create introductions.

Produce multilingual translations.

Generate accessibility summaries.

---

### Research Assistance

Compare sources.

Highlight contradictions.

Identify missing evidence.

Suggest related material.

Recommend additional reading.

---

### Discovery

Power semantic search.

Enable natural-language exploration.

Recommend connected knowledge.

Support graph exploration.

---

## AI Produces Proposals

No AI-generated artifact is considered canonical.

Instead, every AI output is treated as one of the following:

Proposal

Suggestion

Recommendation

Draft

Prediction

Inference

Classification

Extraction

These outputs become inputs to editorial workflows.

They do not become knowledge automatically.

---

## AI Must Be Reproducible

Every AI execution should be reproducible.

Each execution records:

* model identifier
* provider
* prompt version
* workflow version
* input sources
* execution timestamp
* output identifier
* confidence metadata
* processing duration

Future editors should be able to understand exactly how an output was produced.

---

## AI Should Reduce Human Work

Every AI capability should satisfy at least one of the following goals:

Reduce repetitive work.

Improve discovery.

Increase consistency.

Improve scalability.

Surface hidden relationships.

Increase research efficiency.

If an AI feature does not meaningfully improve human productivity or knowledge quality, it should not be introduced.

---

## Examples

### Good

AI extracts entities from transcripts.

AI proposes graph relationships.

AI drafts articles for review.

AI identifies duplicate folklore.

AI suggests missing citations.

AI clusters similar stories.

---

### Bad

AI publishes knowledge directly.

AI silently edits canonical stories.

AI overrides editorial decisions.

AI modifies provenance.

AI changes relationship confidence without review.

---

## Anti-patterns

### AI As Author

Treating generated text as final knowledge.

---

### AI As Editor

Allowing AI to approve publication.

---

### AI As Historian

Assuming AI interpretation is historically authoritative.

---

### AI Without Traceability

Generated outputs lacking provenance.

---

### AI Everywhere

Introducing AI where deterministic software provides a simpler and more reliable solution.

---

## Implementation Impact

### Product

AI features are optional assistants rather than mandatory workflows.

---

### Frontend

Users always understand when AI contributed to an artifact.

AI suggestions remain distinguishable from approved knowledge.

---

### Backend

AI outputs enter editorial workflows as proposals.

Canonical knowledge changes only through approved workflow transitions.

---

### AI Platform

Every service produces structured, reproducible outputs.

No AI service writes directly into canonical knowledge tables.

---

### Database

Generated artifacts remain separate from canonical objects.

All AI outputs retain execution metadata.

---

### Architecture

AI communicates through asynchronous domain events.

Business services own canonical state.

AI services own processing only.

---

## Related Principles

* Humans Decide
* Human Review
* Explainability
* Transparency
* Version Everything

---

## Decision Checklist

Before introducing an AI feature ask:

* Does it reduce repetitive work?
* Does it improve knowledge quality?
* Is every output reproducible?
* Can editors reject the output?
* Does AI remain an assistant rather than an authority?

If not, the feature should be reconsidered.

---

# Principle 12 — Humans Decide

---

## Statement

Final authority over canonical knowledge always belongs to humans.

Artificial Intelligence may recommend.

Artificial Intelligence may explain.

Artificial Intelligence may summarize.

Artificial Intelligence may predict.

Artificial Intelligence may prioritize.

Only humans may decide what becomes part of the platform's canonical knowledge.

---

## Motivation

Knowledge is not merely data.

Knowledge reflects history, culture, identity, language, and community memory.

Many editorial decisions require:

ethical judgment,

historical awareness,

cultural sensitivity,

interpretive reasoning,

and accountability.

These responsibilities cannot be delegated to probabilistic systems.

The Living Atlas therefore establishes an explicit separation between computational assistance and editorial authority.

---

## Decision Ownership

Ownership within the platform follows a clear hierarchy.

AI owns:

* processing
* extraction
* inference
* recommendation
* summarization
* translation
* classification

Humans own:

* approval
* publication
* interpretation
* conflict resolution
* canonical modeling
* editorial policy
* cultural representation
* quality assurance

This separation should remain true regardless of future advances in AI capability.

---

## Editorial Authority

Every canonical change must ultimately be attributable to a human decision.

Examples include:

Approving a new story.

Rejecting AI-generated entities.

Resolving conflicting evidence.

Selecting preferred terminology.

Publishing an article.

Accepting graph relationships.

Approving translations.

Resolving duplicate entities.

The responsible editor becomes part of the permanent editorial history.

---

## AI Confidence Does Not Equal Truth

High-confidence AI predictions are not automatically correct.

Likewise, low-confidence predictions are not automatically wrong.

Confidence reflects the model's internal assessment of probability.

Editorial decisions require broader context, evidence, and judgment.

Confidence informs decisions.

It does not replace them.

---

## Human Override

Editors must always retain the ability to:

Approve.

Reject.

Modify.

Replace.

Annotate.

Delay.

Escalate.

Every AI recommendation.

No AI-generated artifact should bypass human intervention before affecting canonical knowledge.

---

## Examples

### Good

Editor reviews AI-generated article before publication.

Researcher validates extracted relationships.

Editorial board resolves conflicting interpretations.

Human approves ontology changes.

---

### Bad

Automatic publication after AI generation.

Automatic graph updates without review.

Automatic evidence acceptance.

AI resolving historical disputes autonomously.

---

## Anti-patterns

### Autonomous Knowledge

Canonical knowledge changes without human approval.

---

### AI Governance

Editorial policy determined by AI.

---

### Human Rubber Stamping

Editors approve AI outputs without meaningful review.

---

### Hidden Responsibility

No individual can be identified as responsible for published knowledge.

---

### Confidence Worship

Treating numerical confidence as editorial certainty.

---

## Implementation Impact

### Product

Editorial workflows always include explicit human approval states before publication.

---

### Frontend

Review interfaces emphasize comparison, evidence inspection, and informed decision-making rather than one-click acceptance.

---

### Backend

Workflow engines enforce mandatory approval checkpoints for all canonical changes.

---

### AI Platform

Services terminate after producing proposals and publishing completion events.

They never commit canonical changes directly.

---

### Database

Approval records, reviewer identities, timestamps, comments, and decision rationale become permanent components of the knowledge history.

---

### Architecture

The boundary between AI processing and business decision-making remains explicit across every service.

Queues transport proposals.

Business services evaluate proposals.

Editors authorize publication.

---

## Related Principles

* AI Assists
* Human Review
* Evidence Before Opinion
* Explainability
* Transparency
* One Source of Truth

---

## Decision Checklist

Before allowing AI to participate in any workflow ask:

* Who makes the final decision?
* Can the AI output be rejected?
* Is the responsible human recorded?
* Does the workflow preserve accountability?
* Can canonical knowledge change without human approval?

If the answer to the last question is yes, the design violates this principle and must be redesigned.

---

# Principle 13 — Prompt is Code

---

## Statement

Prompts are executable business assets.

They are not temporary text.

They are not configuration.

They are not documentation.

Every prompt within The Living Atlas is treated as production code.

It must be versioned, reviewed, tested, reproducible, and governed using the same engineering discipline applied to software.

---

## Motivation

Large Language Models execute prompts in much the same way that compilers execute source code.

A small prompt modification can significantly alter:

* extracted entities
* generated relationships
* article structure
* factual accuracy
* writing style
* confidence
* downstream embeddings
* graph projection

Because prompts directly influence canonical knowledge, they are production artifacts rather than operational configuration.

---

## Prompts Are Business Logic

The platform should never embed prompts inside application code.

Instead, prompts exist as managed assets.

Examples include:

Entity Extraction Prompt

Story Extraction Prompt

Knowledge Normalization Prompt

Article Generation Prompt

Narrative Style Prompt

Research Summary Prompt

Relationship Extraction Prompt

Translation Prompt

Fact Verification Prompt

Editorial Assistant Prompt

Each serves a well-defined business purpose.

---

## Prompt Registry

Every production prompt belongs to a centralized Prompt Registry.

Each prompt records:

Prompt ID

Version

Purpose

Owner

Author

Creation Date

Last Review Date

Supported Models

Expected Inputs

Expected Outputs

Temperature

System Prompt

User Prompt Template

Variables

Validation Rules

Deprecation Status

Approval Status

Documentation

Prompts become discoverable, reviewable, and reusable assets across the platform.

---

## Prompt Lifecycle

Prompt development follows a controlled lifecycle.

Draft

↓

Internal Testing

↓

Evaluation

↓

Editorial Approval

↓

Production

↓

Deprecation

↓

Archive

Prompt changes never overwrite previous versions.

Every execution references an immutable prompt version.

---

## Prompt Testing

Every production prompt should be evaluated before release.

Typical evaluation includes:

Output consistency

Extraction accuracy

Relationship quality

Hallucination rate

Token usage

Latency

Cost

Regression testing

Golden datasets

Prompt quality is measured, not assumed.

---

## Examples

### Good

Versioned prompt registry.

Prompt pull requests.

Regression benchmarks.

Prompt ownership.

Automated prompt evaluation.

---

### Bad

Hardcoded prompts inside source code.

Editing prompts directly in production.

Undocumented prompt changes.

Sharing prompts through chat history.

Copy-pasting prompts between services.

---

## Anti-patterns

### Prompt Sprawl

Multiple copies of similar prompts.

---

### Hidden Prompt Changes

Prompt modifications without version increments.

---

### Prompt Drift

Different services using inconsistent prompt versions.

---

### Prompt Coupling

Business logic tightly coupled to a specific prompt implementation.

---

## Implementation Impact

### Product

Prompt quality becomes part of product quality.

---

### Backend

Business events reference prompt versions.

---

### AI Platform

Prompt Registry becomes a core platform capability.

All AI services load prompts dynamically.

---

### Database

Prompt metadata becomes canonical.

Execution history references immutable prompt versions.

---

### Architecture

Prompt governance becomes part of software governance.

---

## Related Principles

* Version Everything
* Explainability
* Deterministic Pipeline
* Model Agnostic

---

## Decision Checklist

Before introducing a new prompt ask:

* Does it belong in the Prompt Registry?
* Is it versioned?
* Can it be tested?
* Can it be reproduced?
* Does it have an owner?
* Can previous executions still be reproduced after future prompt changes?

If any answer is no, the prompt is not production-ready.

---

# Principle 14 — Model Agnostic

---

## Statement

The Living Atlas is built around AI capabilities rather than AI vendors.

No business workflow should depend on a specific Large Language Model.

Models are replaceable.

Knowledge is permanent.

---

## Motivation

The AI ecosystem changes rapidly.

Today's leading model may become obsolete within months.

Pricing changes.

Licensing changes.

Capabilities evolve.

New providers emerge.

Building business logic around one provider creates unnecessary technical debt.

Instead, workflows should depend on abstract capabilities such as:

Extraction

Summarization

Classification

Translation

Reasoning

Generation

Embedding

The implementation may change.

The workflow remains stable.

---

## Capability First

The platform chooses models based on required capability.

Examples:

Fast classification

↓

Small reasoning model

---

Long-form article generation

↓

Large reasoning model

---

Embedding creation

↓

Dedicated embedding model

---

Translation

↓

Translation-optimized model

The workflow specifies capability.

The orchestration layer selects the provider.

---

## Provider Independence

Supported providers may include:

OpenAI

Anthropic

Google

Mistral

DeepSeek

OpenRouter

Self-hosted models

Future providers

No domain service should require knowledge of vendor-specific APIs.

---

## Vendor Lock-In Is A Risk

Vendor dependence creates risks including:

Pricing changes

API deprecation

Regional availability

Regulatory restrictions

Model discontinuation

Quality regression

Rate limits

A model abstraction layer minimizes these risks.

---

## Examples

### Good

Capability-based routing.

Configurable provider selection.

Provider fallback.

Multiple supported models.

---

### Bad

Hardcoding GPT-specific logic.

Embedding provider-specific response formats.

Vendor-specific business rules.

Assuming one model is always available.

---

## Anti-patterns

### Single Vendor Architecture

---

### Prompt Vendor Coupling

---

### Model-Specific Business Logic

---

### AI Provider As Infrastructure

---

## Implementation Impact

### Product

Capabilities evolve without changing product behavior.

---

### Backend

Domain events remain provider-independent.

---

### AI Platform

Orchestration selects models dynamically.

Providers implement common interfaces.

---

### Database

Execution records include provider and model metadata without affecting canonical knowledge.

---

### Architecture

Model replacement becomes an operational task rather than a software migration.

---

## Related Principles

* Prompt is Code
* AI Assists
* Version Everything
* Deterministic Pipeline

---

## Decision Checklist

Before integrating a model ask:

* Can another model replace it?
* Is business logic independent of vendor APIs?
* Are prompts portable?
* Can orchestration switch providers?
* Does canonical knowledge remain unaffected by provider replacement?

If not, redesign the integration.

---

# Principle 15 — Deterministic Pipeline

---

## Statement

Given the same inputs, configuration, prompt versions, workflow versions, and model versions, the AI platform should produce reproducible results or explicitly record why differences occurred.

Every AI execution must be traceable.

Every output must be reproducible.

---

## Motivation

Knowledge platforms require long-term reliability.

Editors need to understand why knowledge changed.

Researchers need to reproduce extraction.

Engineers need to debug pipelines.

Auditors need to inspect AI decisions.

Without deterministic execution, none of these activities are reliable.

The goal is not identical token-by-token output—which may be impossible with some models—but deterministic workflow behavior and complete execution traceability.

---

## Determinism Through Metadata

Every execution records:

Execution ID

Workflow Version

Pipeline Version

Prompt Version

Model Version

Provider

Input Dataset

Canonical Story Version

Configuration

Temperature

Seed (if supported)

Execution Timestamp

Output Version

Retry Count

Processing Duration

This metadata allows historical executions to be reconstructed and compared.

---

## Pipelines Are State Machines

Every AI workflow follows explicit state transitions.

Example:

Queued

↓

Running

↓

Extracting

↓

Generating

↓

Validating

↓

Completed

↓

Reviewed

↓

Approved

↓

Published

No hidden processing.

No implicit transitions.

Every state is observable.

---

## Idempotency

Every stage should safely handle retries.

Repeated execution should not create duplicate:

articles,

knowledge objects,

relationships,

embeddings,

events,

or graph projections.

Pipelines must be idempotent by design.

---

## Failure Is Expected

Failures are first-class events.

Examples include:

Provider unavailable.

Queue timeout.

Rate limit exceeded.

Malformed transcript.

Prompt validation failed.

Output validation failed.

Embedding failure.

Relationship extraction failure.

The platform records failures rather than hiding them.

Retry behavior is deterministic and governed by workflow policies.

---

## Examples

### Good

Immutable execution history.

Replayable workflows.

Explicit pipeline states.

Idempotent queue processing.

Deterministic retries.

---

### Bad

Hidden retries.

Silent failures.

Random prompt selection.

State stored only in memory.

Untraceable executions.

---

## Anti-patterns

### Fire-and-Forget AI

---

### Non-idempotent Workers

---

### Invisible Pipeline State

---

### Mutable Execution Metadata

---

### Undocumented Retry Logic

---

## Implementation Impact

### Product

Users receive predictable AI-assisted workflows.

---

### Backend

Every AI request becomes a versioned workflow execution.

---

### AI Platform

Workers operate as deterministic state machines driven by queues.

---

### Database

Execution history is immutable and auditable.

---

### Architecture

Observability, replayability, and fault recovery become architectural guarantees rather than operational conveniences.

---

## Related Principles

* Prompt is Code
* Model Agnostic
* Version Everything
* Explainability
* Human Review

---

## Decision Checklist

Before implementing any AI pipeline ask:

* Can this execution be replayed?
* Is every state observable?
* Is processing idempotent?
* Can failures be diagnosed from metadata alone?
* Can the workflow be reproduced months later?

If not, the pipeline requires additional engineering before production deployment.

---

# UX Principles

The Living Atlas is designed around how people learn rather than how software is traditionally organized.

Readers arrive with different backgrounds.

Some want a quick answer.

Others seek deep historical context.

Researchers require evidence.

Creators seek inspiration.

Students need explanation.

Experts expect precision.

The user experience should therefore adapt to the depth of curiosity rather than forcing every user through the same interface.

The purpose of these principles is to ensure that every interaction makes knowledge easier to discover, understand, and trust.

---

# Principle 16 — Reader First

---

## Statement

Every product decision should prioritize the reader's ability to discover, understand, and trust knowledge.

Technology exists to serve reading.

Reading does not exist to demonstrate technology.

The success of a feature is measured by whether it improves knowledge understanding.

---

## Motivation

Many digital platforms optimize for:

engagement,

retention,

advertising,

virality,

or content production.

The Living Atlas has a different objective.

Its primary responsibility is helping people learn.

Every feature should therefore reduce cognitive effort while increasing understanding.

Readers should spend their attention on knowledge rather than interface mechanics.

---

## Knowledge Before Interface

Interfaces should never become the center of attention.

Navigation exists to reach knowledge.

Search exists to discover knowledge.

AI exists to explain knowledge.

Atlas exists to visualize knowledge.

The interface should quietly support understanding rather than compete with it.

---

## Reading Is The Primary Experience

Although the platform contains:

knowledge graphs,

maps,

AI,

collections,

research tools,

and editorial workflows,

the most common activity remains reading.

Reading experiences therefore receive the highest design priority.

Typography,

spacing,

content hierarchy,

citation visibility,

relationship navigation,

and contextual explanations are more important than visual novelty.

---

## Minimize Cognitive Load

Every screen should answer three questions immediately:

Where am I?

What am I looking at?

What should I do next?

Users should never feel lost inside the knowledge graph.

Complexity belongs to the system.

Not to the reader.

---

## Multiple Reading Styles

Readers consume knowledge differently.

Examples include:

Quick Reading

Overview Reading

Narrative Reading

Research Reading

Comparative Reading

Evidence Reading

The platform supports all of these without duplicating knowledge.

---

## Examples

### Good

Clear reading hierarchy.

Readable typography.

Visible relationships.

Contextual definitions.

Simple navigation.

Focused layouts.

---

### Bad

Decorative interfaces.

Hidden content behind animations.

Feature-heavy dashboards.

Unreadable typography.

Competing visual elements.

---

## Anti-patterns

### Dashboard First

Treating every page as an analytics dashboard.

---

### Interface Before Content

Prioritizing visual effects over readability.

---

### Technology Showcase

Adding AI simply because it is available.

---

### Cognitive Overload

Displaying excessive controls simultaneously.

---

## Implementation Impact

### Product

Reading becomes the primary product experience.

---

### Frontend

Every layout is optimized for comprehension before interaction density.

---

### Backend

Content APIs prioritize structured reading experiences.

---

### AI Platform

AI explains knowledge rather than replacing it.

---

### Design System

Typography becomes the foundation of the visual language.

---

## Related Principles

* Knowledge First
* Progressive Disclosure
* Accessibility by Default

---

## Decision Checklist

Before implementing a feature ask:

* Does this improve understanding?
* Does it reduce cognitive effort?
* Does it help readers discover knowledge?
* Would removing this feature improve clarity?

If the feature distracts more than it educates, it should be redesigned.

---

# Principle 17 — Progressive Disclosure

---

## Statement

Knowledge should be revealed gradually.

Readers should never be overwhelmed by complexity.

Every interface begins with essential understanding and progressively exposes deeper knowledge as curiosity increases.

---

## Motivation

Not every reader requires the same level of detail.

A visitor may only want a short explanation.

A student may need historical context.

A researcher may require evidence, citations, provenance, and conflicting interpretations.

Providing every detail immediately creates unnecessary cognitive load.

Hiding everything prevents meaningful exploration.

Progressive disclosure balances simplicity with depth.

---

## Layers Of Knowledge

The Living Atlas presents knowledge through successive layers.

Overview

↓

Summary

↓

Narrative

↓

Knowledge Objects

↓

Relationships

↓

Evidence

↓

Version History

↓

Editorial Metadata

↓

Raw Sources

Every deeper layer remains available without interrupting casual reading.

---

## Curiosity-Driven Navigation

The interface should reward curiosity.

Each interaction should answer:

"What else is connected to this?"

rather than:

"What page should I visit next?"

Knowledge naturally unfolds through exploration.

---

## Progressive Interface Complexity

The interface itself should also scale.

Casual readers see:

simple navigation,

basic metadata,

core relationships.

Researchers gain access to:

graph exploration,

timeline comparison,

provenance,

workflow history,

version history,

relationship metadata,

AI explanations.

The interface adapts to user intent.

---

## AI Uses Progressive Disclosure

AI responses should begin with concise explanations.

Readers can then request:

more evidence,

alternative interpretations,

historical context,

primary sources,

relationship analysis,

or conflicting viewpoints.

The AI behaves like an expert guide rather than an encyclopedia dump.

---

## Examples

### Good

Expandable evidence.

Collapsible metadata.

Context panels.

Layered reading.

On-demand graph exploration.

---

### Bad

Showing every relationship immediately.

Displaying hundreds of metadata fields.

Opening complex graphs by default.

Requiring expert knowledge for basic reading.

---

## Anti-patterns

### Information Dump

---

### Hidden Knowledge

---

### One-Level Interface

---

### Mandatory Complexity

---

## Implementation Impact

### Product

Knowledge becomes approachable without sacrificing depth.

---

### Frontend

Interfaces expose additional complexity only when requested.

---

### Backend

APIs support incremental loading of related knowledge.

---

### AI Platform

Responses become conversational layers rather than monolithic outputs.

---

### Search

Search results provide summaries first and evidence second.

---

## Related Principles

* Reader First
* Accessibility by Default
* Explainability

---

## Decision Checklist

Before exposing new information ask:

* Is this immediately necessary?
* Can it be revealed later?
* Does hiding it improve clarity?
* Can curious readers still access it easily?

If all information appears simultaneously, progressive disclosure has failed.

---

# Principle 18 — Accessibility by Default

---

## Statement

Accessibility is not an enhancement.

It is a baseline requirement.

Every feature should be usable by the widest possible audience without requiring specialized versions of the platform.

Knowledge should be accessible regardless of physical ability, cognitive style, language proficiency, device capability, or internet quality.

---

## Motivation

Knowledge belongs to everyone.

Many accessibility initiatives focus solely on technical compliance.

The Living Atlas adopts a broader perspective.

Accessibility includes:

physical accessibility,

cognitive accessibility,

linguistic accessibility,

technological accessibility,

cultural accessibility,

and educational accessibility.

Removing barriers increases both usability and knowledge preservation.

---

## Accessibility Beyond WCAG

Compliance with accessibility standards is the minimum expectation.

The platform additionally considers:

Progressive reading.

Terminology explanations.

Simplified summaries.

Language adaptation.

Offline reading.

Keyboard-first interaction.

Screen reader compatibility.

Reduced motion.

Color-independent communication.

Responsive layouts.

Low-bandwidth support.

These capabilities improve usability for all readers, not only users with disabilities.

---

## Knowledge Accessibility

Knowledge itself should be understandable.

The platform provides:

layered explanations,

contextual definitions,

pronunciation guidance,

cross-cultural terminology,

visual relationships,

maps,

timelines,

and summaries.

Readers choose the level of complexity appropriate for their background.

---

## Accessibility Across Devices

Knowledge should remain usable on:

desktop,

tablet,

mobile,

slow networks,

offline environments,

older hardware,

future devices.

The platform adapts without reducing the integrity of the underlying knowledge.

---

## Examples

### Good

Keyboard navigation.

High-contrast typography.

Screen reader support.

Offline reading.

Accessible maps.

Responsive layouts.

Contextual terminology.

---

### Bad

Mouse-only interaction.

Color-only indicators.

Heavy animations.

Unreadable typography.

Desktop-only interfaces.

Complex language without explanation.

---

## Anti-patterns

### Accessibility As Afterthought

---

### Compliance Only

---

### Visual-Only Communication

---

### Performance Ignorance

---

## Implementation Impact

### Product

Accessibility becomes a core quality metric.

---

### Frontend

Every component satisfies accessibility requirements before release.

---

### Backend

Structured semantic metadata supports assistive technologies.

---

### AI Platform

AI generates summaries and explanations appropriate for different reading abilities.

---

### Design System

Accessibility requirements become part of every design token and component specification.

---

## Related Principles

* Reader First
* Progressive Disclosure
* Knowledge First
* Transparency

---

## Decision Checklist

Before releasing any feature ask:

* Can it be used without a mouse?
* Can it be understood by first-time readers?
* Does it work on low-end devices?
* Is meaning conveyed without relying solely on color?
* Can users access the same knowledge regardless of ability?

If any answer is no, the feature is not ready for production.

---

# Principle 19 — Offline Friendly

---

## Statement

Knowledge should remain accessible regardless of internet connectivity.

The Living Atlas is designed with an offline-first mindset wherever technically and operationally feasible.

Users should be able to continue reading, researching, and learning even when network connectivity is slow, unstable, expensive, or temporarily unavailable.

Connectivity should enhance the experience, not determine whether knowledge can be accessed.

---

## Motivation

Knowledge preservation should not depend on infrastructure quality.

Many communities with the richest cultural heritage also experience limited internet access.

Researchers often conduct fieldwork in remote locations.

Students may rely on intermittent mobile connections.

Museums may operate installations without continuous internet access.

If knowledge disappears whenever the network fails, then the platform has failed one of its primary missions.

Offline capability therefore supports cultural preservation, education, and long-term accessibility.

---

## Offline Is A Product Capability

Offline support is not merely browser caching.

It is a deliberate product capability.

Users should understand which knowledge is available offline, which content requires synchronization, and what changes will occur once connectivity is restored.

Offline behavior should be predictable.

---

## Progressive Offline Experience

Different capabilities require different levels of offline support.

### Fully Offline

Previously viewed articles.

Knowledge summaries.

Story content.

Saved collections.

Reader preferences.

Bookmarks.

Notes.

Reading history.

---

### Offline With Synchronization

Annotations.

Research notes.

Collection management.

Draft articles.

Editorial comments.

Workspace configuration.

Changes remain local until synchronization succeeds.

---

### Online Required

AI generation.

Semantic search.

Knowledge graph expansion.

Collaborative editing.

Editorial approval workflows.

Authentication.

Large media downloads.

These capabilities should fail gracefully and clearly communicate why connectivity is required.

---

## Local Knowledge Cache

The platform maintains a local cache for frequently accessed knowledge.

Examples include:

Recently viewed stories.

Saved research collections.

Pinned knowledge objects.

Frequently referenced entities.

Offline glossary.

Media thumbnails.

The cache prioritizes knowledge value rather than simply recent access.

---

## Synchronization Philosophy

Synchronization should be:

Automatic.

Conflict-aware.

Incremental.

Resumable.

Idempotent.

Network-efficient.

Users should never fear losing work because connectivity changed unexpectedly.

---

## Offline Reading

Reading remains the highest priority.

Users should continue to access:

Narratives.

Knowledge articles.

Metadata.

References.

Relationship summaries.

Maps where previously downloaded.

Images already cached.

Typography, navigation, and layout remain fully functional without internet access.

---

## Offline Research

Researchers should continue working offline.

Possible activities include:

Writing annotations.

Comparing notes.

Organizing collections.

Reviewing downloaded sources.

Preparing editorial drafts.

Synchronization occurs when connectivity returns.

---

## Examples

### Good

Offline reading library.

Cached knowledge collections.

Background synchronization.

Queued annotations.

Graceful offline indicators.

Incremental synchronization.

---

### Bad

Blank pages when offline.

Data loss after reconnecting.

Repeated downloads.

Offline mode requiring manual activation.

Blocking the entire application because one request failed.

---

## Anti-patterns

### Network Dependency

Every interaction requires an active connection.

---

### Cache Without Strategy

Large uncontrolled caches consuming device storage.

---

### Silent Synchronization Failures

Users believe work has been saved when synchronization failed.

---

### Offline Lockout

Preventing users from reading already available knowledge because authentication expired.

---

## Implementation Impact

### Product

Offline capability becomes part of the core reading experience.

---

### Frontend

Applications use local storage, IndexedDB, Service Workers, and intelligent cache management.

---

### Backend

Synchronization APIs become idempotent and support incremental updates.

---

### AI Platform

AI processing remains online, but generated outputs become available for offline reading once synchronized.

---

### Architecture

Offline synchronization is treated as a first-class workflow rather than an implementation detail.

---

## Related Principles

* Reader First
* Accessibility by Default
* Progressive Disclosure
* Long-term Thinking

---

## Decision Checklist

Before implementing a feature ask:

* Can users continue reading without internet?
* Can work be saved locally?
* Can synchronization safely resume later?
* Does the user clearly understand offline limitations?
* Will connectivity failures result in data loss?

If any answer is yes to data loss or no to graceful degradation, the feature requires redesign.

---

# Principle 20 — Fast by Default

---

## Statement

Speed is a feature.

Every interaction should feel immediate, predictable, and responsive.

Performance is not an optimization phase after development.

It is a fundamental product requirement.

Users should spend their time understanding knowledge rather than waiting for software.

---

## Motivation

The Living Atlas contains:

millions of knowledge objects,

knowledge graphs,

interactive maps,

AI-assisted search,

large media collections,

and complex relationships.

Without disciplined performance engineering, these capabilities can quickly overwhelm users.

Fast systems encourage exploration.

Slow systems discourage curiosity.

Performance directly influences learning.

---

## Performance Is Perceived Responsiveness

Users do not measure milliseconds.

They measure perceived responsiveness.

The platform should therefore prioritize:

Immediate feedback.

Progressive loading.

Incremental rendering.

Predictable transitions.

Background processing.

Perceived responsiveness is often more valuable than raw benchmark performance.

---

## Reading Must Be Instant

Opening a story or article should prioritize:

Title.

Summary.

Primary content.

Core metadata.

The remainder of the page can progressively load.

Readers should begin learning immediately.

---

## Progressive Loading

Large datasets should never block interaction.

Examples include:

Knowledge graphs.

Maps.

Search results.

Relationship panels.

Comments.

Version history.

Editorial metadata.

These load progressively as users request deeper exploration.

---

## Performance Budget

Every feature consumes part of a finite performance budget.

New functionality should justify its computational cost.

Questions to ask include:

Does this animation improve comprehension?

Does this visualization communicate something valuable?

Does this background request improve the reader experience?

If the answer is no, the feature should be simplified or removed.

---

## Backend Performance

Fast experiences require efficient services.

Principles include:

Efficient database queries.

Pagination by default.

Incremental synchronization.

Asynchronous processing.

Event-driven architecture.

Caching of immutable knowledge.

Minimal network round-trips.

Performance is a platform responsibility rather than solely a frontend concern.

---

## AI Performance

AI should never block primary user workflows.

Long-running AI operations execute asynchronously.

The interface provides:

Processing status.

Progress indication.

Estimated completion.

Notifications when complete.

Reading and exploration continue uninterrupted.

---

## Performance Across Devices

Fast by Default applies equally to:

High-end desktops.

Budget Android phones.

Tablets.

Slow CPUs.

Limited memory devices.

Performance targets should reflect real-world hardware rather than developer workstations.

---

## Examples

### Good

Progressive rendering.

Skeleton loading.

Instant navigation.

Optimized search.

Lazy graph loading.

Incremental hydration.

Background synchronization.

---

### Bad

Blocking the interface while waiting for AI.

Loading entire graphs before displaying content.

Rendering thousands of DOM elements simultaneously.

Multiple redundant API calls.

Heavy client-side computation during reading.

---

## Anti-patterns

### Feature Before Performance

---

### Loading Everything

---

### Synchronous AI

---

### Infinite Rendering

---

### Performance By Hardware

Assuming powerful devices will compensate for inefficient software.

---

## Implementation Impact

### Product

Performance becomes a measurable quality attribute for every feature.

---

### Frontend

Applications adopt code splitting, route-based lazy loading, virtualization, incremental hydration, intelligent prefetching, and optimized rendering strategies.

---

### Backend

Services expose efficient APIs with pagination, caching, asynchronous processing, and event-driven workflows.

---

### AI Platform

All AI processing is asynchronous and queue-driven.

User-facing applications never wait for AI inference before becoming interactive.

---

### Architecture

Performance budgets are established at every architectural layer and validated continuously.

---

## Related Principles

* Reader First
* Progressive Disclosure
* Offline Friendly
* Accessibility by Default
* Long-term Thinking

---

## Decision Checklist

Before shipping a feature ask:

* Does the interface remain responsive during loading?
* Can users begin reading immediately?
* Is heavy computation performed asynchronously?
* Does the feature respect established performance budgets?
* Will this perform well on low-end devices and slow networks?

If any answer is no, the implementation should be optimized before release.

---

# Architecture Principles

The Living Atlas is intended to preserve knowledge for decades rather than software for a single release cycle.

Technologies will evolve.

Programming languages will change.

Frameworks will become obsolete.

Databases will be replaced.

AI providers will emerge and disappear.

What should remain stable is the knowledge itself and the architectural principles that protect it.

These principles guide every technical decision across backend services, frontend applications, AI Platform, data platform, and infrastructure.

Architecture should maximize longevity while minimizing unnecessary coupling.

---

# Principle 21 — Long-term Thinking

---

## Statement

Every architectural decision should prioritize long-term maintainability over short-term convenience.

The platform should remain understandable, extensible, and operable for decades.

Temporary implementation convenience must never compromise permanent knowledge preservation.

---

## Motivation

Most software is designed for the next release.

The Living Atlas is designed for the next generation.

Historical knowledge may outlive:

development teams,

technology vendors,

programming languages,

cloud providers,

AI models,

and even operating systems.

Architecture therefore becomes part of the preservation strategy.

---

## Design For Decades

Every component should answer:

Will this still make sense in ten years?

Can another team maintain it?

Can the underlying knowledge survive framework replacement?

Can the system evolve without rewriting everything?

Long-term maintainability is a functional requirement.

---

## Prefer Evolution Over Replacement

Architecture should evolve gradually.

Examples include:

Modular Monolith → Distributed Services

PostgreSQL Scaling → Sharding

Single AI Provider → Multi-provider

Single Region → Multi-region

Monolithic Search → Distributed Search

The architecture should accommodate these transitions without disrupting business domains.

---

## Stable Domain, Replaceable Technology

Business domains should remain stable even when implementation changes.

For example:

Story remains Story.

Knowledge remains Knowledge.

Research remains Research.

Editorial remains Editorial.

Only implementation changes.

---

## Examples

### Good

DDD modules.

Versioned APIs.

Immutable events.

Clear boundaries.

Migration-friendly architecture.

---

### Bad

Framework-driven architecture.

Business logic tied to infrastructure.

Technology-specific domain models.

Frequent rewrites.

---

## Anti-patterns

Framework First

Vendor Lock-in

Short-term Optimization

Architecture Rewrites

---

## Implementation Impact

Product

Features evolve without breaking knowledge.

Frontend

Stable user experience across technical upgrades.

Backend

Modules evolve independently.

AI Platform

Providers change without changing workflows.

Infrastructure

Deployment technology remains replaceable.

---

## Related Principles

Technology Independent

Open Standards

Version Everything

---

## Decision Checklist

Before adopting a technology ask:

* Will this decision still make sense in ten years?
* Can it evolve incrementally?
* Does it increase long-term maintainability?
* Can it be replaced without changing domain logic?

If not, reconsider the decision.

---

# Principle 22 — Open Standards

---

## Statement

Whenever practical, The Living Atlas should adopt open standards rather than proprietary protocols, formats, or vendor-specific technologies.

Knowledge should never become trapped inside a closed ecosystem.

---

## Motivation

Open standards maximize:

interoperability,

portability,

preservation,

and future compatibility.

Cultural knowledge should remain usable regardless of software vendors.

---

## Preferred Standards

Examples include:

HTTP

REST

JSON

OpenAPI

Markdown

UTF-8

Unicode

GeoJSON

GraphQL (where appropriate)

OAuth 2

OIDC

JWT

Kafka Protocol

SQL

OpenTelemetry

OpenSearch-compatible APIs

Vector standards

W3C accessibility standards

---

## Data Portability

Every canonical knowledge object should be exportable.

Preferred export formats include:

JSON

Markdown

CSV

GeoJSON

RDF (future)

GraphML (future)

BibTeX

RIS

Knowledge should always outlive software.

---

## Examples

### Good

OpenAPI contracts.

Markdown documentation.

JSON events.

Standard authentication.

Portable exports.

---

### Bad

Binary proprietary formats.

Undocumented protocols.

Vendor-specific APIs.

Closed serialization.

---

## Anti-patterns

Closed Ecosystems

Vendor-specific Storage

Custom Network Protocols

Non-standard Authentication

---

## Implementation Impact

Backend

Standardized APIs.

Frontend

Standard browser capabilities.

AI Platform

Provider abstraction.

Database

Portable schemas.

Architecture

Maximum interoperability.

---

## Related Principles

Technology Independent

API First

Long-term Thinking

---

## Decision Checklist

Before introducing a technology ask:

* Is there an open standard?
* Can data be exported?
* Will future systems understand this format?
* Can another implementation replace it?

---

# Principle 23 — API First

---

## Statement

Every capability should be designed as a contract before it is implemented.

Applications consume APIs.

They do not bypass them.

Contracts become the foundation for independent evolution.

---

## Motivation

An API defines business capability rather than implementation.

Designing contracts first improves:

consistency,

parallel development,

testing,

documentation,

and long-term compatibility.

---

## API Before Implementation

The workflow becomes:

Business capability

↓

API contract

↓

Domain model

↓

Implementation

↓

Testing

Not the reverse.

---

## APIs Represent Domains

APIs expose business concepts.

Examples:

Stories

Knowledge

Collections

Annotations

Publishing

Research

Users

Workflows

They should never expose internal database structures.

---

## Internal APIs

Even modules inside the modular monolith communicate through explicit application interfaces.

This prepares future service extraction.

---

## Examples

### Good

OpenAPI before coding.

Stable contracts.

Versioned endpoints.

Consumer-driven testing.

---

### Bad

Database-first APIs.

Controllers exposing entities.

Breaking changes.

Hidden contracts.

---

## Anti-patterns

CRUD-first Design

Database Leakage

Undocumented APIs

Implementation-driven Contracts

---

## Implementation Impact

Backend

Contract-first development.

Frontend

Generated API clients.

AI Platform

Consumes backend contracts rather than databases.

Architecture

Loose coupling between domains.

---

## Related Principles

Open Standards

Technology Independent

Event Driven

---

## Decision Checklist

Before implementing a feature ask:

* Does the API exist?
* Does it represent a business capability?
* Is the contract stable?
* Can another client consume it?

---

# Principle 24 — Event Driven

---

## Statement

Business state changes should be communicated through immutable domain events.

Events describe what happened.

Consumers decide what to do next.

---

## Motivation

The platform contains numerous independent capabilities:

Editorial

Knowledge

Search

AI

Graph

Embeddings

Analytics

Notifications

Tightly coupling them would reduce scalability and maintainability.

Events create loose coupling.

---

## Events Represent Facts

Examples:

StoryCreated

TranscriptGenerated

KnowledgeExtracted

ArticlePublished

EmbeddingCreated

KnowledgeApproved

Events are historical facts.

They never change after publication.

---

## Events Are Business Language

Events describe business meaning.

Not technical implementation.

Good:

StoryPublished

Bad:

DatabaseUpdated

---

## Asynchronous By Default

Long-running processes should execute asynchronously.

Examples:

Embedding generation.

AI extraction.

Graph projection.

Analytics.

Notifications.

---

## Examples

### Good

Redpanda.

Kafka-compatible events.

Immutable payloads.

Event replay.

Idempotent consumers.

---

### Bad

Synchronous service chains.

Shared databases.

Direct table polling.

Hidden dependencies.

---

## Anti-patterns

RPC Everywhere

Database Integration

Mutable Events

Technical Event Names

---

## Implementation Impact

Backend

Domain events become first-class citizens.

AI Platform

Entire platform driven by queues.

Frontend

Receives asynchronous updates.

Analytics

Consumes event streams.

---

## Related Principles

API First

Technology Independent

Long-term Thinking

---

## Decision Checklist

Before integrating two modules ask:

* Can an event replace direct coupling?
* Is the event immutable?
* Does it describe business meaning?
* Can new consumers subscribe without modifying the producer?

---

# Principle 25 — Technology Independent

---

## Statement

Business domains must never depend on specific technologies.

Frameworks, databases, AI providers, messaging systems, and deployment platforms are implementation details.

The domain remains independent.

---

## Motivation

Technology changes continuously.

Knowledge does not.

Architecture should therefore isolate technology behind stable abstractions.

Business rules should survive technology replacement.

---

## Technology Is Replaceable

Examples:

Spring Boot → Future JVM Framework

React → Future UI Framework

PostgreSQL → Another SQL Database

Redpanda → Kafka

Weaviate → Alternative Vector Database

OpenAI → Another AI Provider

Business workflows remain unchanged.

---

## Dependency Direction

Dependencies always point inward.

Infrastructure depends on domains.

Domains never depend on infrastructure.

This preserves architectural integrity.

---

## Examples

### Good

Ports and adapters.

Repository interfaces.

Provider abstractions.

Domain services.

---

### Bad

Spring annotations inside domain models.

Vendor SDKs inside business logic.

Database-specific domain rules.

AI provider APIs embedded in workflows.

---

## Anti-patterns

Framework-driven Domains

Vendor-specific Business Logic

Infrastructure Leakage

Technology-centric Architecture

---

## Implementation Impact

Backend

DDD boundaries remain clean.

Frontend

Business logic independent of UI framework.

AI Platform

Provider adapters isolate external models.

Infrastructure

Technology replacement becomes operational rather than architectural.

---

## Related Principles

Long-term Thinking

Open Standards

API First

Event Driven

Model Agnostic

---

## Decision Checklist

Before introducing any dependency ask:

* Does the domain know about this technology?
* Can it be replaced later?
* Is there an abstraction boundary?
* Will business logic remain unchanged after replacement?

If the answer is no, the dependency should be redesigned.

---

# Culture Principles

The Living Atlas exists to preserve, understand, and connect human cultures.

Culture is not merely content.

It is memory.

Identity.

Language.

Tradition.

Belief.

Practice.

History.

Community.

Unlike entertainment platforms that optimize for engagement, The Living Atlas treats culture as knowledge that deserves careful preservation and responsible representation.

These principles guide how cultural information is collected, interpreted, reviewed, and presented.

---

# Principle 26 — Culture Before Entertainment

---

## Statement

The primary purpose of cultural content is understanding, preservation, and education.

Entertainment may emerge naturally from storytelling, but it must never become the driving objective.

Culture should never be simplified, distorted, or sensationalized solely to increase engagement.

---

## Motivation

Modern digital platforms frequently reward:

clicks,

watch time,

shares,

virality,

and emotional reactions.

As a result, cultural narratives are often exaggerated, romanticized, or stripped of historical complexity.

The Living Atlas intentionally rejects this optimization model.

Stories should remain engaging because they are meaningful, not because they are manipulated for attention.

---

## Authenticity Before Virality

When editorial decisions require choosing between:

greater engagement

or

greater authenticity,

authenticity always wins.

A historically accurate explanation with moderate engagement is preferable to a sensational narrative that spreads misinformation.

---

## Storytelling Is A Teaching Tool

Narrative remains important.

Stories help readers remember knowledge.

However, storytelling serves understanding.

It does not replace evidence.

Every narrative should remain connected to:

historical context,

supporting evidence,

related knowledge,

and cultural meaning.

---

## Cultural Integrity

Editorial decisions should preserve:

traditional terminology,

regional variation,

ritual meaning,

historical chronology,

and original context.

Necessary simplifications for readability should never alter meaning.

---

## Examples

### Good

Explaining cultural practices respectfully.

Presenting myths with historical context.

Separating folklore from historical evidence.

Retaining original terminology.

---

### Bad

Clickbait titles.

Sensational headlines.

Misleading thumbnails.

Artificial controversy.

Exaggerated historical claims.

---

## Anti-patterns

Culture As Marketing

History As Entertainment

Engagement Above Accuracy

Narrative Without Context

---

## Implementation Impact

### Product

Success metrics include learning and understanding rather than only engagement.

---

### Frontend

Reading experiences prioritize clarity over visual spectacle.

---

### Backend

Editorial workflows require evidence before publication.

---

### AI Platform

Generation prompts avoid sensational language and preserve cultural nuance.

---

## Related Principles

Knowledge First

Evidence Before Opinion

Preserve Context

Community Respect

---

## Decision Checklist

Before publishing cultural content ask:

* Does this improve understanding?
* Does it preserve authenticity?
* Would community members recognize their own culture fairly?
* Is entertainment overshadowing education?

If the answer is yes to the last question, redesign the content.

---

# Principle 27 — Preserve Context

---

## Statement

Knowledge should never be separated from the cultural, historical, geographical, linguistic, and social context that gives it meaning.

Facts without context become misinformation.

Stories without context become fiction.

Culture without context becomes stereotype.

---

## Motivation

Many cultural misunderstandings arise because traditions are presented in isolation.

For example:

A ritual without its belief system.

A legend without its historical period.

A proverb without its language.

A dance without its ceremonial role.

Removing context may simplify presentation, but it also removes meaning.

---

## Dimensions Of Context

Every significant knowledge object should preserve relevant context including:

Historical.

Geographical.

Cultural.

Religious.

Linguistic.

Political.

Social.

Editorial.

Relationship context.

Not every dimension applies equally, but the platform should record as much context as is responsibly available.

---

## Context Travels With Knowledge

Whenever knowledge is reused, exported, summarized, translated, or cited, essential contextual information should remain attached.

Summaries should compress content, not erase meaning.

---

## AI Must Preserve Context

AI pipelines should extract and maintain contextual metadata rather than generating isolated facts.

Generated summaries should explicitly retain:

location,

time period,

community,

sources,

and confidence.

---

## Examples

### Good

Showing historical periods.

Displaying regional variations.

Explaining ceremonial purpose.

Linking related traditions.

Including linguistic origin.

---

### Bad

Publishing isolated facts.

Removing historical timelines.

Ignoring regional diversity.

Flattening cultural complexity.

---

## Anti-patterns

Context Stripping

Universal Assumptions

Historical Compression

Meaning Reduction

---

## Implementation Impact

### Product

Knowledge objects include contextual metadata by default.

---

### Backend

Canonical schemas preserve contextual relationships.

---

### AI Platform

Extraction pipelines prioritize contextual preservation.

---

### Database

Context becomes part of the canonical model rather than optional metadata.

---

## Related Principles

Culture Before Entertainment

Respect Multiple Perspectives

Knowledge First

---

## Decision Checklist

Before simplifying knowledge ask:

* What context is being removed?
* Will the remaining information still be accurate?
* Could readers misunderstand this without additional explanation?
* Does the summary preserve cultural meaning?

---

# Principle 28 — Respect Multiple Perspectives

---

## Statement

The Living Atlas acknowledges that many cultural subjects legitimately have multiple interpretations.

The platform should preserve these perspectives whenever credible evidence exists, rather than forcing artificial consensus.

---

## Motivation

Culture evolves through communities, histories, and lived experiences.

Different regions may tell different versions of the same legend.

Researchers may disagree on historical interpretation.

Communities may preserve distinct oral traditions.

These differences are valuable knowledge rather than editorial problems.

The role of the platform is to document and explain them responsibly.

---

## Diversity Of Interpretation

Multiple perspectives may arise from:

Regional traditions.

Academic disagreement.

Religious interpretation.

Historical evidence.

Oral narratives.

Linguistic variation.

Generational practice.

Each perspective should be clearly identified and supported with its own evidence.

---

## Distinguish Difference From Error

Not every disagreement represents misinformation.

Editors should distinguish between:

Evidence-supported alternative interpretations.

Unsupported factual errors.

The platform preserves the former while correcting the latter.

---

## Examples

### Good

Displaying several documented origin stories.

Explaining competing academic theories.

Labeling community-specific practices.

---

### Bad

Removing minority perspectives without justification.

Presenting one interpretation as universally accepted.

Merging conflicting traditions into a single narrative.

---

## Anti-patterns

Forced Consensus

Editorial Centralization

Historical Monoculture

Perspective Suppression

---

## Implementation Impact

### Product

Knowledge pages support multiple interpretations with explicit attribution.

---

### Backend

Claims, interpretations, and evidence remain independently versioned.

---

### AI Platform

Models summarize multiple viewpoints without collapsing them into one.

---

## Related Principles

Evidence Before Opinion

Transparency

No Canonical Bias

Community Respect

---

## Decision Checklist

Before resolving conflicting information ask:

* Are multiple credible perspectives available?
* Can they coexist?
* Is one interpretation being favored without evidence?
* Have community perspectives been represented fairly?

---

# Principle 29 — No Canonical Bias

---

## Statement

Canonical knowledge within The Living Atlas represents structured, evidence-backed knowledge—not official truth.

The platform must avoid privileging a single culture, institution, region, language, ideology, or editorial preference unless evidence clearly requires it.

---

## Motivation

Canonical structure exists to organize knowledge.

It does not exist to establish cultural superiority.

A canonical identifier is a technical necessity.

It is not a declaration that one tradition is more legitimate than another.

The platform distinguishes between:

canonical structure,

and

canonical interpretation.

Only the former exists.

---

## Canonical Structure

The platform maintains canonical identifiers for:

stories,

people,

places,

motifs,

themes,

cultures,

languages,

rituals,

and events.

Alternative names, spellings, regional variants, and interpretations remain connected to the same knowledge graph where appropriate.

---

## Neutral Editorial Position

Editors should describe evidence rather than advocate cultural positions.

Editorial neutrality does not require false balance.

Unsupported claims should not receive equal treatment with well-supported evidence.

However, evidence-backed minority perspectives should remain visible.

---

## Examples

### Good

Recording regional names.

Linking alternative traditions.

Displaying confidence levels.

Documenting disagreement.

---

### Bad

Declaring one community's tradition as universally correct without evidence.

Deleting minority traditions.

Treating editorial preference as historical fact.

---

## Anti-patterns

Editorial Absolutism

Institutional Bias

Majority Bias

Language Bias

---

## Implementation Impact

### Product

Knowledge pages distinguish canonical entities from competing interpretations.

---

### Backend

Entity identity remains separate from claims about the entity.

---

### AI Platform

Generation prompts explicitly preserve competing evidence and regional terminology.

---

## Related Principles

Respect Multiple Perspectives

Evidence Before Opinion

Transparency

Knowledge First

---

## Decision Checklist

Before declaring something canonical ask:

* Is this a canonical identifier or a canonical interpretation?
* Does evidence justify prioritization?
* Are alternative perspectives still discoverable?
* Could users mistake technical canonicalization for cultural endorsement?

---

# Principle 30 — Community Respect

---

## Statement

Communities are not merely sources of information.

They are living custodians of culture.

The Living Atlas should collaborate with communities respectfully, acknowledge their contributions, and represent their knowledge with dignity and accountability.

---

## Motivation

Many knowledge platforms extract cultural information from communities without meaningful recognition, consultation, or feedback.

This weakens trust and risks misrepresentation.

The Living Atlas seeks a collaborative relationship in which communities remain participants in preserving their own heritage rather than passive subjects of documentation.

---

## Communities As Partners

Where practical, communities should be able to:

contribute knowledge,

suggest corrections,

provide contextual information,

review representations,

and preserve local terminology.

Editorial authority remains necessary, but it should be exercised transparently and respectfully.

---

## Respect Includes Attribution

Whenever appropriate, the platform should preserve:

community names,

traditional terminology,

local spellings,

oral contributors,

research collaborators,

and provenance.

Recognition strengthens trust and historical accountability.

---

## Sensitive Cultural Knowledge

Some cultural knowledge may be:

sacred,

restricted,

ceremonial,

or community-specific.

Not every piece of knowledge should be published simply because it can be documented.

Editorial teams should consider ethical, legal, and cultural implications before publication.

---

## Examples

### Good

Acknowledging community contributors.

Respecting traditional terminology.

Providing channels for corrections.

Recording provenance.

Consulting local experts.

---

### Bad

Extracting knowledge without attribution.

Ignoring community feedback.

Publishing culturally sensitive material without consideration.

Renaming traditions for marketing purposes.

---

## Anti-patterns

Knowledge Extraction Without Recognition

Cultural Appropriation

Editorial Colonialism

Community Erasure

---

## Implementation Impact

### Product

Contribution workflows support community participation and feedback.

---

### Backend

Community attribution, contributor metadata, and provenance become first-class entities.

---

### AI Platform

AI respects community terminology and avoids normalizing culturally significant expressions into generic language.

---

## Related Principles

Culture Before Entertainment

Preserve Context

Respect Multiple Perspectives

Transparency

Human Review

---

## Decision Checklist

Before publishing cultural knowledge ask:

* Have affected communities been represented fairly?
* Is attribution preserved?
* Could publication unintentionally cause cultural harm?
* Does the platform respect community terminology and context?
* Would community members recognize this representation as accurate and respectful?

If any answer raises significant concern, the content should undergo additional editorial review before publication.
