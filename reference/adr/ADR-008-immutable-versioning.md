# ADR-008: Immutable Versioning — Append-Only, No Overwrite

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture preserves and structures cultural knowledge. Cultural knowledge is not static — it evolves as new witnesses come forward, new research is published, and new interpretations emerge. A story told in 2023 may be corrected, expanded, or reinterpreted in 2025. Both versions have historical value. The 2023 version represents what was known at that time. Overwriting it would destroy that historical record.

The platform handles four mutable entity types that require versioning:

1. **Stories** — Extracted from transcripts. May be re-extracted with improved AI prompts or corrected by human editors.
2. **Knowledge Objects** — Entities, folklore, beliefs, traditions. May be normalized (aliases resolved), enriched with new evidence, or corrected.
3. **Claims** — Evidence-grounded statements. May be validated, disputed, or refuted by new evidence.
4. **Articles** — Generated from stories and knowledge. May be revised by editors with updated information or improved writing.

Additionally, the platform relies on **projections** (Neo4j graph, Weaviate vectors) that are derived from these entities. Projections must reflect the current state but should be rebuildable from historical data.

The PRD explicitly states: "Updates create new versions. Never overwrite: Stories, Knowledge Objects, Claims, Articles."

## Technical Context

The current codebase uses `@Version` annotations for optimistic locking, not versioning:

```java
// Story.java — existing entity
@Setter(AccessLevel.NONE)
@Version
@Column(nullable = false)
private Long version = 1L;

// KnowledgeObject.java — existing entity
@Version
@Column(nullable = false)
private Long version = 1L;
```

These `@Version` fields are used by JPA for optimistic concurrency control — they prevent concurrent writes from silently overwriting each other. They are NOT content versions. When a story is updated, the version increments but the old state is lost. This is acceptable for mutable data but not for the immutable versioning requirement.

The platform's audit requirements mandate `created_at`, `created_by`, `updated_at`, `updated_by`, `deleted_at`, `deleted_by`, and `version` on every business table — but this does not preserve historical states. The `updated_at` and `updated_by` columns only track the last update, not the full history.

## Constraints

1. **Immutable by declaration (PRD §3.7)**: "Updates create new versions. Never overwrite: Stories, Knowledge Objects, Claims, Articles." This is an architectural principle, not a suggestion.

2. **Audit trail**: Every change must be traceable. Who made what change, when, and why. The audit trail must be complete — no overwrites that destroy history.

3. **Rollback capability**: Editors must be able to revert to a previous version of a story, knowledge object, claim, or article. Rollback must be a version operation, not a data restoration.

4. **Projection impact**: Neo4j and Weaviate projections must reflect the current (latest) version. When a new version is created, projections must be updated. When rolling back, projections must reflect the rolled-back version.

5. **Storage growth**: 100,000 stories × average 5 versions = 500,000 story rows. 1,000,000 knowledge objects × average 3 versions = 3,000,000 knowledge rows. Storage growth is a first-order concern.

6. **Read performance**: The common case is reading the latest version. Version history queries are rare (audit, research, rollback). The schema must optimize for latest-version reads.

7. **Referential integrity**: Other entities reference stories, knowledge objects, claims, and articles by ID. When a new version is created, should the reference point to the old version or the latest version? This must be explicitly defined.

8. **Event-driven consistency**: Version creation emits events (`StoryVersionCreated`, `KnowledgeVersionCreated`). Projection workers consume these events to update Neo4j and Weaviate. Version creation must be atomic with event publication.

## Problem Statement

Stories, Knowledge Objects, Claims, and Articles must never be overwritten. Updates must create new versions while preserving the complete version history. Every version must be traceable to its author, timestamp, and reason for change. The system must support rollback to any previous version. Projections (Neo4j, Weaviate) must reflect the current version. How do we implement immutable versioning across all four entity types while maintaining read performance for latest-version queries, managing storage growth, preserving referential integrity, and ensuring event-driven consistency with projections?

# Decision

**Stories, Knowledge Objects, Claims, and Articles are immutable. Updates create new version rows. The previous version is preserved. No UPDATE statement modifies the content of a versioned entity. The latest version is identified by a `current_version_id` pointer on the aggregate root. Rollback is a version operation that creates a new version identical to the target version. Projections always reflect the version pointed to by `current_version_id`.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    IMMUTABLE VERSIONING MODEL                             │
│                                                                          │
│  ┌──────────────────────────────┐                                        │
│  │      Aggregate Root           │                                        │
│  │      (e.g., Story)            │                                        │
│  │                               │                                        │
│  │  id: UUID (stable)           │──────► Always references the           │
│  │  slug: String (stable)       │        current (latest) version        │
│  │  current_version_id: UUID    │                                        │
│  │  status: ENUM                │                                        │
│  │  created_at: TIMESTAMP       │                                        │
│  └──────────┬───────────────────┘                                        │
│             │                                                             │
│             │ 1:N                                                         │
│             │                                                             │
│             ▼                                                             │
│  ┌──────────────────────────────┐                                        │
│  │      Version Row              │                                        │
│  │      (immutable once written) │                                        │
│  │                               │                                        │
│  │  id: UUID                     │                                        │
│  │  story_id: UUID (FK → root)  │                                        │
│  │  version_number: INTEGER     │         Version 2 (current)            │
│  │  title: String               │  ┌──────────────────────────────┐      │
│  │  content: TEXT/JSONB         │  │  version_number: 2           │      │
│  │  change_reason: TEXT         │  │  change_reason: "Editor      │      │
│  │  created_by: UUID            │  │  correction to timeline"     │      │
│  │  created_at: TIMESTAMP       │  │  created_by: editor@tenant  │      │
│  │  previous_version_id: UUID   │  │  previous_version_id: v1.id │      │
│  └──────────────────────────────┘  └──────────────────────────────┘      │
│                                             ▲                            │
│                                             │                            │
│                                    Version 1 (archived)                  │
│                             ┌──────────────────────────────┐             │
│                             │  version_number: 1           │             │
│                             │  change_reason: "Initial AI  │             │
│                             │  extraction"                 │             │
│                             │  created_by: system@ai       │             │
│                             │  previous_version_id: null   │             │
│                             └──────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Aggregate Root + Version Rows Pattern

