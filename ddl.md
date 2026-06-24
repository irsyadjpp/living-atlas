Untuk platform seperti **The Living Atlas of Indonesian Mystery Culture**, ini adalah pilihan yang paling masuk akal karena:

```text
Global Knowledge
=
Shared

Story
Theme
Motif
Folklore
Culture
Region
Belief
Tradition

--------------------------------

Tenant Knowledge
=
Isolated

Workspace
Collection
Research
Annotation
Note
Private Story
Private Knowledge
```

---

# PostgreSQL 18 DDL Strategy

Saya akan menggunakan standar:

```sql
snake_case

pk_<table>
fk_<table>_<ref>

idx_<table>_<field>

uq_<table>_<field>

chk_<table>_<rule>
```

---

# EXTENSIONS

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

---

# SCHEMAS

```sql
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS iam;
CREATE SCHEMA IF NOT EXISTS tenant;

CREATE SCHEMA IF NOT EXISTS source;
CREATE SCHEMA IF NOT EXISTS content;

CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE SCHEMA IF NOT EXISTS culture;

CREATE SCHEMA IF NOT EXISTS research;
CREATE SCHEMA IF NOT EXISTS ai;

CREATE SCHEMA IF NOT EXISTS governance;
CREATE SCHEMA IF NOT EXISTS workflow;

CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS system;
```

---

# ENUMS

Saya sarankan ENUM hanya untuk nilai yang benar-benar stabil.

---

## tenant_type

```sql
CREATE TYPE tenant.tenant_type AS ENUM (
    'individual',
    'research',
    'publisher',
    'production_house',
    'university',
    'government'
);
```

---

## tenant_status

```sql
CREATE TYPE tenant.tenant_status AS ENUM (
    'active',
    'suspended',
    'archived'
);
```

---

## user_status

```sql
CREATE TYPE auth.user_status AS ENUM (
    'pending',
    'active',
    'blocked',
    'deleted'
);
```

---

# SYSTEM TABLES

---

## system.countries

