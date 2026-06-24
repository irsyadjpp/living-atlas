#!/usr/bin/env python3
"""Generate SQL migration scripts for enrichment and article services.

This script generates SQL files that can be executed when the database is available,
rather than requiring a live database connection during the script execution.
"""

from pathlib import Path


def generate_ai_schema_sql():
    """Generate SQL for AI schema tables."""
    
    sql_content = """
-- ============================================================
-- AI Platform - Enrichment & Article Services Schema
-- PRD v2.0 Compliance
-- ============================================================

-- Create ai schema if not exists
CREATE SCHEMA IF NOT EXISTS ai;

-- ============================================================
-- Enrichment Service Tables
-- ============================================================

-- enrichment_runs: Track enrichment pipeline execution per video
CREATE TABLE IF NOT EXISTS ai.enrichment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID,
    video_id UUID NOT NULL,
    transcript_id UUID,
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC(10,6),
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ai.enrichment_runs IS 'Track enrichment pipeline execution per video with LLM usage and costs';

-- prompt_versions: Versioned prompts for LLM extractors
CREATE TABLE IF NOT EXISTS ai.prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    few_shot_examples JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    notes TEXT,
    CONSTRAINT uq_prompt_name_version UNIQUE(prompt_name, version)
);

COMMENT ON TABLE ai.prompt_versions IS 'Versioned prompts for LLM extractors with A/B testing support';

-- ============================================================
-- Article Service Tables
-- ============================================================

-- article_drafts: Main table for generated article drafts
CREATE TABLE IF NOT EXISTS ai.article_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_type VARCHAR(50) NOT NULL 
        CHECK (article_type IN ('narrative', 'knowledge', 'news', 'creative')),
    title TEXT NOT NULL,
    slug VARCHAR(500) UNIQUE,
    content_markdown TEXT NOT NULL,
    seo_metadata JSONB NOT NULL DEFAULT '{}',
    source_story_ids UUID[] NOT NULL DEFAULT '{}',
    source_video_ids UUID[] NOT NULL DEFAULT '{}',
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    quality_score NUMERIC(5,2),
    quality_issues JSONB DEFAULT '[]',
    review_status VARCHAR(50) NOT NULL DEFAULT 'pending_review'
        CHECK (review_status IN ('pending_review', 'approved', 'rejected', 'needs_revision')),
    reviewer_id UUID,
    review_notes TEXT,
    published_content_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    version BIGINT NOT NULL DEFAULT 1
);

COMMENT ON TABLE ai.article_drafts IS 'Main table for generated article drafts pending curator review';

-- article_draft_versions: Version history for article drafts
CREATE TABLE IF NOT EXISTS ai.article_draft_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_draft_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    content_markdown TEXT NOT NULL,
    seo_metadata JSONB,
    quality_score NUMERIC(5,2),
    change_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    CONSTRAINT fk_draft_version
        FOREIGN KEY(article_draft_id) REFERENCES ai.article_drafts(id)
);

COMMENT ON TABLE ai.article_draft_versions IS 'Version history for article drafts with change tracking';

-- cost_tracking: Track total costs per video across all pipeline stages
CREATE TABLE IF NOT EXISTS ai.cost_tracking (
    video_id UUID PRIMARY KEY,
    extraction_cost_usd NUMERIC(10,6) DEFAULT 0,
    enrichment_cost_usd NUMERIC(10,6) DEFAULT 0,
    embedding_cost_usd NUMERIC(10,6) DEFAULT 0,
    article_cost_usd NUMERIC(10,6) DEFAULT 0,
    total_cost_usd NUMERIC(10,6) DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE ai.cost_tracking IS 'Track total third-party API costs per video across all pipeline stages';

-- ============================================================
-- Indexes for Performance
-- ============================================================

-- enrichment_runs indexes
CREATE INDEX IF NOT EXISTS idx_enrichment_runs_video_id ON ai.enrichment_runs(video_id);
CREATE INDEX IF NOT EXISTS idx_enrichment_runs_status ON ai.enrichment_runs(status);
CREATE INDEX IF NOT EXISTS idx_enrichment_runs_created_at ON ai.enrichment_runs(created_at);

-- prompt_versions indexes
CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON ai.prompt_versions(prompt_name);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON ai.prompt_versions(is_active) WHERE is_active = true;

-- article_drafts indexes
CREATE INDEX IF NOT EXISTS idx_article_drafts_review_status ON ai.article_drafts(review_status);
CREATE INDEX IF NOT EXISTS idx_article_drafts_article_type ON ai.article_drafts(article_type);
CREATE INDEX IF NOT EXISTS idx_article_drafts_quality_score ON ai.article_drafts(quality_score);
CREATE INDEX IF NOT EXISTS idx_article_drafts_created_at ON ai.article_drafts(created_at);

-- article_draft_versions indexes
CREATE INDEX IF NOT EXISTS idx_article_draft_versions_draft_id ON ai.article_draft_versions(article_draft_id);
"""
    
    return sql_content


def generate_knowledge_schema_sql():
    """Generate SQL for Knowledge schema tables."""
    
    sql_content = """
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
"""
    
    return sql_content