Every versioned entity uses a two-table pattern:

- **Aggregate root table** (e.g., `content_stories`): One row per entity. Contains the stable identifier (`id`), the `current_version_id` pointer, the current `status`, and lifecycle timestamps.
- **Version table** (e.g., `content_story_versions`): One row per version. Contains the actual content fields. Immutable after creation.

```sql
-- Aggregate root table
CREATE TABLE content_stories (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                VARCHAR(500) UNIQUE,
    
    -- Points to the current (latest) version
    current_version_id  UUID NOT NULL REFERENCES content_story_versions(id),
    
    -- Status is tracked on the root, not on individual versions
    status              VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
    
    -- Provenance
    tenant_id           UUID NOT NULL,
    workspace_id        UUID,
    owner_id            UUID,
    
    -- Lifecycle (the root is never updated for content changes)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- Changes when version pointer changes
    updated_by          UUID,
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID,
    is_deleted          BOOLEAN NOT NULL DEFAULT false,
    
    CONSTRAINT fk_current_version FOREIGN KEY (current_version_id) 
        REFERENCES content_story_versions(id)
);

-- Version table (immutable)
CREATE TABLE content_story_versions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to aggregate root
    story_id            UUID NOT NULL REFERENCES content_stories(id),
    
    -- Monotonic version number within this aggregate
    version_number      INTEGER NOT NULL,
    
    -- Content fields (actual data)
    title               TEXT NOT NULL,
    summary             TEXT,
    story_type          VARCHAR(50) NOT NULL,
    narrative_type      VARCHAR(50),
    language_code       VARCHAR(20),
    cultural_context    JSONB,
    content             JSONB,           -- Full Canonical Story JSON if AI-generated
    metadata            JSONB,           -- Extraction metadata, prompt version, etc.
    
    -- Version chain
    previous_version_id UUID REFERENCES content_story_versions(id),
    change_reason       TEXT,            -- Why this version was created
    change_type         VARCHAR(50) NOT NULL,  -- 'initial_extraction', 'human_edit', 're_extraction', 'rollback', 'merge'
    
    -- Immutable audit (these never change)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL,
    
    -- Constraints
    UNIQUE(story_id, version_number),
    CONSTRAINT fk_previous_version FOREIGN KEY (previous_version_id)
        REFERENCES content_story_versions(id),
    CONSTRAINT check_rollback_cycle CHECK (id != previous_version_id)
);

-- Index for fast latest-version lookup
CREATE INDEX idx_stories_current_version ON content_stories(current_version_id);
CREATE INDEX idx_story_versions_story_id ON content_story_versions(story_id, version_number DESC);
```

### Rule 2: Creating a New Version Is INSERT Only

Creating a new version never modifies old version rows. It INSERTs into the version table and UPDATEs the `current_version_id` pointer on the aggregate root.

