# Atlas Experience

**Project**

The Living Atlas of Indonesian Mystery Culture

Version: 1.0

Status: Draft

Owner: Product Design Team

Last Updated: June 2026

---

# Purpose

The Atlas is the signature experience of The Living Atlas.

Unlike traditional maps, graphs, or archives, the Atlas provides an interactive environment where users explore the relationships between stories, beliefs, rituals, cultures, regions, historical events, and creators.

The Atlas is not a visualization.

It is a mode of exploration.

Users should feel as though they are travelling through an interconnected cultural landscape rather than browsing a database.

---

# Product Vision

Traditional websites answer questions.

The Atlas inspires new questions.

Instead of presenting isolated articles, the Atlas continuously reveals hidden relationships that encourage curiosity.

Every interaction should naturally lead to another discovery.

---

# Design Philosophy

The Atlas should feel:

- Calm
- Elegant
- Immersive
- Exploratory
- Trustworthy
- Scholarly
- Human

The interface should disappear behind the knowledge.

Technology should never become the center of attention.

---

# User Goals

The Atlas serves different audiences with different intentions.

Reader

- Discover interesting stories
- Explore folklore
- Learn cultural context

Researcher

- Identify relationships
- Compare evidence
- Analyze regional patterns

Creator

- Find inspiration
- Explore themes
- Discover motifs
- Build fictional worlds

Anthropologist

- Study traditions
- Compare interpretations
- Trace cultural evolution

Production House

- Research locations
- Identify authentic references
- Explore historical context

---

# Core Navigation Model

Users may begin exploration from any knowledge object.

Examples:

Story

↓

Related Entity

↓

Culture

↓

Belief

↓

Timeline

↓

Historical Event

↓

Another Story

or

Region

↓

Tradition

↓

Spirit

↓

Investigation

↓

Creator

↓

Podcast Episode

There is no single "correct" path.

---

# Atlas Modes

The Atlas supports multiple exploration modes.

---

## Relationship Mode

Default mode.

Displays connections between knowledge objects.

Objects:

Stories

Entities

Cultures

Beliefs

Regions

Creators

Artifacts

Historical Events

Connections represent explicit knowledge graph relationships.

---

## Geographic Mode

Explores cultural knowledge through geography.

Users may navigate:

Island

↓

Province

↓

City

↓

District

↓

Village

↓

Story

↓

Knowledge

Sensitive locations remain protected.

The platform may intentionally reduce precision.

---

## Timeline Mode

Explores knowledge through time.

Examples:

Historical Event

↓

Traditional Belief

↓

Modern Investigation

↓

Podcast Episode

↓

Current Interpretation

Users understand cultural evolution.

---

## Theme Mode

Groups stories by themes.

Examples:

Abandoned Buildings

Sacred Forests

Possession

Ancestor Worship

Dreams

Water Spirits

Mountain Spirits

Users discover recurring narratives.

---

## Culture Mode

Explores cultural traditions.

Example

Sundanese

↓

Traditional Beliefs

↓

Rituals

↓

Entities

↓

Stories

↓

Creators

Knowledge is organized around cultural identity.

---

## Creator Mode

Explores creators.

Example

Creator

↓

Videos

↓

Stories

↓

Regions

↓

Collaborators

↓

Recurring Themes

↓

Influence Network

Creators become knowledge hubs.

---

## Investigation Mode

Focuses on documented investigations.

Users explore:

Investigation

↓

Evidence

↓

Witnesses

↓

Transcript

↓

Knowledge Extraction

↓

Published Story

This mode emphasizes provenance.

---

# Atlas Layout

Desktop

```
┌─────────────────────────────────────────────────────────────┐
│ Header                                                      │
├─────────────────────────────────────────────────────────────┤
│ Search                                                      │
├───────────────┬──────────────────────────────┬──────────────┤
│ Filters       │                              │ Inspector    │
│               │                              │              │
│               │      Atlas Canvas            │ Relationships│
│               │                              │ Timeline     │
│               │                              │ Evidence     │
├───────────────┴──────────────────────────────┴──────────────┤
│ Bottom Context Bar                                          │
└─────────────────────────────────────────────────────────────┘
```

