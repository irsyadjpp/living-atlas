-- Knowledge Domain Schema
-- Living Atlas of Indonesian Mystery Culture
-- Core knowledge graph and intelligence layer

-- ============================================================
-- ENUMS
-- ============================================================

DO $$
BEGIN
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
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- KNOWLEDGE OBJECTS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.objects (
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

CREATE INDEX IF NOT EXISTS idx_knowledge_objects_name ON knowledge.objects USING GIN(canonical_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_knowledge_objects_metadata ON knowledge.objects USING GIN(metadata);

-- ============================================================
-- OBJECT ALIASES
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.object_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_id UUID NOT NULL,
    alias_name TEXT NOT NULL,
    language_code VARCHAR(20),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT fk_alias_object FOREIGN KEY(object_id) REFERENCES knowledge.objects(id)
);

-- ============================================================
-- ENTITIES
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_id UUID NOT NULL UNIQUE,
    entity_type knowledge.entity_type NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT fk_entity_object FOREIGN KEY(object_id) REFERENCES knowledge.objects(id)
);

-- ============================================================
-- FOLKLORE ENTITIES
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.folklore_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL UNIQUE,
    folklore_category VARCHAR(100),
    first_known_reference TEXT,
    origin_story TEXT,
    appearance_description TEXT,
    behavior_description TEXT,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT fk_folklore_entity FOREIGN KEY(entity_id) REFERENCES knowledge.entities(id)
);

-- ============================================================
-- CHARACTERS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL UNIQUE,
    character_type VARCHAR(100),
    biography TEXT,
    metadata JSONB DEFAULT '{}'
);

-- ============================================================
-- LOCATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.locations (
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

-- ============================================================
-- THEMES
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.themes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}'
);

-- ============================================================
-- MOTIFS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.motifs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE,
    name TEXT NOT NULL,
    description TEXT
);

-- ============================================================
-- ARCHETYPES
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.archetypes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE,
    name TEXT NOT NULL,
    description TEXT
);

-- ============================================================
-- NARRATIVE PATTERNS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.narrative_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE,
    name TEXT NOT NULL,
    description TEXT
);

-- ============================================================
-- STORY RELATIONSHIPS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.story_entities (
    story_id UUID NOT NULL,
    entity_id UUID NOT NULL,
    confidence_score NUMERIC(5,2),
    PRIMARY KEY(story_id, entity_id)
);

CREATE TABLE IF NOT EXISTS knowledge.story_themes (
    story_id UUID NOT NULL,
    theme_id UUID NOT NULL,
    weight NUMERIC(5,2),
    PRIMARY KEY(story_id, theme_id)
);

CREATE TABLE IF NOT EXISTS knowledge.story_motifs (
    story_id UUID NOT NULL,
    motif_id UUID NOT NULL,
    weight NUMERIC(5,2),
    PRIMARY KEY(story_id, motif_id)
);

CREATE TABLE IF NOT EXISTS knowledge.story_patterns (
    story_id UUID NOT NULL,
    pattern_id UUID NOT NULL,
    weight NUMERIC(5,2),
    PRIMARY KEY(story_id, pattern_id)
);

-- ============================================================
-- KNOWLEDGE CLAIMS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.claims (
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

-- ============================================================
-- CLAIM SOURCES
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.claim_sources (
    claim_id UUID NOT NULL,
    transcript_segment_id UUID NOT NULL,
    evidence_level knowledge.evidence_level NOT NULL,
    confidence_score NUMERIC(5,2),
    PRIMARY KEY(claim_id, transcript_segment_id)
);

-- ============================================================
-- KNOWLEDGE ASSERTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.assertions (
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

-- ============================================================
-- CONTRADICTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    contradiction_type VARCHAR(100),
    description TEXT,
    severity VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- CONTRADICTION CLAIMS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.contradiction_claims (
    contradiction_id UUID NOT NULL,
    claim_id UUID NOT NULL,
    PRIMARY KEY(contradiction_id, claim_id)
);

-- ============================================================
-- KNOWLEDGE SOURCES
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(100),
    source_reference TEXT,
    title TEXT,
    author TEXT,
    publication_year INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- ============================================================
-- CITATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    target_type VARCHAR(100),
    target_id UUID NOT NULL,
    citation_note TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- KNOWLEDGE EVOLUTION
-- ============================================================

CREATE TABLE IF NOT EXISTS knowledge.entity_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID
);

CREATE TABLE IF NOT EXISTS knowledge.entity_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    change_type VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