```java
@Service
@Transactional
public class StoryService {
    
    private final StoryRepository storyRepository;
    private final StoryVersionRepository versionRepository;
    private final EventPublisher eventPublisher;
    
    public Story createInitialVersion(CreateStoryCommand cmd) {
        // 1. Create aggregate root
        Story story = new Story();
        story.setSlug(generateSlug(cmd.getTitle()));
        story.setStatus(StoryStatus.DRAFT);
        story.setTenantId(cmd.getTenantId());
        story.setWorkspaceId(cmd.getWorkspaceId());
        story.setOwnerId(cmd.getUserId());
        story = storyRepository.save(story);
        
        // 2. Create version 1
        StoryVersion version = new StoryVersion();
        version.setStoryId(story.getId());
        version.setVersionNumber(1);
        version.setTitle(cmd.getTitle());
        version.setStoryType(cmd.getStoryType());
        version.setContent(cmd.getContent());
        version.setChangeType("initial_extraction");
        version.setChangeReason("Initial AI extraction from transcript");
        version.setCreatedBy(cmd.getUserId());
        version.setPreviousVersionId(null);  // First version
        version = versionRepository.save(version);
        
        // 3. Point root to current version
        story.setCurrentVersionId(version.getId());
        story = storyRepository.save(story);
        
        // 4. Publish event
        eventPublisher.publish(new StoryVersionCreated(
            story.getId(), version.getId(), 1, "initial_extraction"
        ));
        
        return story;
    }
    
    public Story createNewVersion(CreateVersionCommand cmd) {
        Story story = storyRepository.findById(cmd.getStoryId())
            .orElseThrow(() -> new NotFoundException("Story not found"));
        
        StoryVersion currentVersion = versionRepository.findById(story.getCurrentVersionId())
            .orElseThrow(() -> new NotFoundException("Current version not found"));
        
        // 1. Create new version
        StoryVersion newVersion = new StoryVersion();
        newVersion.setStoryId(story.getId());
        newVersion.setVersionNumber(currentVersion.getVersionNumber() + 1);
        newVersion.setTitle(cmd.getTitle());
        newVersion.setStoryType(cmd.getStoryType());
        newVersion.setContent(cmd.getContent());
        newVersion.setChangeType(cmd.getChangeType());
        newVersion.setChangeReason(cmd.getChangeReason());
        newVersion.setCreatedBy(cmd.getUserId());
        newVersion.setPreviousVersionId(currentVersion.getId());
        newVersion = versionRepository.save(newVersion);
        
        // 2. Update root pointer (only UPDATE on the root)
        story.setCurrentVersionId(newVersion.getId());
        story.setUpdatedAt(OffsetDateTime.now());
        story.setUpdatedBy(cmd.getUserId());
        story = storyRepository.save(story);
        
        // 3. Publish event
        eventPublisher.publish(new StoryVersionCreated(
            story.getId(), newVersion.getId(), 
            newVersion.getVersionNumber(), cmd.getChangeType()
        ));
        
        return story;
    }
}
```

**Critical**: The only UPDATEs allowed on the aggregate root are:
- `current_version_id` (when a new version is created or rollback occurs)
- `updated_at` / `updated_by` (lifecycle tracking)
- `deleted_at` / `deleted_by` / `is_deleted` (soft delete)
- `status` (state machine transitions)

Content fields on the aggregate root are READ-ONLY. They are always read from the current version.

### Rule 3: Reading the Latest Version

The common read path must be efficient. The aggregate root's `current_version_id` provides a direct pointer to the current version row.

```java
// Reading the latest version — single query with join
public StoryVersion getLatestVersion(UUID storyId) {
    return entityManager.createQuery(
        "SELECT v FROM StoryVersion v " +
        "JOIN Story s ON s.currentVersionId = v.id " +
        "WHERE s.id = :storyId", StoryVersion.class)
    .setParameter("storyId", storyId)
    .getSingleResult();
}

// Reading a specific version — direct lookup
public StoryVersion getVersion(UUID versionId) {
    return versionRepository.findById(versionId)
        .orElseThrow(() -> new NotFoundException("Version not found"));
}

// Reading version history — ordered by version number
public List<StoryVersion> getVersionHistory(UUID storyId) {
    return versionRepository.findByStoryIdOrderByVersionNumberDesc(storyId);
}
```

**API response shape**:
```json
{
  "id": "story-uuid",
  "slug": "misteri-kuntilanak-di-desa-sukamaju",
  "status": "PUBLISHED",
  "currentVersion": {
    "versionNumber": 3,
    "title": "Misteri Kuntilanak di Desa Sukamaju",
    "summary": "...",
    "changeReason": "Editor correction to timeline",
    "createdAt": "2026-06-25T10:00:00Z",
    "createdBy": "editor-uuid"
  },
  "versionHistory": [
    {"versionNumber": 3, "changeReason": "Editor correction", "createdAt": "..."},
    {"versionNumber": 2, "changeReason": "Re-extraction with v4 prompt", "createdAt": "..."},
    {"versionNumber": 1, "changeReason": "Initial AI extraction", "createdAt": "..."}
  ]
}
```

**Important**: The version history endpoint returns metadata only (version number, change reason, timestamp, author). It does not return full content for all versions. Full content is only returned for the current version or when a specific version is requested. This prevents the API from sending massive payloads for stories with many versions.

### Rule 4: Rollback Creates a New Version

Rollback does NOT restore an old version in-place. It creates a NEW version whose content is a copy of the target version. This preserves the audit trail — every operation is recorded as a new version.

```java
public StoryVersion rollbackToVersion(UUID storyId, UUID targetVersionId, UUID userId, String reason) {
    Story story = storyRepository.findById(storyId)
        .orElseThrow(() -> new NotFoundException("Story not found"));
    
    StoryVersion targetVersion = versionRepository.findById(targetVersionId)
        .orElseThrow(() -> new NotFoundException("Target version not found"));
    
    StoryVersion currentVersion = versionRepository.findById(story.getCurrentVersionId())
        .orElseThrow(() -> new NotFoundException("Current version not found"));
    
    // Create a new version with the target version's content
    StoryVersion rollbackVersion = new StoryVersion();
    rollbackVersion.setStoryId(story.getId());
    rollbackVersion.setVersionNumber(currentVersion.getVersionNumber() + 1);
    rollbackVersion.setTitle(targetVersion.getTitle());
    rollbackVersion.setStoryType(targetVersion.getStoryType());
    rollbackVersion.setContent(targetVersion.getContent());
    rollbackVersion.setChangeType("rollback");
    rollbackVersion.setChangeReason(reason != null ? reason 
        : "Rollback to version " + targetVersion.getVersionNumber());
    rollbackVersion.setCreatedBy(userId);
    rollbackVersion.setPreviousVersionId(currentVersion.getId());
    rollbackVersion = versionRepository.save(rollbackVersion);
    
    // Update root pointer
    story.setCurrentVersionId(rollbackVersion.getId());
    story.setUpdatedAt(OffsetDateTime.now());
    story.setUpdatedBy(userId);
    story = storyRepository.save(story);
    
    // Publish event
    eventPublisher.publish(new StoryVersionCreated(
        story.getId(), rollbackVersion.getId(),
        rollbackVersion.getVersionNumber(), "rollback"
    ));
    
    return rollbackVersion;
}
```

