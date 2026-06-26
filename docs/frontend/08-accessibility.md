# Accessibility

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Frontend Platform Team

Last Updated: June 2026

---

# Purpose

Accessibility ensures that every person can meaningfully access, understand, and interact with The Living Atlas.

Accessibility extends beyond technical compliance.

The platform must make Indonesian mystery culture accessible to diverse audiences while preserving scholarly integrity and cultural nuance.

Accessibility in The Living Atlas is built upon three equally important dimensions:

- Human Accessibility
- Knowledge Accessibility
- Cultural Accessibility

---

# Vision

Every user should be able to explore, understand, and contribute to cultural knowledge regardless of:

- Physical ability
- Cognitive ability
- Language proficiency
- Technical expertise
- Academic background
- Device
- Internet quality

Accessibility is a product philosophy, not a compliance checklist.

---

# Accessibility Principles

## Inclusive by Default

Accessibility is designed into every feature from the beginning.

It is never treated as an enhancement after implementation.

---

## Equal Knowledge

Every user should have access to the same knowledge.

Presentation may change.

Knowledge does not.

---

## Multiple Ways to Learn

Different users learn differently.

Every important concept should be understandable through more than one representation.

Examples:

- Text
- Diagram
- Timeline
- Relationship Graph
- Audio (future)
- Visual Summary (future)

---

## Progressive Complexity

Knowledge should unfold gradually.

A casual reader and a researcher should both find value on the same page.

Users choose how deeply they explore.

---

# Human Accessibility

The platform targets conformance with **WCAG 2.2 AA** as the baseline.

Where practical, AAA techniques may be adopted for reading experiences.

---

# Keyboard Navigation

Every interactive element must be reachable using only the keyboard.

Required capabilities:

- Logical tab order
- Visible focus indicator
- Skip navigation links
- Keyboard shortcuts
- Modal focus trapping
- Escape key support

No workflow should require a mouse.

---

# Screen Reader Support

Every page must expose semantic structure.

Use proper HTML landmarks:

- header
- nav
- main
- aside
- footer

Interactive controls require:

- Accessible names
- ARIA roles where appropriate
- Meaningful labels
- Descriptive status messages

Avoid unnecessary ARIA when native HTML semantics are sufficient.

---

# Typography

Text should remain readable under:

- 200% browser zoom
- Large operating system fonts
- High DPI displays

Avoid fixed-height text containers.

Recommended:

- Minimum body size: 16 px
- Comfortable line length: 60–75 characters
- Line height: 1.5–1.8

---

# Color and Contrast

Color must never be the only means of conveying information.

Contrast ratios:

- Normal text ≥ 4.5:1
- Large text ≥ 3:1
- Interactive controls ≥ 3:1

Charts, graphs, and maps must remain understandable without relying solely on color.

---

# Motion

Respect the user's operating system preference for reduced motion.

Reduce or disable:

- Background animation
- Continuous movement
- Decorative transitions
- Automatic zoom effects

Motion should communicate structure, not decoration.

---

# Touch Accessibility

Interactive targets should be at least:

44 × 44 px

Spacing should prevent accidental activation.

---

# Knowledge Accessibility

Knowledge should be understandable without requiring specialist expertise.

---

## Layered Reading

Every article should provide multiple reading depths.

### Level 1 — Quick Summary

A concise overview in plain language.

### Level 2 — Standard Reading

Complete narrative or knowledge article.

### Level 3 — Deep Exploration

Evidence, relationships, citations, and historical context.

Users decide how deeply to engage.

---

## Explain Terminology

Specialized cultural terms should include inline explanations.

Example:

```
Ruwatan

Traditional Javanese purification ritual.

Learn More →
```

Definitions should not interrupt reading flow.

---

## Visual Knowledge

Whenever appropriate, accompany complex concepts with visual representations.

Examples:

- Timelines
- Relationship diagrams
- Geographic distribution
- Knowledge cards

Visuals complement, not replace, text.

---

## Reading Assistance

Support:

- Reading progress
- Estimated reading time
- Bookmarking
- Highlighting
- Adjustable font size
- Reading mode

Future enhancements:

- Text-to-speech
- Simplified reading mode

---

# Cultural Accessibility

The platform documents living traditions.

It must respect diversity of interpretation.

---

## Multiple Perspectives

Present regional or cultural variations separately.

Example:

```
West Java

...

Central Java

...

East Java

...
```

Do not merge distinct traditions into a single explanation.

---

## Evidence Transparency

Distinguish clearly between:

- Transcript-derived information
- Editorial synthesis
- Historical documentation
- Academic interpretation
- AI-generated assistance

Readers should always understand the origin of information.

---

## Neutral Language

Avoid presenting supernatural claims as established facts.

Prefer language such as:

- "According to..."
- "In this tradition..."
- "This investigation reports..."
- "The creator describes..."

The platform documents beliefs rather than validates them.

---

# Atlas Accessibility

The Atlas must remain usable without relying on complex visual interaction.

Support:

- Keyboard navigation
- Search-first navigation
- Relationship lists
- Inspector summaries
- Alternative textual views

Every graph interaction should have an equivalent accessible representation.

---

# AI Discovery Accessibility

AI Discovery should support:

- Structured responses
- Clearly labeled citations
- Expandable sections
- Keyboard navigation
- Screen reader compatibility

Responses should avoid overly dense paragraphs.

---

# Multimedia Accessibility

Videos

- Captions
- Transcript
- Speaker identification (where available)

Audio

- Transcript
- Timestamps

Images

- Descriptive alternative text

Interactive visualizations

- Accessible summaries

---

# Cognitive Accessibility

Reduce unnecessary cognitive load.

Support:

- Consistent navigation
- Predictable layouts
- Plain-language summaries
- Progressive disclosure
- Stable interface behavior

Avoid:

- Unexpected modal dialogs
- Excessive animation
- Information overload

---

# Language Accessibility

Future support includes:

- Indonesian
- English

The architecture should support additional regional languages without redesign.

Where possible, preserve original cultural terminology alongside translations.

---

# Error Accessibility

Error messages should explain:

- What happened
- Why it happened (if known)
- How to recover

Avoid vague messages such as:

```
Unknown Error
```

---

# Offline Considerations

When connectivity is poor:

- Preserve reading progress
- Cache recently viewed articles
- Display meaningful offline states

Knowledge should remain accessible whenever practical.

---

# Testing Strategy

Accessibility testing includes:

Manual testing

Keyboard-only navigation

Screen reader testing

Automated accessibility auditing

Color contrast verification

Responsive accessibility validation

Real-user testing with assistive technologies

Accessibility should be verified throughout development, not only before release.

---

# Accessibility Metrics

Monitor:

Keyboard completion rate

Screen reader compatibility issues

Contrast violations

Accessibility audit score

Reading completion rate

Average reading depth

Search success rate

Accessibility is measured by successful knowledge access, not merely technical compliance.

---

# Future Vision

Future accessibility capabilities include:

Voice navigation

Text-to-speech

Speech-to-text search

Adaptive reading assistance

Museum accessibility modes

Educational accessibility profiles

Personalized reading preferences

AI-assisted explanation levels

The platform should evolve as accessibility technologies improve.

---

# Guiding Principle

Accessibility means ensuring that every person can meaningfully engage with Indonesian mystery culture.

The goal is not simply to meet technical standards, but to remove barriers to understanding while preserving the richness, diversity, and authenticity of the knowledge being shared.

An accessible Living Atlas is one where every user—regardless of ability, background, or expertise—can discover, learn, and contribute with confidence.