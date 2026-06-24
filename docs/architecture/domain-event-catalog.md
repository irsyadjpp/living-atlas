# Domain Event Catalog

## Version 1.0
## Status: Draft

---

# Overview

This catalog defines all domain events emitted by services in The Living Atlas platform. Events are the backbone of the event-driven architecture, enabling loose coupling between bounded contexts.

Each event follows the standard envelope defined in ADR-004.

---

# Event Categories

## Identity Domain (identity-service)

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| UserRegistered | 1 | User completes registration | identity-service | gateway-service, content-service | New user account created |
| UserLoggedIn | 1 | Successful authentication | identity-service | governance-service | User login event (audit) |
| UserSuspended | 1 | Admin suspends user | identity-service | gateway-service | User access revoked |
| UserDeleted | 1 | User account removed | identity-service | All services | User data deletion trigger |
| TenantCreated | 1 | New tenant registered | identity-service | All services | New organization onboarded |
| TenantUpdated | 1 | Tenant configuration changed | identity-service | All services | Tenant settings modified |
| RoleAssigned | 1 | Role granted to user | identity-service | gateway-service | User authorization changed |
| RoleRevoked | 1 | Role removed from user | identity-service | gateway-service | User authorization revoked |

## Source Domain (content-service)

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| ChannelRegistered | 1 | New channel added | content-service | ingestion-service | YouTube/podcast channel tracked |
| VideoIngested | 1 | Video content acquired | ingestion-service | content-service, extraction-service | Raw video data stored |
| MetadataCaptured | 1 | Video metadata collected | ingestion-service | content-service | Title, description, tags stored |
| TranscriptImported | 1 | Transcript ready | extraction-service | content-service, enrichment-service | Audio transcribed to text |
| TranscriptSegmentCreated | 1 | Segment extracted | extraction-service | content-service, enrichment-service | Timestamped segment available |
| SpeakerIdentified | 1 | Speaker diarized | extraction-service | content-service | Speaker label assigned to segment |
| SourceRegistered | 1 | Source tracked in system | content-service | knowledge-service | New content source available |

## Story Domain (content-service)

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| StoryCreated | 1 | Story extracted or manually created | content-service | knowledge-service, research-service, workflow-service | New story entered the system |
| StoryVersionCreated | 1 | New version of story saved | content-service | knowledge-service | Immutable version recorded |
| StorySubmittedForReview | 1 | Story sent to workflow | content-service | workflow-service | Story enters editorial review |
| StoryApproved | 1 | Story passes review | workflow-service | content-service, knowledge-service | Story ready for publication |
| StoryRejected | 1 | Story fails review | workflow-service | content-service | Story returned for revision |
| StoryPublished | 1 | Story goes live | content-service | knowledge-service, search-service | Story publicly available |
| StoryArchived | 1 | Story removed from publication | content-service | knowledge-service | Story no longer public |
| StoryMerged | 1 | Two stories consolidated | content-service | knowledge-service | Duplicate stories merged |
| EvidenceLinked | 1 | Evidence attached to story | content-service | knowledge-service | Transcript segment linked |

## Knowledge Domain (knowledge-service)

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| KnowledgeObjectCreated | 1 | New entity/theme/motif discovered | enrichment-service, knowledge-service | neo4j-sync, weaviate-sync | Knowledge artifact created |
| KnowledgeObjectUpdated | 1 | Knowledge object modified | knowledge-service | neo4j-sync, weaviate-sync | Existing object revised |
| KnowledgeObjectMerged | 1 | Objects consolidated | knowledge-service | neo4j-sync, weaviate-sync | Duplicate resolution |
| ClaimCreated | 1 | New claim extracted | enrichment-service | knowledge-service | Statement with evidence recorded |
| ClaimVerified | 1 | Claim passes human review | workflow-service | knowledge-service | Claim confirmed by editor |
| ContradictionDetected | 1 | Conflicting claims found | knowledge-service | research-service | Multiple versions detected |
| ThemeExtracted | 1 | Theme identified from content | enrichment-service | knowledge-service | Narrative theme cataloged |
| MotifExtracted | 1 | Motif identified from content | enrichment-service | knowledge-service | Narrative motif cataloged |
| EntityLinkedToStory | 1 | Entity associated with story | knowledge-service | neo4j-sync | Graph relationship created |

## Article Domain (content-service)

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| ArticleGenerated | 1 | Article created by AI | article-service | content-service | AI article ready for review |
| ArticlePublished | 1 | Article goes live | content-service | web-atlas | Article publicly accessible |
| ArticleUpdated | 1 | Article content revised | content-service | web-atlas | Published article updated |
| ArticleArchived | 1 | Article removed | content-service | web-atlas | Article no longer available |

## Research Domain (research-service)

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| CollectionCreated | 1 | Research collection created | research-service | - | User organizes research |
| AnnotationAdded | 1 | Annotation saved | research-service | - | User annotates content |
| SavedQueryCreated | 1 | Query bookmarked | research-service | - | User saves search |
| ExportGenerated | 1 | Export package ready | research-service | - | Research exported |

## Workflow Domain (workflow-service)

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| ReviewRequested | 1 | Content sent for review | workflow-service | content-service, knowledge-service | Reviewer assignment |
| ReviewApproved | 1 | Content approved | workflow-service | content-service, knowledge-service | Quality gate passed |
| ReviewRejected | 1 | Content rejected | workflow-service | content-service, knowledge-service | Quality gate failed |
| WorkflowCompleted | 1 | Full workflow finished | workflow-service | content-service | Final state reached |