**Rollback chain example**:
```
Version 1 (initial) ← Version 2 (edit) ← Version 3 (edit) ← Version 4 (rollback to v1)
                                                                      ↑
                                                              Content is copy of v1
```

After rollback, version 4 is the current version. Its content is identical to version 1. Versions 2 and 3 are preserved in the history. This creates a complete, auditable trail: "Editor rolled back to version 1 because the edits in versions 2 and 3 introduced factual errors."

### Rule 5: Referential Integrity — References Point to Aggregate Root

Other entities that reference stories, knowledge objects, claims, or articles point to the aggregate root ID, not the version ID. The current version is always resolved through the root pointer.

```sql
-- Other entities reference the aggregate root
CREATE TABLE knowledge_claims (
    id                  UUID PRIMARY KEY,
    story_id            UUID REFERENCES content_stories(id),  -- References the root, not a version
    statement           TEXT NOT NULL,
    ...
);

-- To get the claim's story content, resolve through the root
SELECT v.title, v.content 
FROM knowledge_claims c
JOIN content_stories s ON c.story_id = s.id
JOIN content_story_versions v ON s.current_version_id = v.id
WHERE c.id = :claimId;
```

**Rationale**: If references pointed to specific versions, then:
- When a new version is created, all references would still point to the old version
- The system would have stale data everywhere
- Explicit version pinning would be required (e.g., "display story version 3 on article 5")
- This adds complexity that is not justified for the common case

**Exception**: Historical exports and research snapshots may pin specific versions. This is handled at the application layer, not the database layer:

```sql
CREATE TABLE research_version_pins (
    id                  UUID PRIMARY KEY,
    collection_id       UUID NOT NULL REFERENCES research_collections(id),
    entity_type         VARCHAR(50) NOT NULL,  -- 'story', 'knowledge_object', 'article'
    entity_id           UUID NOT NULL,          -- Aggregate root ID
    pinned_version_id   UUID NOT NULL,          -- Specific version ID
    pinned_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pinned_by           UUID NOT NULL,
    
    UNIQUE(collection_id, entity_type, entity_id)
);
```

### Rule 6: Status Is on the Aggregate Root, Not on Versions

Content status (DRAFT, REVIEW, APPROVED, PUBLISHED, ARCHIVED) is tracked on the aggregate root, not on individual versions. This means:
- A version is not inherently "published" or "draft"
- The current version is whatever the root points to, regardless of status
- Publishing a story does not create a new version — it changes the status
- Editing a published story creates a new version and (optionally) changes status to DRAFT or REVIEW

```java
public void publishStory(UUID storyId, UUID userId) {
    Story story = storyRepository.findById(storyId)
        .orElseThrow(() -> new NotFoundException("Story not found"));
    
    // State machine validation
    if (story.getStatus() != StoryStatus.APPROVED) {
        throw new IllegalStateException(
            "Only APPROVED stories can be published. Current status: " + story.getStatus());
    }
    
    story.setStatus(StoryStatus.PUBLISHED);
    story.setUpdatedBy(userId);
    storyRepository.save(story);
    
    eventPublisher.publish(new StoryPublished(story.getId(), story.getCurrentVersionId()));
}
```

**Why status is on the root**: Status is a property of the entity, not of a specific version. A published story with version 5 is the same entity as when it was a draft with version 5. The status changes independently of version creation.

### Rule 7: Version Change Types

Every version must declare its `change_type`. This enables filtering, analytics, and rollback decision-making.

| Change Type | Description | Creator | Requires Review? |
|-------------|-------------|---------|------------------|
| `initial_extraction` | First version from AI extraction | System (AI) | Yes |
| `re_extraction` | Re-extraction with updated prompt/AI model | System (AI) | Yes |
| `human_edit` | Manual edit by editor or creator | Human | If published |
| `human_correction` | Error correction (minor, no review needed) | Human | No |
| `rollback` | Rollback to a previous version | Human or System | If published |
| `merge` | Merge from another branch/version | Human | Yes |
| `ai_suggestion` | AI-suggested edit (requires human approval) | System (AI) | Yes |
| `normalization` | Automated normalization (alias resolution) | System | No |
| `bulk_update` | Bulk operation (e.g., tenant-wide change) | System or Human | Yes |