---

# Atlas Canvas

The canvas is infinite.

Users may:

Pan

Zoom

Expand

Collapse

Focus

Bookmark

Compare

Inspect

Reset

The canvas behaves like a workspace rather than a page.

---

# Knowledge Cards

Every object appears as a rich card.

Example:

Story

- Title
- Summary
- Region
- Related Culture
- Relationship Count
- Evidence Count

Entity

- Name
- Category
- Description
- Regional Variants
- Story Count

Cards provide sufficient context before opening detail pages.

---

# Relationship Visualization

Relationships are first-class objects.

Examples:

Appears In

Mentioned By

Belongs To

Originates From

Influences

Documents

References

Derived From

Contradicts

Supports

Inspired By

Relationship types should be visually distinguishable without overwhelming the user.

---

# Progressive Disclosure

The Atlas never displays the entire graph at once.

Instead it reveals information gradually.

Initial view

↓

First-degree relationships

↓

Second-degree relationships

↓

Expanded network

This prevents cognitive overload.

---

# Knowledge Trails

One of the Atlas's defining features.

A trail records the user's exploration path.

Example

```
Kuntilanak

↓

West Java

↓

Traditional Belief

↓

Ancestor Ritual

↓

Historical Event

↓

Another Story
```

Users may:

Save

Rename

Share

Export

Resume

Trails become reusable research paths.

---

# Compare Mode

Users may compare two or more objects.

Example

Kuntilanak

vs

Wewe Gombel

Comparison includes:

Regions

Stories

Beliefs

Themes

Timeline

Evidence

Relationship Network

Comparisons are visual rather than tabular whenever possible.

---

# Atlas Filters

Available filters include:

Knowledge Type

Culture

Region

Theme

Motif

Creator

Language

Evidence Quality

Publication Status

Time Period

Review Status

Filters update the Atlas instantly.

---

# Inspector Panel

Selecting an object opens the inspector.

Displays:

Overview

Metadata

Relationships

Timeline

Evidence

Sources

Related Stories

Related Articles

Quick Actions

Users remain inside the Atlas while inspecting details.

---

# Story Journey

The Atlas emphasizes journeys rather than destinations.

Every object should answer:

Where did this originate?

What is it related to?

How has it evolved?

Where should I explore next?

The platform actively encourages continuous exploration.

---

# AI Assistance

Atlas AI assists users by:

Highlighting hidden relationships

Suggesting unexplored paths

Explaining graph structures

Summarizing clusters

Identifying recurring motifs

Recommending related stories

AI suggestions always cite underlying knowledge objects.

---

# Accessibility

Atlas interactions support:

Keyboard navigation

Screen readers

High contrast

Reduced motion

Zoom

Large text

No interaction should rely solely on drag-and-drop.

---

# Performance

Target performance:

Initial Atlas Load

<2 seconds

Expand Node

<300 ms

Filter Update

<300 ms

Inspector Open

<150 ms

Zoom

60 FPS

Performance directly affects perceived quality.

---

# Analytics

Measure:

Exploration Depth

Trail Length

Node Expansion Rate

Relationship Click Rate

Saved Trails

Comparison Usage

Atlas Session Duration

Discovery Completion

The objective is to understand how people learn—not merely how long they stay.

---

# Future Vision

The Atlas is designed to evolve.

Future capabilities include:

3D Atlas

Historical Layers

Seasonal Layers

Audio Layers

Interactive Museum Mode

Collaborative Exploration

Educational Mode

AR/VR Experiences

Personal Research Spaces

Knowledge Constellations

The architecture should accommodate these without requiring fundamental redesign.

---

# Guiding Principle

The Atlas is not a graph viewer.

It is a living landscape of Indonesian mystery culture.

Every interaction should deepen understanding, reveal meaningful connections, and inspire further exploration.

When users forget that they are using software and instead feel that they are exploring an ever-growing cultural world, the Atlas has achieved its purpose.