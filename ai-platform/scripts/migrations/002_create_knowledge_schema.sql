
-- ============================================================
-- Knowledge Schema - Enrichment Service Output
-- PRD v2.0 Compliance
-- ============================================================

-- Create knowledge schema if not exists
CREATE SCHEMA IF NOT EXISTS knowledge;

-- ============================================================
-- Knowledge Storage Tables
-- ============================================================

-- claims: All knowledge claims extracted from transcripts
CREATE TABLE IF NOT EXISTS knowledge.claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(50) NOT NULL,
    confidence NUMERIC(5,2),
    source_segment_id UUID,
    entity_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE knowledge.claims IS 'All knowledge claims extracted from transcripts with confidence scoring';

-- claim_sources: Evidence mapping from claims to transcript segments
CREATE TABLE IF NOT EXISTS knowledge.claim_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL,
    transcript_segment_id UUID NOT NULL,
    evidence_text TEXT,
    confidence NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_claim_source_claim
        FOREIGN KEY(claim_id) REFERENCES knowledge.claims(id)
);

COMMENT ON TABLE knowledge.claim_sources IS 'Evidence mapping from claims to transcript segments for traceability';

-- entities: Canonical entities (people, spirits, locations, etc.)
CREATE TABLE IF NOT EXISTS knowledge.entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(50) NOT NULL,
    aliases JSONB DEFAULT '[]',
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE knowledge.entities IS 'Canonical entities with deduplication by canonical_name and aliases';

-- assertions: Validated relationships between entities
CREATE TABLE IF NOT EXISTS knowledge.assertions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID NOT NULL,
    target_entity_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    confidence NUMERIC(5,2),
    evidence JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE knowledge.assertions IS 'Validated relationships between entities forming the knowledge graph';

-- ============================================================
-- Indexes for Performance
-- ============================================================

-- claims indexes
CREATE INDEX IF NOT EXISTS idx_claims_claim_type ON knowledge.claims(claim_type);
CREATE INDEX IF NOT EXISTS idx_claims_confidence ON knowledge.claims(confidence);
CREATE INDEX IF NOT EXISTS idx_claims_entity_id ON knowledge.claims(entity_id);
CREATE INDEX IF NOT EXISTS idx_claims_source_segment ON knowledge.claims(source_segment_id);

-- claim_sources indexes
CREATE INDEX IF NOT EXISTS idx_claim_sources_claim_id ON knowledge.claim_sources(claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_sources_segment_id ON knowledge.claim_sources(transcript_segment_id);

-- entities indexes
CREATE INDEX IF NOT EXISTS idx_entities_entity_type ON knowledge.entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_canonical_name ON knowledge.entities(canonical_name);

-- assertions indexes
CREATE INDEX IF NOT EXISTS idx_assertions_source ON knowledge.assertions(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_assertions_target ON knowledge.assertions(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_assertions_relationship ON knowledge.assertions(relationship_type);

-- ============================================================
-- Foreign Key Constraints for Cross-Schema References
-- ============================================================

-- Note: Cross-schema references will be validated at application level
-- per PRD Section 7.1 requirements
