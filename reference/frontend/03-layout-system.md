# Layout System

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Product Design Team

Last Updated: June 2026

---

# Purpose

This document defines the layout architecture used across every application within The Living Atlas.

The objective is to create a layout system that feels calm, predictable, scalable, and capable of presenting extremely dense knowledge without overwhelming users.

The layout should disappear into the background, allowing knowledge itself to become the primary focus.

Unlike visual styling, the layout system defines how space is organized and how users move their attention through the interface.

---

# Design Philosophy

The layout should never compete with content.

The layout should guide attention naturally.

Good layout is almost invisible.

Users should immediately understand:

- Where they are
- What is most important
- What can be done
- Where to go next

without conscious effort.

---

# Layout Hierarchy

Every screen follows the same hierarchy.

```
Application

↓

Page

↓

Section

↓

Container

↓

Content Block

↓

Component

↓

Primitive
```

Each layer has exactly one responsibility.

---

# Application Shell

Every application shares the same shell.

```
┌─────────────────────────────────────────────────────────────┐
│ Global Header                                               │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│ Left Nav     │                Main Content                  │
│              │                                              │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│ Context Panel│                                              │
└──────────────┴──────────────────────────────────────────────┘
```

This shell never changes.

Only the content changes.

---

# Global Header

Height

72px

Contains:

- Logo
- Search
- Primary Navigation
- Notifications
- Bookmarks
- User Menu

The header always remains visible.

---

# Left Navigation

Purpose:

Global navigation.

Contains:

Stories

Knowledge

Atlas

Timeline

Cultures

Regions

Creators

Research

Collapsed Width

72px

Expanded Width

280px

Navigation should support both modes.

---

# Main Content

Maximum Width

1440px

Reading Width

760px

Research Width

Full Width

The layout adapts to content.

Narrative pages prioritize readability.

Research pages prioritize information density.

---

# Context Panel

Purpose

Contextual exploration.

Examples

Related Stories

Knowledge Objects

Timeline

Evidence

AI Suggestions

Graph Summary

Desktop Width

360px

Tablet

Drawer

Mobile

Bottom Sheet

---

# Page Layout Types

The Living Atlas defines several canonical layouts.

---

## Layout A

Narrative

```
Header

↓

Hero

↓

Story

↓

Related Knowledge

↓

Related Stories

↓

Footer
```

Optimized for reading.

---

## Layout B

Knowledge Detail

```
Hero

↓

Overview

↓

Relationships

↓

Evidence

↓

Timeline

↓

Sources
```

Optimized for understanding.

---

## Layout C

Atlas

```
Map

↓

Knowledge Panel

↓

Relationship Panel

↓

Timeline
```

Optimized for exploration.

---

## Layout D

Research Workspace

```
Toolbar

↓

Graph

↓

Inspector

↓

Evidence

↓

Notes
```

Optimized for productivity.

---

## Layout E

Editorial Workspace

```
Queue

↓

Review Panel

↓

Comparison

↓

Approval
```

Optimized for decision making.

---

# Grid System

Desktop

12 Columns

Tablet

8 Columns

Mobile

4 Columns

All spacing should derive from a single spacing scale.

---

# Spacing Scale

```
4
8
12
16
24
32
40
48
64
80
96
128
```

No arbitrary spacing values.

---

# Reading Width

Reading comfort takes precedence.

Maximum narrative width:

760px

Knowledge cards:

900px

Research layouts:

Fluid

Long text should never exceed optimal reading width.

---

# White Space

Whitespace communicates hierarchy.

Never fill empty space simply because it exists.

Whitespace improves comprehension.

---

# Section Structure

Every section follows:

```
Title

↓

Description (optional)

↓

Primary Content

↓

Actions

↓

Metadata
```

Consistency reduces cognitive load.

---

# Hero Section

Every major detail page begins with a hero.

Contains:

Title

Summary

Metadata

Primary Actions

Quick Facts

Hero sections establish context immediately.

---

# Sidebar Philosophy

Sidebars should provide context, not distractions.

Good sidebar content:

Related entities

Timeline

Evidence

Sources

Collections

Bookmarks

Avoid advertisements or unrelated widgets.

---

# Sticky Elements

Allowed sticky elements:

Header

Context Panel

Research Toolbar

Search

Table Headers

Avoid excessive sticky UI.

---

# Responsive Behavior

Desktop

Three-column layouts.

Tablet

Two-column layouts.

Mobile

Single-column layouts.

No functionality should disappear.

Only presentation changes.

---

# Empty States

Every empty state should explain:

Why it is empty.

How to populate it.

What the user can do next.

---

# Loading States

Use skeleton loading.

Avoid generic spinners whenever possible.

Loading should preserve layout stability.

---

# Error States

Errors should be contextual.

Include:

Problem

Explanation

Recovery Action

Support Link (if needed)

---

# Scroll Behavior

Narrative

Single vertical scroll.

Research

Independent scroll regions where appropriate.

Graph

Pan and zoom.

Timeline

Horizontal + vertical.

Scrolling behavior should match user expectations.

---

# Motion

Motion should communicate spatial relationships.

Examples:

Panel expansion

Node highlighting

Timeline transitions

Avoid decorative animation.

---

# Layout Consistency

Every application should feel familiar.

Users switching from:

Atlas

↓

Research

↓

Admin

should immediately recognize:

Navigation

Spacing

Panels

Toolbar

Interactions

Consistency builds confidence.

---

# Future Expansion

The layout system must support future applications without redesign.

Potential additions include:

Museum Mode

Interactive Wall Displays

Mobile Apps

Desktop Applications

Educational Portals

Digital Exhibitions

The shell remains stable while content evolves.

---

# Guiding Principle

A successful layout is one that users stop noticing.

When users focus entirely on the stories, knowledge, and cultural connections—not the interface itself—the layout has achieved its purpose.