def generate_initial_prompts_sql():
    """Generate SQL for initial prompt versions."""
    
    sql_content = """
-- ============================================================
-- Initial Prompt Versions for Enrichment Service
-- PRD v2.0 Compliance
-- ============================================================

-- Theme Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'theme_extraction',
    '1.0.0',
    'theme_extraction',
    'You are analyzing a transcript from Indonesian mystery folklore content.

Your task is to extract themes present in the following transcript segment.

Themes are broad narrative categories such as:
- Fear, Loss, Afterlife, Curiosity, Forbidden Place
- Ancestral Spirits, Supernatural Revenge, Guardian Spirits
- Transformation, Warning, Investigation, Witness Testimony
- Cultural Identity, Colonial Legacy, Modern vs Traditional',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "themes": [
    {
      "name": "string (theme name)",
      "confidence": float (0.0-1.0),
      "evidence": "string (quote from transcript that supports this theme)"
    }
  ]
}

Extract between 1-4 themes. Be conservative — only extract themes with clear evidence.',
    true,
    'Initial theme extraction prompt based on PRD v2.0'
);

-- Motif Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'motif_extraction',
    '1.0.0',
    'motif_extraction',
    'Extract narrative motifs from this Indonesian folklore transcript segment.

Motifs are recurring narrative elements such as:
- Mysterious Voice, Shadow Figure, Abandoned House
- Sacred Tree, Possession, Missing Person
- Ritual Failure, Dream Vision, Guardian Animal
- Transformation, Invisibility, Time Loop',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "motifs": [
    {
      "name": "string (motif name)",
      "confidence": float (0.0-1.0),
      "evidence": "string (quote from transcript that supports this motif)"
    }
  ]
}',
    true,
    'Initial motif extraction prompt based on PRD v2.0'
);

-- Entity Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'entity_extraction',
    '1.0.0',
    'entity_extraction',
    'Extract supernatural entities and named entities from this Indonesian folklore transcript.

Entities include:
- People: witnesses, narrators, community members, cultural authorities
- Spirits: kuntilanak, pocong, genderuwo, sundel bolong
- Creatures: tuyul, leak, other mythological beings
- Locations: villages, forests, rivers, mountains, sacred places
- Objects: ritual items, cursed objects, cultural artifacts',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "entities": [
    {
      "name": "string (entity name)",
      "type": "string (person|spirit|creature|location|object|organization)",
      "description": "string",
      "role_in_story": "string",
      "confidence": float (0.0-1.0)"
    }
  ]
}',
    true,
    'Initial entity extraction prompt based on PRD v2.0'
);

-- Claim Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'claim_extraction',
    '1.0.0',
    'claim_extraction',
    'Extract claims, assertions, and statements from this Indonesian folklore transcript.

Distinguish between:
- Direct observations (what someone saw/heard)
- Testimony (what someone said they experienced)
- Cultural beliefs (what is believed but not directly observed)
- Interpretations (explanations or theories)
- Hearsay (secondhand information)',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "claims": [
    {
      "claim": "string (the statement)",
      "claimant": "string (who made the claim)",
      "type": "string (observation|testimony|belief|interpretation|hearsay)",
      "confidence": float (0.0-1.0)",
      "evidence": "string (supporting quote from transcript)",
      "status": "string (verified|unverified|contradicted|cultural_belief)"
    }
  ]
}',
    true,
    'Initial claim extraction prompt based on PRD v2.0'
);
"""
    
    return sql_content


def main():
    """Generate all SQL migration scripts."""
    
    print("=" * 70)
    print("🔧 GENERATING SQL MIGRATION SCRIPTS")
    print("=" * 70)
    print()
    
    # Create scripts directory
    scripts_dir = Path("/home/sdibonerate85/Developmet/living-atlas/ai-platform/scripts/migrations")
    scripts_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate AI schema SQL
    ai_schema_sql = generate_ai_schema_sql()
    ai_schema_file = scripts_dir / "001_create_ai_schema.sql"
    with open(ai_schema_file, 'w') as f:
        f.write(ai_schema_sql)
    print(f"✅ Generated: {ai_schema_file}")
    
    # Generate Knowledge schema SQL
    knowledge_schema_sql = generate_knowledge_schema_sql()
    knowledge_schema_file = scripts_dir / "002_create_knowledge_schema.sql"
    with open(knowledge_schema_file, 'w') as f:
        f.write(knowledge_schema_sql)
    print(f"✅ Generated: {knowledge_schema_file}")
    
    # Generate initial prompts SQL
    prompts_sql = generate_initial_prompts_sql()
    prompts_file = scripts_dir / "003_insert_initial_prompts.sql"
    with open(prompts_file, 'w') as f:
        f.write(prompts_sql)
    print(f"✅ Generated: {prompts_file}")
    
    print()
    print("=" * 70)
    print("✅ SQL MIGRATION SCRIPTS GENERATED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Generated files:")
    print(f"  📄 {ai_schema_file}")
    print(f"  📄 {knowledge_schema_file}")
    print(f"  📄 {prompts_file}")
    print()
    print("Next steps:")
    print("  1. Start PostgreSQL database")
    print("  2. Execute SQL files in order:")
    print("     - psql -U living_atlas -d living_atlas -f {ai_schema_file}")
    print("     - psql -U living_atlas -d living_atlas -f {knowledge_schema_file}")
    print("     - psql -U living_atlas -d living_atlas -f {prompts_file}")
    print("  3. Configure external API keys in .env file")
    print("  4. Set up Redpanda topics")
    print("  5. Configure Redis")


if __name__ == "__main__":
    main()