**Review requirement by change type**:
- `initial_extraction`, `re_extraction`, `human_edit` (published), `merge`, `ai_suggestion`, `bulk_update` → status changes to `REVIEW_REQUIRED`
- `human_correction`, `rollback` (draft), `normalization` → status remains or auto-approves

### Rule 8: Projection Consistency

When a new version is created, projection workers must update Neo4j and Weaviate to reflect the new version. The aggregate root's `updated_at` timestamp changes, which can be used as a polling trigger.

```python
# Projection worker — triggered by StoryVersionCreated event
async def handle_story_version_created(event):
    story_id = event.data['storyId']
    version_id = event.data['versionId']
    version_number = event.data['versionNumber']
    change_type = event.data['changeType']
    
    # Read the current version (the root's current_version_id now points to the new version)
    story = await db.fetch_one("""
        SELECT s.id, s.status, s.current_version_id,
               v.title, v.summary, v.content, v.story_type,
               v.version_number, v.change_type
        FROM content_stories s
        JOIN content_story_versions v ON s.current_version_id = v.id
        WHERE s.id = $1
    """, story_id)
    
    # Update Neo4j
    await neo4j_session.run("""
        MATCH (s:Story {id: $story_id})
        SET s.title = $title,
            s.summary = $summary,
            s.version_number = $version_number,
            s.updated_at = timestamp()
    """, story_id=story['id'], title=story['title'],
         summary=story['summary'], version_number=story['version_number'])
    
    # Update Weaviate
    await weaviate_client.data_object.update(
        class_name="Story",
        uuid=story['id'],
        data_object={
            "title": story['title'],
            "summary": story['summary'],
            "version_number": story['version_number']
        }
    )
    
    # Log projection state
    await db.execute("""
        INSERT INTO projection_state 
            (entity_type, entity_id, projected_version_id, projected_at)
        VALUES ('story', $1, $2, NOW())
        ON CONFLICT (entity_type, entity_id) 
        DO UPDATE SET projected_version_id = $2, projected_at = NOW()
    """, story_id, version_id)
```

**Rollback projection**: When a rollback creates a new version, the projection worker processes it like any other version. The rollback version's content is a copy of the target version, so Neo4j and Weaviate reflect the rolled-back state correctly.

### Rule 9: Storage Management

Storage growth is managed through archiving, not deletion. Version history is preserved but can be moved to cold storage.

**Archiving strategy**:

```sql
-- Archived version table (same schema, different tablespace)
CREATE TABLE content_story_versions_archive (
    LIKE content_story_versions INCLUDING ALL
) TABLESPACE cold_storage;

-- Archiving job (scheduled, runs weekly)
CREATE OR REPLACE FUNCTION archive_old_versions()
RETURNS void AS $$
BEGIN
    -- Archive versions older than 1 year, keeping at least the last 5 versions per story
    WITH versions_to_archive AS (
        SELECT v.* FROM content_story_versions v
        WHERE v.created_at < NOW() - INTERVAL '1 year'
        AND v.id NOT IN (
            -- Keep the latest 5 versions per story
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY story_id ORDER BY version_number DESC
                ) AS rn
                FROM content_story_versions
            ) ranked WHERE rn <= 5
        )
    )
    INSERT INTO content_story_versions_archive
    SELECT * FROM versions_to_archive;
    
    -- Delete archived versions from main table
    DELETE FROM content_story_versions
    WHERE id IN (SELECT id FROM content_story_versions_archive);
END;
$$ LANGUAGE plpgsql;
```

**Storage estimation**:

| Entity | Rows | Avg Versions | Avg Size/Version | Total |
|--------|------|-------------|-----------------|-------|
| Stories | 100,000 | 5 | 10KB | 5GB |
| Knowledge Objects | 1,000,000 | 3 | 2KB | 6GB |
| Claims | 5,000,000 | 2 | 1KB | 10GB |
| Articles | 200,000 | 4 | 8KB | 6.4GB |
| **Total** | | | | **~27.4GB** |

At the target scale, version storage is approximately 27GB. With archiving (keep 5 most recent versions, archive older), active storage is approximately 15GB.

### Rule 10: API Versioning — Breaking Changes to the Versioning Model

If the versioning model itself needs to change (e.g., introducing branching, merging, or draft/published version separation), the API must maintain backward compatibility.

**Backward-compatible API evolution**: The API always returns the latest version by default. Clients that do not care about versioning continue to work unchanged. Version history and specific-version retrieval are optional query parameters:

```
GET /api/v1/stories/{id}                          → Returns latest version
GET /api/v1/stories/{id}?version=latest           → Returns latest version (explicit)
GET /api/v1/stories/{id}?version=3                → Returns version 3
GET /api/v1/stories/{id}/versions                 → Returns version history (metadata only)
GET /api/v1/stories/{id}/versions/3               → Returns version 3 (full content)
```

# Alternatives Considered

## Alternative 1: Single Table with Soft Delete and History Table

**Description**: Keep the current single-table approach (`content_stories` with `@Version`). When a record is updated, copy the old state to a `content_stories_history` table before applying the update. The main table always has the latest state. The history table has all previous states.

**Advantages**:
- Simple read path — always read from the main table (single table, no join)
- Backward compatible with existing code — existing `@Version` logic continues to work
- History queries are possible but isolated to the history table
- No application-layer changes needed for basic CRUD operations

