#!/usr/bin/env python3
"""Database schema setup for enrichment and article services.

Creates required tables in ai and knowledge schemas based on PRD v2.0.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add shared package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "src"))

from ai_shared.database import Database
from ai_shared.config import ServiceConfig


async def create_ai_schema_tables(db: Database):
    """Create tables in ai schema for enrichment and article services."""
    
    print("=" * 70)
    print("🔧 CREATING AI SCHEMA TABLES")
    print("=" * 70)
    print()
    
    # Create ai schema if not exists
    await db.execute("CREATE SCHEMA IF NOT EXISTS ai;")
    print("✅ Created ai schema")
    print()
    
    # Create enrichment_runs table
    await db.execute("""
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
    """)
    print("✅ Created ai.enrichment_runs table")
    
    # Create prompt_versions table
    await db.execute("""
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
    """)
    print("✅ Created ai.prompt_versions table")
    
    # Create article_drafts table
    await db.execute("""
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
    """)
    print("✅ Created ai.article_drafts table")
    
    # Create article_draft_versions table
    await db.execute("""
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
    """)
    print("✅ Created ai.article_draft_versions table")
    
    # Create cost_tracking table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS ai.cost_tracking (
            video_id UUID PRIMARY KEY,
            extraction_cost_usd NUMERIC(10,6) DEFAULT 0,
            enrichment_cost_usd NUMERIC(10,6) DEFAULT 0,
            embedding_cost_usd NUMERIC(10,6) DEFAULT 0,
            article_cost_usd NUMERIC(10,6) DEFAULT 0,
            total_cost_usd NUMERIC(10,6) DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    print("✅ Created ai.cost_tracking table")
    
    print()
    print("✅ All AI schema tables created successfully")


async def create_knowledge_schema_tables(db: Database):
    """Create tables in knowledge schema for enrichment service."""
    
    print("=" * 70)
    print("🔧 CREATING KNOWLEDGE SCHEMA TABLES")
    print("=" * 70)
    print()
    
    # Create knowledge schema if not exists
    await db.execute("CREATE SCHEMA IF NOT EXISTS knowledge;")
    print("✅ Created knowledge schema")
    print()
    
    # Create claims table
    await db.execute("""
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
    """)
    print("✅ Created knowledge.claims table")
    
    # Create claim_sources table
    await db.execute("""
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
    """)
    print("✅ Created knowledge.claim_sources table")
    
    # Create entities table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS knowledge.entities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            canonical_name VARCHAR(255) NOT NULL UNIQUE,
            entity_type VARCHAR(50) NOT NULL,
            aliases JSONB DEFAULT '[]',
            description TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    print("✅ Created knowledge.entities table")
    
    # Create assertions table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS knowledge.assertions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_entity_id UUID NOT NULL,
            target_entity_id UUID NOT NULL,
            relationship_type VARCHAR(50) NOT NULL,
            confidence NUMERIC(5,2),
            evidence JSONB DEFAULT '[]',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    print("✅ Created knowledge.assertions table")
    
    print()
    print("✅ All knowledge schema tables created successfully")


async def insert_initial_prompt_versions(db: Database):
    """Insert initial prompt versions for enrichment extractors."""
    
    print("=" * 70)
    print("🔧 INSERTING INITIAL PROMPT VERSIONS")
    print("=" * 70)
    print()
    
    # Theme extraction prompt
    await db.execute("""
        INSERT INTO ai.prompt_versions 
        (prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, 
        "theme_extraction", "1.0.0", "theme_extraction",
        """You are analyzing a transcript from Indonesian mystery folklore content.

Your task is to extract themes present in the following transcript segment.

Themes are broad narrative categories such as:
- Fear, Loss, Afterlife, Curiosity, Forbidden Place
- Ancestral Spirits, Supernatural Revenge, Guardian Spirits
- Transformation, Warning, Investigation, Witness Testimony
- Cultural Identity, Colonial Legacy, Modern vs Traditional""",
        """TRANSCRIPT SEGMENT:
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

Extract between 1-4 themes. Be conservative — only extract themes with clear evidence.""",
        True,
        "Initial theme extraction prompt based on PRD v2.0"
    )
    print("✅ Inserted theme_extraction prompt v1.0.0")
    
    # Motif extraction prompt
    await db.execute("""
        INSERT INTO ai.prompt_versions 
        (prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, 
        "motif_extraction", "1.0.0", "motif_extraction",
        """Extract narrative motifs from this Indonesian folklore transcript segment.

Motifs are recurring narrative elements such as:
- Mysterious Voice, Shadow Figure, Abandoned House
- Sacred Tree, Possession, Missing Person
- Ritual Failure, Dream Vision, Guardian Animal
- Transformation, Invisibility, Time Loop""",
        """TRANSCRIPT SEGMENT:
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
}""",
        True,
        "Initial motif extraction prompt based on PRD v2.0"
    )
    print("✅ Inserted motif_extraction prompt v1.0.0")
    
    # Entity extraction prompt
    await db.execute("""
        INSERT INTO ai.prompt_versions 
        (prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, 
        "entity_extraction", "1.0.0", "entity_extraction",
        """Extract supernatural entities and named entities from this Indonesian folklore transcript.

Entities include:
- People: witnesses, narrators, community members, cultural authorities
- Spirits: kuntilanak, pocong, genderuwo, sundel bolong
- Creatures: tuyul, leak, other mythological beings
- Locations: villages, forests, rivers, mountains, sacred places
- Objects: ritual items, cursed objects, cultural artifacts""",
        """TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "entities": [
    {
      "name": "string (entity name)",
      "type": "string (person|spirit|creature|location|object|organization)",
      "description": "string",
      "role_in_story": "string",
      "confidence": float (0.0-1.0)
    }
  ]
}""",
        True,
        "Initial entity extraction prompt based on PRD v2.0"
    )
    print("✅ Inserted entity_extraction prompt v1.0.0")
    
    # Claim extraction prompt
    await db.execute("""
        INSERT INTO ai.prompt_versions 
        (prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """, 
        "claim_extraction", "1.0.0", "claim_extraction",
        """Extract claims, assertions, and statements from this Indonesian folklore transcript.

Distinguish between:
- Direct observations (what someone saw/heard)
- Testimony (what someone said they experienced)
- Cultural beliefs (what is believed but not directly observed)
- Interpretations (explanations or theories)
- Hearsay (secondhand information)""",
        """TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "claims": [
    {
      "claim": "string (the statement)",
      "claimant": "string (who made the claim)",
      "type": "string (observation|testimony|belief|interpretation|hearsay)",
      "confidence": float (0.0-1.0),
      "evidence": "string (supporting quote from transcript)",
      "status": "string (verified|unverified|contradicted|cultural_belief)"
    }
  ]
}""",
        True,
        "Initial claim extraction prompt based on PRD v2.0"
    )
    print("✅ Inserted claim_extraction prompt v1.0.0")
    
    print()
    print("✅ All initial prompt versions inserted successfully")


