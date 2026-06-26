# Responsive System

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Frontend Platform Team

Last Updated: June 2026

---

# Purpose

This document defines how The Living Atlas adapts across devices, screen sizes, input methods, and usage contexts.

Responsive design is not merely about resizing layouts.

The platform should optimize the experience for the user's intent, available space, and interaction capabilities.

The same knowledge should be accessible everywhere.

Only the presentation changes.

---

# Design Philosophy

Traditional responsive design asks:

> "How do we fit this page onto a smaller screen?"

The Living Atlas asks:

> "How should this knowledge be experienced on this device?"

Every adaptation should improve usability rather than simply reduce content.

---

# Guiding Principles

## Knowledge is Constant

Knowledge objects never disappear because of screen size.

A Story remains a Story.

An Entity remains an Entity.

A Relationship remains a Relationship.

Only the visual representation changes.

---

## Adapt, Don't Remove

Incorrect

Desktop

```
Graph

Timeline

Evidence

Inspector
```

Mobile

```
Graph removed
```

Correct

Desktop

```
Graph
```

↓

Mobile

```
Graph Preview

↓

Full Screen Graph
```

Capabilities should move—not disappear.

---

## Mobile is Not a Reduced Product

The mobile experience should provide complete access to the platform.

Certain advanced workflows may require additional interactions, but no core knowledge should be inaccessible.

---

# Responsive Breakpoints

The platform defines semantic breakpoints rather than device names.

| Name     |        Width |
| -------- | -----------: |
| Compact  |     0–639 px |
| Medium   |  640–1023 px |
| Expanded | 1024–1439 px |
| Wide     | 1440–1919 px |
| Ultra    |     ≥1920 px |

Layouts respond to available space rather than assumed hardware.

---

# Adaptive Modes

The platform supports distinct interaction modes.

## Reading Mode

Optimized for long-form narrative.

Characteristics:

* Narrow reading column
* Large typography
* Minimal distractions
* Sticky progress indicator
* Inline citations
* Context drawer on demand

---

## Discovery Mode

Optimized for exploration.

Characteristics:

* Multi-panel layout
* Persistent search
* Inspector panel
* Relationship suggestions
* AI Discovery panel

---

## Atlas Mode

Optimized for visual navigation.

Characteristics:

* Large canvas
* Floating inspector
* Layer controls
* Zoom controls
* Progressive graph expansion

---

## Research Mode

Optimized for productivity.

Characteristics:

* Dense information
* Multiple synchronized panels
* Resizable workspace
* Keyboard shortcuts
* Multi-selection
* Persistent filters

---

## Editorial Mode

Optimized for review.

Characteristics:

* Queue-first workflow
* Comparison panels
* Approval controls
* Audit visibility
* AI extraction review

---

# Screen Adaptation

## Compact

Single column.

Navigation:

Bottom navigation.

Context:

Bottom sheet.

Atlas:

Preview + fullscreen.

Timeline:

Scrollable cards.

Tables:

Card layout.

Inspector:

Fullscreen modal.

---

## Medium

Two-column layout where appropriate.

Sidebar:

Collapsible.

Inspector:

Slide-over.

Atlas:

Reduced toolset.

Timeline:

Hybrid list.

---

## Expanded

Three-column layout.

Sidebar:

Persistent.

Inspector:

Persistent.

Atlas:

Standard workspace.

Research:

Split panels.

---

## Wide

Optimized workspace.

Additional capabilities:

Pinned inspector.

Secondary timeline.

AI Discovery panel.

Multi-selection.

Graph comparison.

---

## Ultra

Professional workspace.

Possible layout:

```
Navigation

↓

Canvas

↓

Inspector

↓

Timeline

↓

AI Discovery

↓

Evidence
```

Ultra-wide displays maximize simultaneous context rather than enlarging individual elements.

---

# Navigation Adaptation

Desktop

Global sidebar.

Tablet

Collapsible sidebar.

Mobile

Bottom navigation.

Research tools may expose additional floating actions.

---

# Search Adaptation

Desktop

Persistent global search.

Tablet

Expandable search.

Mobile

Fullscreen search experience.

Search quality remains identical.

---

# Atlas Adaptation

Desktop

Canvas + inspector + filters.

Tablet

Canvas + drawer.

Mobile

Canvas fullscreen.

Inspector becomes a bottom sheet.

Node interactions become touch-friendly.

---

# Timeline Adaptation

Desktop

Horizontal timeline.

Tablet

Hybrid timeline.

Mobile

Vertical timeline.

Timeline semantics remain identical.

---

# Tables

Desktop

Traditional table.

Tablet

Scrollable table.

Mobile

Responsive cards.

Users retain access to every field.

---

# Knowledge Cards

Cards adapt progressively.

Compact

Title

Summary

Type

Expanded

Metadata

Evidence count

Relationships

Actions

Wide

Additional previews.

Cards grow richer with available space.

---

# Forms

Desktop

Multi-column.

Mobile

Single-column.

Field ordering never changes.

Validation remains consistent.

---

# AI Discovery Panel

Desktop

Persistent right panel.

Tablet

Slide-over.

Mobile

Dedicated screen.

Conversation context remains synchronized across devices.

---

# Media

Images

Scale proportionally.

Videos

Responsive aspect ratio.

Audio

Persistent player.

Transcript

Adaptive synchronized reader.

Media should never overflow containers.

---

# Gestures

Touch devices support:

Tap

Double tap

Long press

Pinch

Pan

Swipe

Desktop interactions remain keyboard and pointer friendly.

---

# Keyboard Support

All desktop experiences remain fully operable without a mouse.

Essential shortcuts:

Search

Navigation

Bookmarks

Collections

Atlas controls

Timeline controls

Workspace switching

---

# Orientation

Landscape

Workspace-first.

Portrait

Reading-first.

Orientation changes should preserve application state.

---

# Accessibility Adaptation

Support:

Large text

Reduced motion

High contrast

Screen readers

Keyboard-only navigation

Touch targets ≥44 px

Accessibility preferences persist across devices.

---

# Performance Budgets

Compact

Initial load <1.5 s

Expanded

<2 s

Atlas

Interactive within 2 s

AI Discovery

Ready within 2 s

Performance targets apply independently of screen size.

---

# State Preservation

Changing screen size should never discard:

Current page

Search query

Selected object

Graph expansion

Timeline position

Workspace filters

Reading position

Users should continue seamlessly.

---

# Future Platforms

The responsive system anticipates:

Foldable devices

Desktop applications

Museum kiosks

Interactive walls

Large touch displays

Smart TVs

AR/VR interfaces

Vehicle infotainment systems

Each platform reuses the same information architecture.

---

# Anti-Patterns

Avoid:

Horizontal scrolling for primary content

Hidden functionality

Hover-only interactions

Tiny touch targets

Unexpected layout jumps

Feature discrepancies between devices

Responsive design should never compromise understanding.

---

# Guiding Principle

Responsive design is not about shrinking interfaces.

It is about preserving understanding across every environment.

Whether a user is reading a story on a phone, researching folklore on an ultra-wide monitor, or exploring cultural relationships in a museum installation, they should feel they are using the same Living Atlas—adapted to their context, not diminished by it.