**Disadvantages**:
- **UPDATE still overwrites**: Despite the history table, the main table row is still UPDATEd. This means the main table's `created_at` reflects the original creation, but the actual content has been overwritten multiple times. The history table is a secondary artifact, not the primary record.
- **No version identity**: Each "version" in the history table is an opaque copy. There is no version number, no version chain, no change reason. Reconstructing the version history requires comparing snapshots.
- **Rollback requires data restoration**: Rolling back means copying a history row back to the main table. This is a data restoration operation, not a version operation. Audit trail for the rollback itself is lost (the restoration overwrites the current state).
- **Referential integrity ambiguity**: Other entities reference the main table's ID. When history is restored during rollback, other entities still point to the same ID. There is no way to know which version of the data was current when the reference was created.
- **History table growth**: The history table grows unbounded, just like the version table. But without version numbers, pruning old history is complex — which snapshots can be safely deleted?

**Rejection rationale**: The history table pattern is a band-aid on top of a fundamentally mutating data model. It provides an audit trail but does not provide version identity, version chains, or clean rollback semantics. The aggregate root + version rows pattern is architecturally cleaner and provides first-class version support.

## Alternative 2: Event Sourcing

**Description**: Replace the current state-based persistence with event sourcing. Instead of storing current state and version history, store the full event stream. Current state is derived by replaying events. Every state change is an event appended to the event store.

**Advantages**:
- **Complete audit trail**: Every state change is an immutable event. Nothing is lost. Ever.
- **Temporal queries**: Query the state at any point in time by replaying events up to that point.
- **Built-in version history**: Version history is the event stream. No separate versioning mechanism needed.
- **Natural fit with event-driven architecture**: The event store is already the source of truth for event-driven communication.
- **No storage duplication**: State is derived, not stored. No duplication of current state and historical state.

**Disadvantages**:
- **Massive architectural change**: Event sourcing would replace the entire persistence layer. The existing `@Entity`, `JpaRepository`, and `@Version` patterns would be replaced with event store repositories. This is a months-long migration.
- **Read performance**: Reading current state requires replaying all events for an aggregate. At 100 versions per story, this means 100 reads to get the current title. Snapshotting mitigates this but adds complexity.
- **Event store infrastructure**: Event sourcing requires an event store (either PostgreSQL with careful schema design or a dedicated event store like EventStoreDB). This adds operational complexity.
- **Query complexity**: Ad-hoc queries that are simple with SQL (e.g., "find all published stories about Kuntilanak") become complex with event sourcing. CQRS is required, adding another architectural layer.
- **Schema evolution**: Evolving the event schema is harder than evolving a state schema. Old events must be handled by current code. Event versioning is essential but complex.
- **Team unfamiliarity**: Event sourcing requires a significant mindset shift. For a small team (3–8 engineers), the learning curve and implementation complexity are prohibitive.

**Rejection rationale**: Event sourcing provides the strongest guarantees for audit, versioning, and temporal queries, but it is a massive architectural investment that is not justified for the current scale and team size. The aggregate root + version rows pattern provides the same benefits (immutability, audit trail, rollback, version history) with a fraction of the complexity. If the platform grows significantly, event sourcing can be reconsidered for specific bounded contexts (e.g., the AI pipeline state machine).

## Alternative 3: JSONB Append-Only Log per Entity

**Description**: Store all versions as an array of JSONB objects in a single row per entity. The `content_stories` table has a `versions JSONB[]` column that contains all versions. The current version is the last element in the array.

**Advantages**:
- Single table, no joins — read current version and all history from one row
- Simple schema — no separate version table to maintain
- Atomic updates — appending a version is a single UPDATE with `array_append`
- No foreign key complexity between root and version tables

**Disadvantages**:
- **PostgreSQL JSONB array size limit**: Each JSONB array element has overhead. At 10KB per version × 100 versions = 1MB per row. PostgreSQL TOAST can handle this, but performance degrades significantly as the array grows.
- **Concurrent append contention**: Multiple concurrent updates to the same row cause serialization failures. The `array_append` operation locks the entire row.
- **Indexing complexity**: Querying for a specific version within the array requires `jsonb_array_element()` or `UNNEST()`. These are significantly slower than indexed columns in a separate version table.
- **No referential integrity**: Other entities cannot reference a specific version within the JSONB array. They can only reference the entity ID.
- **Pruning complexity**: Removing old versions from the array requires rewriting the entire array. For a story with 100 versions, removing the oldest 50 requires reading, filtering, and writing a 500KB+ JSONB value.
- **Rollback complexity**: Rolling back requires finding the target version in the array and making it the current version. This requires array manipulation that is not atomic.

**Rejection rationale**: While the JSONB append-only log is architecturally simple, it does not scale to the platform's requirements. PostgreSQL JSONB arrays are not designed for append-heavy workloads with concurrent writers. The separate version table provides better performance, concurrency, and queryability.

## Alternative 4: Git-Like Content-Addressable Storage

**Description**: Store each version as a content-addressable blob (keyed by hash of content). The aggregate root stores a list of hashes representing the version history. Versions are stored in a blob store (PostgreSQL Large Objects, S3, or filesystem).