async def main():
    """Main function to set up database schemas."""
    
    # Initialize database connection with ServiceConfig
    config = ServiceConfig(
        service_name="database_setup",
        pg_host=os.getenv("LA_PG_HOST", "localhost"),
        pg_port=int(os.getenv("LA_PG_PORT", "5432")),
        pg_database=os.getenv("LA_PG_DATABASE", "living_atlas"),
        pg_user=os.getenv("LA_PG_USER", "living_atlas"),
        pg_password=os.getenv("LA_PG_PASSWORD", "living_atlas"),
    )
    
    db = Database(config)
    
    try:
        await db.connect()
        print("✅ Connected to database")
        print()
        
        # Create AI schema tables
        await create_ai_schema_tables(db)
        print()
        
        # Create Knowledge schema tables
        await create_knowledge_schema_tables(db)
        print()
        
        # Insert initial prompt versions
        await insert_initial_prompt_versions(db)
        print()
        
        print("=" * 70)
        print("✅ DATABASE SETUP COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Summary:")
        print("  ✅ AI schema created with 5 tables")
        print("  ✅ Knowledge schema created with 4 tables")
        print("  ✅ 4 prompt versions inserted")
        print()
        print("Next steps:")
        print("  1. Configure external API keys in .env")
        print("  2. Set up Redpanda topics")
        print("  3. Configure Redis")
        print("  4. Test database connectivity from services")
        
    except Exception as e:
        print(f"❌ Error during database setup: {e}")
        raise
    finally:
        await db.close()
        print("✅ Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())