## AI Pipeline (ai-platform)

The AI Platform event catalog has been moved to `docs/ai-platform/domain-event-catalog.md`.
This section is maintained for backward compatibility. See the AI Platform document for the complete catalog.

| Event | Version | Trigger | Producers | Consumers | Description |
|-------|---------|---------|-----------|-----------|-------------|
| SourceSubmitted | 1 | Source registered | content-service | orchestration-service | New source material submitted |
| SourceMetadataImported | 1 | Metadata retrieved | ingestion-service | content-service, orchestration-service | External metadata imported |
| TranscriptImported | 1 | Transcript ready | ingestion-service | orchestration-service, content-service | Raw transcript imported |
| TranscriptNormalized | 1 | Transcript cleaned | ingestion-service | orchestration-service | Transcript normalized |
| CanonicalStoryExtractionRequested | 1 | Story extraction needed | orchestration-service | extraction-service | Request story extraction |
| CanonicalStoryExtracted | 1 | Story extracted | extraction-service | orchestration-service, content-service | Canonical story ready |
| KnowledgeExtractionRequested | 1 | Knowledge extraction needed | orchestration-service | extraction-service | Request knowledge extraction |
| KnowledgeExtracted | 1 | Knowledge extracted | extraction-service | orchestration-service, knowledge-service | Knowledge entities ready |
| KnowledgeNormalizationRequested | 1 | Normalization needed | orchestration-service | normalization-service | Request normalization |
| KnowledgeNormalized | 1 | Knowledge normalized | normalization-service | orchestration-service, knowledge-service | Knowledge normalized |
| KnowledgeValidationRequested | 1 | Validation needed | orchestration-service | validation-service | Request validation |
| KnowledgeValidated | 1 | Knowledge validated | validation-service | orchestration-service, knowledge-service | Knowledge validated |
| ArticleGenerationRequested | 1 | Article needed | orchestration-service | article-service | Request article generation |
| ArticleGenerated | 1 | Article created | article-service | orchestration-service, workflow-service | Article draft ready |
| EmbeddingGenerationRequested | 1 | Embeddings needed | orchestration-service | embedding-service | Request embedding generation |
| EmbeddingGenerated | 1 | Embeddings ready | embedding-service | orchestration-service, weaviate-sync | Vector embeddings available |
| GraphProjectionRequested | 1 | Graph update needed | orchestration-service | neo4j-sync | Request graph projection |
| GraphProjected | 1 | Graph updated | neo4j-sync | orchestration-service | Graph projection complete |
| ReviewRequested | 1 | Review needed | orchestration-service, content-service | workflow-service | Content submitted for review |
| ReviewApproved | 1 | Content approved | workflow-service | orchestration-service, content-service, knowledge-service | Review passed |
| ReviewRejected | 1 | Content rejected | workflow-service | orchestration-service, content-service, knowledge-service | Review failed |
| PublicationRequested | 1 | Publication needed | workflow-service | content-service | Request publication |
| PublicationCompleted | 1 | Content published | content-service | orchestration-service, knowledge-service, research-service | Publication complete |
| PipelineFailed | 1 | Pipeline step failed | any AI service | orchestration-service | Error in processing |
| PipelineCompleted | 1 | Full pipeline done | orchestration-service | content-service, knowledge-service | End-to-end processing complete |

---

# Event Flow Diagrams

## Story Creation Flow
```
content-service                  enrichment-service           knowledge-service
     │                                │                            │
     │  StoryCreated ───────────────► │                            │
     │                                │  ThemeExtracted ──────────►│
     │                                │  MotifExtracted ──────────►│
     │                                │  ClaimCreated ────────────►│
     │                                │  KnowledgeObjectCreated ──►│
     │                                │                            │
     │  StorySubmittedForReview ──► workflow-service              │
     │                                │                            │
     │  StoryApproved ◄───────── workflow-service                 │
     │                                │                            │
     │  StoryPublished ──────────► knowledge-service              │
     │                                │                            │
     │                                │  EntityLinkedToStory ──► neo4j-sync
     │                                │  EmbeddingCreated ────► weaviate-sync
```

## Source Ingestion Flow
```
content-service              ingestion-service          extraction-service
     │                            │                            │
     │  ChannelRegistered ──────► │                            │
     │                            │  VideoIngested ──────────► │
     │                            │                            │
     │                            │  MetadataCaptured ──────►  │
     │                            │                            │
     │                            │  TranscriptImported ──────►│
     │                            │  SpeakerIdentified         │
     │                            │                            │
     │  SourceRegistered ◄──────────────────────────────────── │
```

---

# Event Versioning

Events follow semantic versioning at the schema level:

- **Major**: Breaking schema changes (field removal, type changes)
- **Minor**: Backward-compatible additions (new optional fields)
- **Patch**: Documentation clarifications

Each event type tracks its own version independently.

---

# References

- ADR-004: Event-Driven Architecture with Transactional Outbox
- ADR-006: Service Boundaries and Ownership
- BACKEND-PRD.md §5 Event Architecture
- docs/ai-platform/domain-event-catalog.md: AI Platform event catalog (authoritative for AI pipeline events)
- docs/ai-platform/queue-contract-specification.md: Queue contract specification