**Advantages**:
- **Deduplication**: If two versions have identical content (e.g., rollback creates a version identical to v1), the content is stored once. Git uses this to save space.
- **Content integrity**: Content hash verification ensures no data corruption.
- **Separation of structure from content**: The aggregate root is small (just hashes). Content is stored efficiently in the blob store.
- **Natural diff capability**: Content addressed by hash makes comparing versions trivial.

**Disadvantages**:
- **No human-readable database**: Content is stored as opaque blobs. Querying the database directly for content analysis is impossible without resolving hashes.
- **Application-layer complexity**: Every read and write requires hash computation, blob store resolution, and cache management. This is significantly more complex than a simple version table join.
- **Blob store operational overhead**: PostgreSQL Large Objects require special handling for backup and replication. External blob stores (S3) add network latency and availability concerns.
- **No benefit at the platform's scale**: Git's content deduplication is valuable at Google-scale (millions of versions of the same file). At 5–10 versions per story, the deduplication benefit is negligible.
- **SQL query complexity**: Finding "all stories by author X" requires resolving hashes to determine the author. This cannot be done efficiently in SQL.
- **Debugging overhead**: Engineers cannot read the database directly to debug issues. They must use special tooling to resolve hashes.

**Rejection rationale**: Content-addressable storage solves problems (massive deduplication, content integrity) that are not significant at the platform's scale. It adds significant complexity for negligible benefit. The version table approach provides better developer experience, simpler debugging, and adequate storage efficiency.

# Consequences

## Positive

1. **Complete audit trail**: Every version change is recorded with `change_type`, `change_reason`, `created_by`, and `created_at`. The version chain (`previous_version_id`) provides a complete, traversable history of every modification.

2. **True rollback**: Rollback creates a new version with the target version's content. The old versions are preserved. The rollback itself is recorded as a version with `change_type = 'rollback'`. This provides a complete, auditable trail of every state change, including corrections.

3. **Reproducibility**: Any past state can be reproduced by reading the appropriate version row. Researchers can verify "what did this story look like when the claim was made?" by reading the version that was current at that time.

4. **Concurrent safety**: The version table is append-only. Concurrent writes do not conflict — they create separate version rows. The only contention point is the `current_version_id` UPDATE on the aggregate root, which is a single-row, high-speed operation.

5. **Event-driven projection consistency**: Each version creation emits an event. Projection workers process the event and update Neo4j/Weaviate. The projection always reflects the version pointed to by `current_version_id`.

6. **Simple read path for latest version**: The aggregate root's `current_version_id` is a direct pointer to the current version row. A single JOIN query retrieves the latest version content. No aggregation, no sorting, no subquery.

7. **API backward compatibility**: The API returns the latest version by default. Clients that do not care about versioning continue to work unchanged. Version history and specific-version retrieval are optional.

8. **Storage management via archiving**: Old versions can be archived to cold storage while keeping the most recent versions in the active table. The version chain is preserved across archived and active tables.

## Negative

1. **Write amplification**: Every content change requires two writes (INSERT into version table + UPDATE on aggregate root). Compare to a mutable model where a single UPDATE suffices. At scale, this doubles write I/O.

2. **Read complexity for version history**: Reading version history requires querying the version table with `ORDER BY version_number DESC`. With millions of version rows, this query must be indexed carefully to avoid performance degradation.

3. **Storage growth**: Version history grows with every edit. 100,000 stories × average 5 versions = 500,000 version rows. 1,000,000 knowledge objects × average 3 versions = 3,000,000 version rows. Total ~27GB at target scale.

4. **Rollback is not undo**: Rollback creates a new version. It does not "undo" the intermediate versions — they remain in the history. If a rollback was performed in error, the user must rollback again to the version before the rollback. This is correct from an audit perspective but can be confusing.

5. **Status/version coupling confusion**: Status is on the aggregate root. Version is on the version rows. A published story with version 5 can have a new version 6 that is still in DRAFT status. Developers must understand that status and version are independent concerns.

6. **Referential integrity indirection**: Other entities reference the aggregate root ID. To get content, they must join through the current version pointer. This adds one JOIN to every query that needs content, compared to a single-table model.