```sql
CREATE TABLE system.countries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(3) NOT NULL UNIQUE,

    name VARCHAR(255) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

# TENANT DOMAIN

---

## tenant.tenants

```sql
CREATE TABLE tenant.tenants (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    slug VARCHAR(255) NOT NULL UNIQUE,

    name VARCHAR(255) NOT NULL,

    tenant_type tenant.tenant_type NOT NULL,

    status tenant.tenant_status NOT NULL DEFAULT 'active',

    subscription_plan VARCHAR(100),

    description TEXT,

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,

    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    version BIGINT NOT NULL DEFAULT 1,

    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
```

---

Indexes

```sql
CREATE INDEX idx_tenants_created_at
ON tenant.tenants(created_at DESC);

CREATE INDEX idx_tenants_status
ON tenant.tenants(status);

CREATE INDEX idx_tenants_metadata
ON tenant.tenants
USING GIN(metadata);
```

---

## tenant.workspaces

```sql
CREATE TABLE tenant.workspaces (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    tenant_id UUID NOT NULL,

    slug VARCHAR(255) NOT NULL,

    name VARCHAR(255) NOT NULL,

    workspace_type VARCHAR(100) NOT NULL,

    visibility VARCHAR(50) NOT NULL DEFAULT 'private',

    description TEXT,

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,

    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    version BIGINT NOT NULL DEFAULT 1,

    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT fk_workspaces_tenant
        FOREIGN KEY (tenant_id)
        REFERENCES tenant.tenants(id)
);
```

---

Unique

```sql
CREATE UNIQUE INDEX uq_workspace_slug
ON tenant.workspaces(tenant_id, slug);
```

---

# AUTH DOMAIN

---

## auth.users

```sql
CREATE TABLE auth.users (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    email CITEXT NOT NULL UNIQUE,

    username CITEXT NOT NULL UNIQUE,

    display_name VARCHAR(255),

    avatar_url TEXT,

    status auth.user_status NOT NULL DEFAULT 'pending',

    email_verified BOOLEAN NOT NULL DEFAULT FALSE,

    last_login_at TIMESTAMPTZ,

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,

    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    version BIGINT NOT NULL DEFAULT 1,

    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
```

---

Indexes

```sql
CREATE INDEX idx_users_email
ON auth.users(email);

CREATE INDEX idx_users_username
ON auth.users(username);

CREATE INDEX idx_users_status
ON auth.users(status);
```

---

# IAM DOMAIN

---

## iam.roles

```sql
CREATE TABLE iam.roles (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(100) NOT NULL UNIQUE,

    name VARCHAR(255) NOT NULL,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## iam.permissions

```sql
CREATE TABLE iam.permissions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(255) NOT NULL UNIQUE,

    resource_type VARCHAR(100) NOT NULL,

    action VARCHAR(100) NOT NULL,

    description TEXT
);
```

---

## iam.role_permissions

```sql
CREATE TABLE iam.role_permissions (

    role_id UUID NOT NULL,

    permission_id UUID NOT NULL,

    PRIMARY KEY(role_id, permission_id),

    CONSTRAINT fk_role_permissions_role
        FOREIGN KEY(role_id)
        REFERENCES iam.roles(id),

    CONSTRAINT fk_role_permissions_permission
        FOREIGN KEY(permission_id)
        REFERENCES iam.permissions(id)
);
```

---

## iam.user_roles

```sql
CREATE TABLE iam.user_roles (

    user_id UUID NOT NULL,

    role_id UUID NOT NULL,

    tenant_id UUID,

    workspace_id UUID,

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    assigned_by UUID,

    PRIMARY KEY (
        user_id,
        role_id,
        tenant_id,
        workspace_id
    )
);
```

---

# ABAC DOMAIN

Ini yang membedakan platform ini dari CMS biasa.

---

## iam.policies

```sql
CREATE TABLE iam.policies (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    code VARCHAR(255) NOT NULL UNIQUE,

    name VARCHAR(255) NOT NULL,

    effect VARCHAR(20) NOT NULL,

    description TEXT,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## iam.policy_rules

```sql
CREATE TABLE iam.policy_rules (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    policy_id UUID NOT NULL,

    rule_order INTEGER NOT NULL,

    rule_expression JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_policy_rules_policy
        FOREIGN KEY(policy_id)
        REFERENCES iam.policies(id)
);
```

---

Contoh:

```json
{
  "subject.role":"researcher",
  "resource.status":"published",
  "resource.type":"knowledge_article"
}
```

---

# GOVERNANCE DOMAIN

Ini akan menjadi sangat penting nanti.

---

## governance.audit_logs

```sql
CREATE TABLE governance.audit_logs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    actor_id UUID,

    tenant_id UUID,

    action VARCHAR(100) NOT NULL,

    resource_type VARCHAR(100) NOT NULL,

    resource_id UUID,

    old_value JSONB,

    new_value JSONB,

    ip_address INET,

    user_agent TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
PARTITION BY RANGE(created_at);
```

---

Monthly partitions:

```sql
CREATE TABLE governance.audit_logs_2026_06
PARTITION OF governance.audit_logs
FOR VALUES FROM ('2026-06-01')
TO ('2026-07-01');
```

---

Indexes

```sql
CREATE INDEX idx_audit_actor
ON governance.audit_logs(actor_id);

CREATE INDEX idx_audit_resource
ON governance.audit_logs(resource_type, resource_id);

CREATE INDEX idx_audit_created_at
ON governance.audit_logs(created_at DESC);
```

---

# GOVERNANCE LINEAGE

---

## governance.lineage

```sql
CREATE TABLE governance.lineage (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_type VARCHAR(100) NOT NULL,

    source_id UUID NOT NULL,

    target_type VARCHAR(100) NOT NULL,

    target_id UUID NOT NULL,

    relationship_type VARCHAR(100) NOT NULL,

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Contoh:

```text
Video
→ Transcript

Transcript
→ Story

Story
→ Article

Article
→ Knowledge Object

Knowledge Object
→ Neo4j Node

Knowledge Object
→ Weaviate Object
```

---


### Soft Delete vs Hard Delete

Untuk Living Atlas saya merekomendasikan:

```text
Knowledge Domain      → Never Delete

Content Domain        → Soft Delete

Source Domain         → Soft Delete

Governance Domain     → Never Delete

Audit Domain          → Never Delete
```

---

Bagus. Sebelum masuk ke Phase 2, saya ingin melakukan sedikit koreksi terhadap desain sebelumnya.

Untuk **The Living Atlas**, Source Domain bukan sekadar menyimpan video.

Source Domain adalah:

```text
Acquisition Layer
+
Evidence Layer
+
Provenance Layer
```

Artinya semua Knowledge Object harus bisa ditelusuri kembali ke:

```text
Knowledge Object
↓
Transcript Segment
↓
Transcript Version
↓
Video
↓
Playlist
↓
Channel
↓
Raw Payload
```

Ini akan sangat penting untuk antropolog, peneliti, dan audit AI.

---


# SOURCE INGESTION DOMAIN

Schema:

```sql
source
```

Subdomain:

```text
Source Registry

Channels
Playlists
Videos

Raw Payload

Assets

Subtitle

Transcript

Speaker

Comment

Ingestion

Extraction
```

---

# ENUMS

## Platform

```sql
CREATE TYPE source.platform_type AS ENUM (
    'youtube',
    'spotify',
    'apple_podcast',
    'rss',
    'book',
    'website',
    'manual'
);
```

---

## Asset Type

```sql
CREATE TYPE source.asset_type AS ENUM (
    'video',
    'audio',
    'thumbnail',
    'subtitle',
    'transcript',
    'image',
    'pdf'
);
```

---

## Transcript Type

```sql
CREATE TYPE source.transcript_type AS ENUM (
    'human_subtitle',
    'auto_subtitle',
    'whisperx',
    'edited'
);
```

---

## Job Status

```sql
CREATE TYPE source.job_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled'
);
```

---

# SOURCE CHANNELS

## source.channels

```sql
CREATE TABLE source.channels (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    platform source.platform_type NOT NULL,

    platform_channel_id VARCHAR(255) NOT NULL,

    slug VARCHAR(255),

    name VARCHAR(500) NOT NULL,

    description TEXT,

    country_code VARCHAR(10),

    language_code VARCHAR(20),

    channel_url TEXT,

    custom_url TEXT,

    avatar_url TEXT,

    banner_url TEXT,

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,

    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    version BIGINT NOT NULL DEFAULT 1,

    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT uq_channels_platform_channel
        UNIQUE(platform, platform_channel_id)
);
```

Indexes:

```sql
CREATE INDEX idx_channels_platform
ON source.channels(platform);

CREATE INDEX idx_channels_name
ON source.channels
USING GIN(name gin_trgm_ops);

CREATE INDEX idx_channels_metadata
ON source.channels
USING GIN(metadata);
```

---

# CHANNEL SNAPSHOTS

Historical growth.

## source.channel_snapshots

```sql
CREATE TABLE source.channel_snapshots (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    channel_id UUID NOT NULL,

    subscriber_count BIGINT,

    video_count BIGINT,

    view_count BIGINT,

    metadata JSONB DEFAULT '{}',

    snapshot_at TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_channel_snapshots_channel
        FOREIGN KEY(channel_id)
        REFERENCES source.channels(id)
)
PARTITION BY RANGE(snapshot_at);
```

---

# PLAYLISTS

## source.playlists

```sql
CREATE TABLE source.playlists (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    channel_id UUID NOT NULL,

    platform_playlist_id VARCHAR(255) NOT NULL,

    title TEXT NOT NULL,

    description TEXT,

    playlist_url TEXT,

    video_count INTEGER,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_playlist_channel
        FOREIGN KEY(channel_id)
        REFERENCES source.channels(id),

    CONSTRAINT uq_playlist_platform
        UNIQUE(platform_playlist_id)
);
```

---

# PLAYLIST SNAPSHOT

Playlist berubah dari waktu ke waktu.

```sql
CREATE TABLE source.playlist_snapshots (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    playlist_id UUID NOT NULL,

    title TEXT,

    description TEXT,

    video_count INTEGER,

    metadata JSONB,

    snapshot_at TIMESTAMPTZ NOT NULL
);
```

---

# VIDEOS

Pusat seluruh ingestion.

## source.videos

```sql
CREATE TABLE source.videos (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    channel_id UUID NOT NULL,

    playlist_id UUID,

    platform_video_id VARCHAR(255) NOT NULL,

    title TEXT NOT NULL,

    description TEXT,

    language_code VARCHAR(20),

    published_at TIMESTAMPTZ,

    duration_seconds INTEGER,

    view_count BIGINT,

    like_count BIGINT,

    comment_count BIGINT,

    video_url TEXT,

    current_payload_version_id UUID,

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    deleted_at TIMESTAMPTZ,

    version BIGINT NOT NULL DEFAULT 1,

    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,

    CONSTRAINT uq_platform_video
        UNIQUE(platform_video_id),

    CONSTRAINT fk_video_channel
        FOREIGN KEY(channel_id)
        REFERENCES source.channels(id)
);
```

Indexes:

```sql
CREATE INDEX idx_videos_published
ON source.videos(published_at DESC);

CREATE INDEX idx_videos_channel
ON source.videos(channel_id);

CREATE INDEX idx_videos_metadata
ON source.videos
USING GIN(metadata);
```

---

# VIDEO PAYLOAD VERSIONS

Raw YT-DLP.

Tidak boleh diubah.

## source.video_payload_versions

```sql
CREATE TABLE source.video_payload_versions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID NOT NULL,

    payload_hash TEXT NOT NULL,

    extractor_name VARCHAR(100),

    extractor_version VARCHAR(100),

    payload JSONB NOT NULL,

    collected_at TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_payload_video
        FOREIGN KEY(video_id)
        REFERENCES source.videos(id)
);
```

Indexes:

```sql
CREATE INDEX idx_payload_video
ON source.video_payload_versions(video_id);

CREATE INDEX idx_payload_json
ON source.video_payload_versions
USING GIN(payload jsonb_path_ops);
```

---

# VIDEO FORMATS

Semua format hasil YT-DLP.

```sql
CREATE TABLE source.video_formats (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    payload_version_id UUID NOT NULL,

    format_id VARCHAR(50),

    ext VARCHAR(20),

    resolution VARCHAR(100),

    fps INTEGER,

    vcodec TEXT,

    acodec TEXT,

    filesize BIGINT,

    metadata JSONB
);
```

---

# VIDEO CHAPTERS

```sql
CREATE TABLE source.video_chapters (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID NOT NULL,

    start_seconds NUMERIC(12,3),

    end_seconds NUMERIC(12,3),

    title TEXT NOT NULL
);
```

---

# VIDEO TAGS

```sql
CREATE TABLE source.video_tags (

    video_id UUID NOT NULL,

    tag TEXT NOT NULL,

    PRIMARY KEY(video_id, tag)
);
```

---

# THUMBNAILS

```sql
CREATE TABLE source.video_thumbnails (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID NOT NULL,

    thumbnail_url TEXT,

    width INTEGER,

    height INTEGER,

    preference INTEGER,

    metadata JSONB
);
```

---

# ASSETS

Audio hasil ffmpeg.

Subtitle hasil download.

PDF jika ada.

```sql
CREATE TABLE source.assets (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID,

    asset_type source.asset_type NOT NULL,

    storage_path TEXT NOT NULL,

    mime_type TEXT,

    checksum TEXT,

    file_size BIGINT,

    metadata JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

# SUBTITLE TRACKS

```sql
CREATE TABLE source.subtitle_tracks (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID NOT NULL,

    language_code VARCHAR(20),

    is_auto_generated BOOLEAN,

    subtitle_url TEXT,

    subtitle_format VARCHAR(20),

    metadata JSONB
);
```

---

# TRANSCRIPTS

Versioned.

Immutable.

```sql
CREATE TABLE source.transcripts (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID NOT NULL,

    transcript_type source.transcript_type NOT NULL,

    language_code VARCHAR(20),

    version_number INTEGER NOT NULL,

    checksum TEXT,

    word_count INTEGER,

    content TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

# SPEAKERS

Pyannote output.

```sql
CREATE TABLE source.speakers (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID NOT NULL,

    speaker_name TEXT,

    speaker_type VARCHAR(100),

    confidence_score NUMERIC(5,2),

    metadata JSONB
);
```

---

# TRANSCRIPT SEGMENTS

Ini yang akan menjadi sumber Knowledge Graph.

```sql
CREATE TABLE source.transcript_segments (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    transcript_id UUID NOT NULL,

    speaker_id UUID,

    start_seconds NUMERIC(12,3),

    end_seconds NUMERIC(12,3),

    content TEXT NOT NULL,

    embedding_status VARCHAR(50),

    metadata JSONB,

    CONSTRAINT fk_segment_transcript
        FOREIGN KEY(transcript_id)
        REFERENCES source.transcripts(id)
);
```

Index:

```sql
CREATE INDEX idx_segment_transcript
ON source.transcript_segments(transcript_id);

CREATE INDEX idx_segment_speaker
ON source.transcript_segments(speaker_id);
```

---

# COMMENTS

Sangat berharga untuk lore tambahan.

## source.video_comments

```sql
CREATE TABLE source.video_comments (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    video_id UUID NOT NULL,

    platform_comment_id VARCHAR(255),

    parent_comment_id VARCHAR(255),

    author_name TEXT,

    author_channel_id TEXT,

    content TEXT,

    like_count BIGINT,

    published_at TIMESTAMPTZ,

    metadata JSONB
)
PARTITION BY HASH(video_id);
```

---

# INGESTION JOBS

Audit pipeline.

```sql
CREATE TABLE source.ingestion_jobs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_type VARCHAR(100),

    target_id UUID,

    status source.job_status NOT NULL,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    error_message TEXT,

    metadata JSONB
);
```

---

# EXTRACTION JOBS

```sql
CREATE TABLE source.extraction_jobs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    transcript_id UUID,

    model_name VARCHAR(255),

    model_version VARCHAR(255),

    status source.job_status,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    metadata JSONB
);
```

---

SOURCE INGESTION DOMAIN sudah mampu:

```text
✓ Crawl Channel

✓ Crawl Playlist

✓ Crawl Video

✓ Simpan Full YT-DLP Metadata

✓ Simpan Full Raw JSON

✓ Simpan Historical Snapshot

✓ Simpan Subtitle

✓ Simpan Transcript

✓ Simpan Speaker Diarization

✓ Simpan Comments

✓ Audit Ingestion

✓ Audit Extraction

✓ Data Lineage Ready
```

---


Saya menyarankan struktur:

```text
Knowledge Object
    ↓
Entity
    ↓
Concept
    ↓
Story
    ↓
Narrative Pattern
    ↓
Cultural Relationship
```

Karena suatu saat Anda akan memiliki:

* Video
* Podcast
* Buku
* Artikel
* Manuskrip
* Wawancara
* Arsip kolonial
* Cerita rakyat

yang semuanya menghasilkan knowledge object yang sama.

---



```sql
knowledge
culture
```

---

# ENUMS

## Entity Type

```sql
CREATE TYPE knowledge.entity_type AS ENUM (

    'folklore',

    'spirit',
    'ghost',
    'entity',

    'person',
    'character',

    'location',

    'ritual',

    'belief',

    'tradition',

    'artifact',

    'symbol',

    'event',

    'organization',

    'creature',

    'mythological_being'
);
```

---

## Evidence Level

```sql
CREATE TYPE knowledge.evidence_level AS ENUM (

    'direct',

    'derived',

    'inferred',

    'generated'
);
```

---

## Story Type

```sql
CREATE TYPE content.story_type AS ENUM (

    'investigation',

    'personal_experience',

    'folklore',

    'urban_legend',

    'historical',

    'cultural',

    'ritual',

    'mythology',

    'podcast_discussion'
);
```

---

# KNOWLEDGE OBJECTS

Semua objek pengetahuan berasal dari sini.

---

## knowledge.objects

```sql
CREATE TABLE knowledge.objects (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    object_type VARCHAR(100) NOT NULL,

    canonical_name TEXT NOT NULL,

    slug VARCHAR(500) NOT NULL UNIQUE,

    summary TEXT,

    confidence_score NUMERIC(5,2),

    status VARCHAR(50) NOT NULL DEFAULT 'active',

    metadata JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,

    deleted_at TIMESTAMPTZ,

    version BIGINT NOT NULL DEFAULT 1,

    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);
```

---

Index

```sql
CREATE INDEX idx_knowledge_objects_name
ON knowledge.objects
USING GIN(canonical_name gin_trgm_ops);

CREATE INDEX idx_knowledge_objects_metadata
ON knowledge.objects
USING GIN(metadata);
```

---

# ALIASES

Karena satu entitas bisa punya banyak nama.

---

## knowledge.object_aliases

```sql
CREATE TABLE knowledge.object_aliases (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    object_id UUID NOT NULL,

    alias_name TEXT NOT NULL,

    language_code VARCHAR(20),

    is_primary BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT fk_alias_object
        FOREIGN KEY(object_id)
        REFERENCES knowledge.objects(id)
);
```

Contoh:

```text
Kuntilanak
Pontianak
Ponti
```

---

# ENTITYS

Layer khusus entity.

---

## knowledge.entities

```sql
CREATE TABLE knowledge.entities (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    object_id UUID NOT NULL UNIQUE,

    entity_type knowledge.entity_type NOT NULL,

    description TEXT,

    metadata JSONB DEFAULT '{}',

    CONSTRAINT fk_entity_object
        FOREIGN KEY(object_id)
        REFERENCES knowledge.objects(id)
);
```

---

# FOLKLORE

---

## knowledge.folklore_entities

```sql
CREATE TABLE knowledge.folklore_entities (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID NOT NULL UNIQUE,

    folklore_category VARCHAR(100),

    first_known_reference TEXT,

    origin_story TEXT,

    appearance_description TEXT,

    behavior_description TEXT,

    metadata JSONB DEFAULT '{}',

    CONSTRAINT fk_folklore_entity
        FOREIGN KEY(entity_id)
        REFERENCES knowledge.entities(id)
);
```

---

# CHARACTERS

---

## knowledge.characters

```sql
CREATE TABLE knowledge.characters (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID NOT NULL UNIQUE,

    character_type VARCHAR(100),

    biography TEXT,

    metadata JSONB DEFAULT '{}'
);
```

---

# LOCATIONS

Rahasiakan koordinat asli.

---

## knowledge.locations

```sql
CREATE TABLE knowledge.locations (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID NOT NULL UNIQUE,

    location_name TEXT,

    location_type VARCHAR(100),

    latitude NUMERIC(12,8),

    longitude NUMERIC(12,8),

    is_sensitive BOOLEAN DEFAULT FALSE,

    public_region_id UUID,

    metadata JSONB DEFAULT '{}'
);
```

---

**Penting**

Untuk Jurnal Risa, Nadia Omara, dsb:

```text
Lokasi asli
=
Private

Lokasi publik
=
Kabupaten/Kota/Provinsi
```

---

# CULTURE DOMAIN

---

## culture.cultures

```sql
CREATE TABLE culture.cultures (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name TEXT NOT NULL,

    slug VARCHAR(255) UNIQUE,

    description TEXT,

    metadata JSONB DEFAULT '{}'
);
```

---

## culture.ethnic_groups

```sql
CREATE TABLE culture.ethnic_groups (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    culture_id UUID,

    name TEXT NOT NULL,

    description TEXT,

    metadata JSONB DEFAULT '{}'
);
```

---

## culture.regions

```sql
CREATE TABLE culture.regions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    parent_region_id UUID,

    name TEXT NOT NULL,

    region_type VARCHAR(100),

    country_code VARCHAR(10),

    metadata JSONB DEFAULT '{}'
);
```

---

Contoh:

```text
Indonesia

Sulawesi Selatan

Selayar

Bontoharu
```

---

# BELIEF SYSTEMS

---

## culture.beliefs

```sql
CREATE TABLE culture.beliefs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name TEXT NOT NULL,

    description TEXT,

    metadata JSONB DEFAULT '{}'
);
```

---

## culture.traditions

```sql
CREATE TABLE culture.traditions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name TEXT NOT NULL,

    description TEXT,

    metadata JSONB DEFAULT '{}'
);
```

---

## culture.rituals

```sql
CREATE TABLE culture.rituals (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name TEXT NOT NULL,

    description TEXT,

    metadata JSONB DEFAULT '{}'
);
```

---

# THEMES

---

## knowledge.themes

```sql
CREATE TABLE knowledge.themes (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    slug VARCHAR(255) UNIQUE,

    name TEXT NOT NULL,

    description TEXT,

    metadata JSONB DEFAULT '{}'
);
```

Contoh:

```text
Fear

Loss

Afterlife

Curiosity

Forbidden Place

Ancestral Spirits
```

---

# MOTIFS

---

## knowledge.motifs

```sql
CREATE TABLE knowledge.motifs (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    slug VARCHAR(255) UNIQUE,

    name TEXT NOT NULL,

    description TEXT
);
```

Contoh:

```text
Mysterious Voice

Shadow Figure

Abandoned House

Sacred Tree

Possession
```

---

# ARCHETYPES

---

## knowledge.archetypes

```sql
CREATE TABLE knowledge.archetypes (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    slug VARCHAR(255) UNIQUE,

    name TEXT NOT NULL,

    description TEXT
);
```

---

# NARRATIVE PATTERNS

---

## knowledge.narrative_patterns

```sql
CREATE TABLE knowledge.narrative_patterns (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    slug VARCHAR(255) UNIQUE,

    name TEXT NOT NULL,

    description TEXT
);
```

Contoh:

```text
Warning Ignored

Investigation

Witness Testimony

Encounter

Ritual Failure

Curiosity Leads To Consequence
```

---

# STORIES

Ini jantung platform.

---

## content.stories

```sql
CREATE TABLE content.stories (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    slug VARCHAR(500) UNIQUE,

    title TEXT NOT NULL,

    summary TEXT,

    story_type content.story_type NOT NULL,

    confidence_score NUMERIC(5,2),

    canonical_source_video_id UUID,

    status VARCHAR(50),

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT now(),

    updated_at TIMESTAMPTZ DEFAULT now()
);
```

---

# STORY VERSIONS

Immutable.

---

## content.story_versions

```sql
CREATE TABLE content.story_versions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    story_id UUID NOT NULL,

    version_number INTEGER NOT NULL,

    title TEXT,

    summary TEXT,

    content JSONB NOT NULL,

    created_at TIMESTAMPTZ DEFAULT now(),

    created_by UUID
);
```

---

# STORY EVIDENCE

Ini sangat penting untuk penelitian.

---

## content.story_evidence

```sql
CREATE TABLE content.story_evidence (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    story_id UUID NOT NULL,

    transcript_segment_id UUID,

    evidence_level knowledge.evidence_level NOT NULL,

    confidence_score NUMERIC(5,2),

    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# STORY GENOME

Ini aset masa depan.

---

## research.story_genomes

```sql
CREATE TABLE research.story_genomes (

    story_id UUID PRIMARY KEY,

    theme_vector JSONB,

    motif_vector JSONB,

    archetype_vector JSONB,

    narrative_pattern_vector JSONB,

    culture_vector JSONB,

    emotion_vector JSONB,

    metadata JSONB DEFAULT '{}'
);
```

---

# STORY RELATIONSHIPS

---

## knowledge.story_entities

```sql
CREATE TABLE knowledge.story_entities (

    story_id UUID NOT NULL,

    entity_id UUID NOT NULL,

    confidence_score NUMERIC(5,2),

    PRIMARY KEY(story_id, entity_id)
);
```

---

## knowledge.story_themes

```sql
CREATE TABLE knowledge.story_themes (

    story_id UUID NOT NULL,

    theme_id UUID NOT NULL,

    weight NUMERIC(5,2),

    PRIMARY KEY(story_id, theme_id)
);
```

---

## knowledge.story_motifs

```sql
CREATE TABLE knowledge.story_motifs (

    story_id UUID NOT NULL,

    motif_id UUID NOT NULL,

    weight NUMERIC(5,2),

    PRIMARY KEY(story_id, motif_id)
);
```

---

## knowledge.story_patterns

```sql
CREATE TABLE knowledge.story_patterns (

    story_id UUID NOT NULL,

    pattern_id UUID NOT NULL,

    weight NUMERIC(5,2),

    PRIMARY KEY(story_id, pattern_id)
);
```

---

Phase 3.5 adalah bagian yang menurut saya justru akan menjadi **moat (competitive advantage)** platform Anda.

Karena setelah Phase 3, hampir semua orang bisa membuat:

```text
Story
Theme
Motif
Culture
Folklore
Graph
```

Tetapi yang sulit adalah:

```text
Knowledge Quality
Knowledge Provenance
Knowledge Contradiction
Knowledge Evolution
Knowledge Intelligence
```

---


# KNOWLEDGE INTELLIGENCE LAYER

Schema:

```sql
knowledge
research
governance
```

---

# 1. KNOWLEDGE CLAIMS

Setiap cerita mengandung banyak klaim.

Contoh:

```text
Kuyang berasal dari Kalimantan.

Pohon tertentu dianggap keramat.

Ada ritual tertentu sebelum memasuki lokasi.
```

Jangan langsung simpan sebagai fakta.

Simpan sebagai CLAIM.

---

## knowledge.claims

```sql
CREATE TABLE knowledge.claims (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    claim_text TEXT NOT NULL,

    claim_type VARCHAR(100),

    confidence_score NUMERIC(5,2),

    extraction_method VARCHAR(100),

    status VARCHAR(50) NOT NULL DEFAULT 'unverified',

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    created_by UUID
);
```

---

## knowledge.claim_sources

```sql
CREATE TABLE knowledge.claim_sources (

    claim_id UUID NOT NULL,

    transcript_segment_id UUID NOT NULL,

    evidence_level knowledge.evidence_level NOT NULL,

    confidence_score NUMERIC(5,2),

    PRIMARY KEY(
        claim_id,
        transcript_segment_id
    )
);
```

---

# 2. KNOWLEDGE ASSERTIONS

Claim dapat menghasilkan assertion.

Contoh:

```text
Kuyang

ASSOCIATED_WITH

Dayak
```

---

## knowledge.assertions

```sql
CREATE TABLE knowledge.assertions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    subject_entity_id UUID NOT NULL,

    predicate VARCHAR(100) NOT NULL,

    object_entity_id UUID,

    object_value TEXT,

    confidence_score NUMERIC(5,2),

    status VARCHAR(50) DEFAULT 'candidate',

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

Contoh:

```text
Kuyang
  associated_with
Dayak

Kuntilanak
  appears_in
Pontianak
```

---

# 3. CONTRADICTIONS

Sangat penting untuk antropologi.

Karena folklore sering memiliki versi berbeda.

---

## knowledge.contradictions

```sql
CREATE TABLE knowledge.contradictions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID NOT NULL,

    contradiction_type VARCHAR(100),

    description TEXT,

    severity VARCHAR(50),

    status VARCHAR(50),

    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## knowledge.contradiction_claims

```sql
CREATE TABLE knowledge.contradiction_claims (

    contradiction_id UUID NOT NULL,

    claim_id UUID NOT NULL,

    PRIMARY KEY(
        contradiction_id,
        claim_id
    )
);
```

---

Contoh:

```text
Versi A

Kuyang berasal dari Dayak

Versi B

Kuyang berasal dari Banjar
```

Tidak ada yang dihapus.

Keduanya disimpan.

---

# 4. KNOWLEDGE SOURCES

Untuk citation.

---

## knowledge.sources

```sql
CREATE TABLE knowledge.sources (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_type VARCHAR(100),

    source_reference TEXT,

    title TEXT,

    author TEXT,

    publication_year INTEGER,

    metadata JSONB DEFAULT '{}'
);
```

---

## knowledge.citations

```sql
CREATE TABLE knowledge.citations (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_id UUID NOT NULL,

    target_type VARCHAR(100),

    target_id UUID NOT NULL,

    citation_note TEXT,

    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 5. KNOWLEDGE EVOLUTION

Knowledge berubah dari waktu ke waktu.

---

## knowledge.entity_versions

```sql
CREATE TABLE knowledge.entity_versions (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID NOT NULL,

    version_number INTEGER NOT NULL,

    content JSONB NOT NULL,

    created_at TIMESTAMPTZ DEFAULT now(),

    created_by UUID
);
```

---

## knowledge.entity_change_log

```sql
CREATE TABLE knowledge.entity_change_log (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID NOT NULL,

    change_type VARCHAR(100),

    old_value JSONB,

    new_value JSONB,

    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

# 6. STORY SIMILARITY ENGINE

Aset besar untuk:

```text
Production House

Writer

Researchers
```

---

## research.story_similarity

```sql
CREATE TABLE research.story_similarity (

    story_id_a UUID NOT NULL,

    story_id_b UUID NOT NULL,

    similarity_score NUMERIC(8,6),

    similarity_method VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT now(),

    PRIMARY KEY(
        story_id_a,
        story_id_b
    )
);
```

---

# 7. NARRATIVE DNA

Inilah inti "Story Genome".

---

## research.narrative_dna

```sql
CREATE TABLE research.narrative_dna (

    story_id UUID PRIMARY KEY,

    dna_version INTEGER NOT NULL,

    motif_vector JSONB,

    archetype_vector JSONB,

    narrative_vector JSONB,

    emotional_vector JSONB,

    cultural_vector JSONB,

    metadata JSONB DEFAULT '{}'
);
```

---

Contoh:

```json
{
  "investigation": 0.92,
  "warning_ignored": 0.81,
  "encounter": 0.88,
  "ritual_failure": 0.31
}
```

---

# 8. ADAPTATION INTELLIGENCE

Ini yang dicari Production House.

---

## research.adaptation_scores

```sql
CREATE TABLE research.adaptation_scores (

    story_id UUID PRIMARY KEY,

    movie_score NUMERIC(5,2),

    series_score NUMERIC(5,2),

    documentary_score NUMERIC(5,2),

    podcast_score NUMERIC(5,2),

    novel_score NUMERIC(5,2),

    game_score NUMERIC(5,2),

    metadata JSONB DEFAULT '{}'
);
```

---

## research.adaptation_reasons

```sql
CREATE TABLE research.adaptation_reasons (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    story_id UUID NOT NULL,

    reason_type VARCHAR(100),

    score NUMERIC(5,2),

    explanation TEXT
);
```

---

# 9. CULTURAL EVOLUTION

Ini yang hampir tidak dimiliki platform lain.

---

## analytics.cultural_trends

```sql
CREATE TABLE analytics.cultural_trends (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_id UUID,

    region_id UUID,

    period_start DATE,

    period_end DATE,

    mention_count BIGINT,

    growth_rate NUMERIC(8,4),

    metadata JSONB DEFAULT '{}'
);
```

---

## analytics.theme_trends

```sql
CREATE TABLE analytics.theme_trends (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    theme_id UUID,

    period_start DATE,

    period_end DATE,

    mention_count BIGINT,

    growth_rate NUMERIC(8,4)
);
```

---

# 10. KNOWLEDGE QUALITY

Ini wajib jika menggunakan AI.

---

## governance.knowledge_reviews

```sql
CREATE TABLE governance.knowledge_reviews (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    target_type VARCHAR(100),

    target_id UUID,

    reviewer_id UUID,

    review_status VARCHAR(50),

    review_notes TEXT,

    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## governance.knowledge_quality_scores

```sql
CREATE TABLE governance.knowledge_quality_scores (

    target_type VARCHAR(100),

    target_id UUID,

    completeness_score NUMERIC(5,2),

    confidence_score NUMERIC(5,2),

    citation_score NUMERIC(5,2),

    consistency_score NUMERIC(5,2),

    freshness_score NUMERIC(5,2),

    overall_score NUMERIC(5,2),

    PRIMARY KEY(
        target_type,
        target_id
    )
);
```

---

# 11. MISSING KNOWLEDGE DETECTION

Sangat berguna untuk kreator dan peneliti.

---

## research.knowledge_gaps

```sql
CREATE TABLE research.knowledge_gaps (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    gap_type VARCHAR(100),

    entity_id UUID,

    description TEXT,

    priority_score NUMERIC(5,2),

    status VARCHAR(50),

    created_at TIMESTAMPTZ DEFAULT now()
);
```

Contoh:

```text
Kuntilanak:
- Banyak cerita
- Sedikit sumber budaya

Gap ditemukan.

Perlu penelitian tambahan.
```

---