7. **No branching**: The version chain is linear (v1 → v2 → v3). There is no support for branches (v2a and v2b from the same parent). Branching is not required by the PRD but may be desired for collaborative editing in the future.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Audit trail** | Complete, traversable version history | Every edit creates a new version row (write amplification) |
| **Rollback** | True rollback with audit trail | Rollback is not undo — intermediate versions remain |
| **Reproducibility** | Any past state can be reproduced | Requires version number + timestamp mapping |
| **Read performance** | Latest version via direct pointer | Version history queries need indexed sorting |
| **Storage** | Archivable, manageable growth | ~27GB at target scale for active versions |
| **Concurrency** | Append-only prevents write conflicts | Single contention point on root pointer update |
| **API simplicity** | Latest version by default | Clients must opt-in to version features |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Aggregate root UPDATE contention on high-traffic stories** | Low | Medium — concurrent version creation conflicts | Use `SELECT ... FOR UPDATE` on the root before version creation. Retry on conflict. The contention window is milliseconds — acceptable for the platform's traffic. |
| **Version table index size exceeds memory** | Low | Medium — index scan performance degrades | Partition version tables by creation date (monthly partitions). Use partial indexes for active versions. Archive old partitions. |
| **Orphaned version rows (root deleted but versions remain)** | Medium | Low — storage waste | Soft-delete cascades: when root is archived, all versions are marked as archived. No hard deletes. |
| **Rollback creates version that references non-existent previous_version_id** | Low | Critical — broken version chain | Foreign key constraint on `previous_version_id` prevents this. Always set `previous_version_id` to the current version at the time of rollback creation. |
| **Version history grows faster than archiving can keep up** | Medium | Medium — active storage exceeds budget | Monitor version table growth. Auto-scale archiving frequency. Alert on growth rate > 2× expected. |
| **API accidentally returns full version history with full content** | Medium | Medium — massive API response | API returns version history as metadata only. Full content requires explicit version request. Enforce at API gateway level. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Developer forgets to create a version row when updating content** | Medium | High — content update without version history | Enforce at the repository level: all content modifications go through the `createNewVersion()` method. Direct `StoryRepository.save()` on content fields is forbidden. ArchUnit test enforces this. |
| **Direct database UPDATE bypasses versioning** | Low | Critical — silent data loss | PostgreSQL triggers prevent UPDATE on version tables. RLS policies prevent direct UPDATE on aggregate root content fields (only `current_version_id`, `status`, `updated_*`, `deleted_*` are updatable). |
| **Storage costs exceed budget due to rapid versioning** | Low | Medium — unexpected cloud storage costs | Set per-entity version limits (max 50 versions per story). Alert when approaching limit. Implement aggressive archiving for high-churn entities. |
| **Backup/Restore complexity with version tables** | Medium | Low — longer restore times | Version tables are backed up as part of the standard PostgreSQL backup. Restore time is proportional to total data size, not version count. Archived versions on cold storage have separate backup procedures. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Collaborative branching required** | Linear version chain cannot support branches | Introduce `parent_version_id` (optional, supports multiple parents for merge) and `branch` field. This is a backward-compatible schema addition. |
| **Temporal query performance degrades** | Querying "state as of timestamp" requires scanning versions | Implement materialized snapshot tables for common time points (daily snapshots). Use version table partitioning by creation date. |
| **Version count per entity exceeds 1,000** | Version history becomes unwieldy | Implement version compaction: collapse sequential versions with the same `change_type` and `created_by` into a single version. This is lossy — only use when necessary. |
| **Multi-entity atomic versioning required** | Cannot atomically version a story + its claims + its articles | Implement distributed transaction coordination (saga pattern) across versions. This is a significant architectural addition — only pursue if the business requirement is proven. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Collaborative editing requires branching**: If multiple editors need to work on different versions simultaneously (e.g., Editor A works on a narrative article while Editor B works on a knowledge article derived from the same story), the linear version chain must be extended to support branching. This requires adding `branch` and `parent_version_id` fields to the version table.

2. **Version count per entity exceeds 1,000**: At this scale, version history management becomes complex. Consider version compaction, automated archiving, or restricting version creation to specific change types.

3. **Regulatory requirements mandate exact temporal queries**: If auditors require "show me the exact state of this story as of June 1, 2026, 3:00 PM UTC," implement materialized temporal snapshots or temporal tables (PostgreSQL `tsrange` with exclusion constraints).

4. **Cross-entity atomic versioning required**: If a single operation must atomically create versions across multiple entities (e.g., "update story v5, create knowledge object v3, and create claim v2 as a single transaction"), implement saga-based distributed versioning or move to event sourcing for the affected bounded contexts.

5. **Storage costs become prohibitive**: If version storage exceeds 100GB, implement more aggressive archiving, compress version content, or move to content-addressable storage for deduplication.

6. **Microservices extraction changes versioning boundaries**: If a module is extracted to a microservice (per ADR-002 extraction strategy), the versioning tables move with the service. The aggregate root + version rows pattern remains the same, but cross-service version queries require API composition or event-driven replication.

# References

- **Backend Platform PRD §3.7** — "Immutable Versioning" — Updates create new versions. Never overwrite.
- **Backend Platform PRD §12** — "Audit Requirements" — `created_at`, `created_by`, `updated_at`, `updated_by`, `version` on every business table.
- **Backend Platform PRD §9** — "State Machines" — Status transitions independent of version creation.
- **ADR-001: PostgreSQL as Source of Truth** — Version data stored in PostgreSQL, projected to Neo4j/Weaviate.
- **ADR-003: Event-Driven Architecture** — `StoryVersionCreated` event emitted on version creation.
- **ADR-004: Queue-Driven AI Platform** — AI workers create new versions, not overwrite.
- **ADR-007: Canonical Story Core Contract** — Canonical Story versions are immutable — aligns with this ADR.
- **Event Sourcing** — https://martinfowler.com/eaaDev/EventSourcing.html — Pattern for storing state as event stream (future consideration).
- **PostgreSQL Temporal Tables** — https://www.postgresql.org/docs/18/rangetypes.html — Range types for temporal modeling (future consideration).
- **Git Data Model** — https://git-scm.com/book/en/v2/Git-Internals-Git-Objects — Content-addressable storage (alternative considered).