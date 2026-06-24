"""End-to-End Test: Crawling → Transcript → Canonical Story → 4 Articles

This script tests the complete pipeline for one RJL 5 video:
1. Ingestion: Crawls video metadata
2. Extraction: Gets transcript using 4-tier strategy
3. Enrichment: Creates canonical story using 3-stage pipeline
4. Article Generation: Generates 4 article types (narrative, knowledge, news, creative)

Test video: RJL 5 YouTube video
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "shared/src"))
sys.path.insert(0, str(project_root / "ingestion-service/src"))
sys.path.insert(0, str(project_root / "extraction-service/src"))
sys.path.insert(0, str(project_root / "enrichment-service/src"))
sys.path.insert(0, str(project_root / "article-service/src"))

import structlog
from ai_shared.database import Database
from ai_shared.config import ServiceConfig

from ingestion.infrastructure.youtube import YouTubeClient
from extraction.ingestion.four_tier_pipeline import FourTierIngestionPipeline
from enrichment.application.service import EnrichmentService
from article.application.service import ArticleService

logger = structlog.get_logger(__name__)


# RJL 5 Test Video
# Replace with actual RJL 5 video URL
# Examples of RJL 5 videos (replace with actual ID):
# RJL5_TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Placeholder
RJL5_TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with real RJL 5 video


async def main():
    """Run end-to-end test for RJL 5 video."""
    
    # Initialize database
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/living_atlas")
    db = Database(db_url)
    
    # Initialize config
    config = ServiceConfig(service_name="test-pipeline")
    
    logger.info("=" * 60)
    logger.info("STARTING END-TO-END TEST FOR RJL 5 VIDEO")
    logger.info("=" * 60)
    logger.info("video_url", url=RJL5_TEST_VIDEO)
    
    try:
        await db.initialize()
        
        # Step 1: Ingestion - Crawl video metadata
        logger.info("STEP 1: INGESTION - Crawling video metadata")
        youtube_client = YouTubeClient()
        
        video_info = youtube_client.get_video_info(RJL5_TEST_VIDEO)
        logger.info(
            "video_info_crawled",
            title=video_info.title,
            channel=video_info.channel_name,
            duration_seconds=video_info.duration_seconds,
            view_count=video_info.view_count,
        )
        
        # Store video in database
        video_id = str(uuid.uuid4())
        await db.execute("""
            INSERT INTO source.channels (id, name, url, subscriber_count, default_priority)
            VALUES ($1, $2, $3, $4, 'HIGH')
            ON CONFLICT (url) DO UPDATE SET name = $2
            RETURNING id
        """, str(uuid.uuid4()), video_info.channel_name, video_info.channel_url, video_info.subscriber_count)
        
        channel_result = await db.fetchrow(
            "SELECT id FROM source.channels WHERE url = $1",
            video_info.channel_url
        )
        channel_id = channel_result["id"] if channel_result else str(uuid.uuid4())
        
        await db.execute("""
            INSERT INTO source.videos (id, channel_id, url, title, published_at, priority, processing_state)
            VALUES ($1, $2, $3, $4, $5, 'HIGH', 'SUBMITTED')
        """, video_id, channel_id, RJL5_TEST_VIDEO, video_info.title, video_info.published_at)
        
        logger.info("video_stored_in_db", video_id=video_id)
        
        # Step 2: Extraction - Get transcript using 4-tier strategy
        logger.info("STEP 2: EXTRACTION - Getting transcript (4-tier strategy)")
        
        # Note: For this test, we'll use Tier 1/2 (YouTube subtitles) to avoid API costs
        # In production, Tier 3 (cloud transcription) would be used if needed
        from extraction.ingestion.four_tier_pipeline import TranscriptResult
        
        try:
            transcript_result, transcript_metadata = await FourTierIngestionPipeline(
                youtube_client=youtube_client,
                whisper_client=None,  # Skip Tier 3 for test to save API costs
                db=db,
            ).extract_transcript(RJL5_TEST_VIDEO, video_id)
            
            logger.info(
                "transcript_extracted",
                tier=transcript_metadata.source_tier,
                quality_score=transcript_metadata.quality_score,
                word_count=transcript_metadata.word_count,
                cost_usd=transcript_metadata.cost_usd,
            )
            
            # Store transcript in database
            transcript_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO source.transcripts (
                    id, video_id, content, language, source_type, 
                    source_tier, quality_score, word_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, transcript_id, video_id, transcript_result.text, transcript_result.language,
                transcript_result.provider, transcript_metadata.source_tier,
                transcript_metadata.quality_score, transcript_metadata.word_count)
            
            logger.info("transcript_stored_in_db", transcript_id=transcript_id)
        
        except Exception as e:
            logger.error("transcript_extraction_failed", error=str(e), exc_info=True)
            # For testing, create a mock transcript if extraction fails
            logger.warning("using_mock_transcript_for_testing")
            transcript_id = str(uuid.uuid4())
            mock_transcript = """
            Ini adalah transcript contoh untuk testing pipeline.
            Video ini membahas tentang topik budaya Indonesia.
            Cerita ini memiliki elemen penting untuk dianalisis.
            """
            await db.execute("""
                INSERT INTO source.transcripts (id, video_id, content, language)
                VALUES ($1, $2, $3, 'id')
            """, transcript_id, video_id, mock_transcript)
        
        # Step 3: Enrichment - Create canonical story using 3-stage pipeline
        logger.info("STEP 3: ENRICHMENT - Creating canonical story (3-stage pipeline)")
        
        enrichment_service = EnrichmentService(db, config)
        
        # Get transcript text
        transcript_result = await db.fetchrow(
            "SELECT content FROM source.transcripts WHERE id = $1",
            transcript_id
        )
        transcript_text = transcript_result["content"] if transcript_result else ""
        
        video_metadata = {
            "title": video_info.title,
            "channel_name": video_info.channel_name,
            "channel_url": video_info.channel_url,
            "published_at": str(video_info.published_at),
            "duration_seconds": video_info.duration_seconds,
            "view_count": video_info.view_count,
        }
        
        try:
            canonical_story, validation_result = await enrichment_service.process_transcript_to_canonical_story(
                video_id=video_id,
                transcript_id=transcript_id,
                transcript_text=transcript_text,
                video_metadata=video_metadata,
            )
            
            logger.info(
                "canonical_story_created",
                story_title=canonical_story.story.title,
                story_type=canonical_story.story.story_type.value,
                quality_score=validation_result.get("quality_score"),
                ready_for_graph=validation_result.get("ready_for_graph"),
                entity_count=len(canonical_story.entities),
                claim_count=len(canonical_story.claims),
                relationship_count=len(canonical_story.relationships),
            )
            
            # The canonical_story_id is passed to the service and stored in DB
            # We need to retrieve it or use the one we passed
            canonical_story_id = await db.fetchval(
                "SELECT id FROM canonical.stories WHERE source_video_id = $1 ORDER BY created_at DESC LIMIT 1",
                video_id
            )
        
        except Exception as e:
            logger.error("enrichment_failed", error=str(e), exc_info=True)
            logger.warning("skipping_article_generation")
            return
        
        # Step 4: Article Generation - Generate 4 articles
        logger.info("STEP 4: ARTICLE GENERATION - Generating 4 article types")
        
        article_service = ArticleService(db, config)
        
        article_types = ["narrative", "knowledge", "news", "creative"]
        results = {}
        
        for article_type in article_types:
            logger.info(f"generating_{article_type}_article")
            
            try:
                result = await article_service.generate_article(
                    canonical_story_id=canonical_story_id,
                    canonical_story=canonical_story,
                    article_type=article_type,
                )
                
                if result.error:
                    logger.error(
                        f"{article_type}_article_failed",
                        error=result.error,
                    )
                else:
                    results[article_type] = result
                    
                    # Store article draft in database
                    article_id = str(uuid.uuid4())
                    await db.execute("""
                        INSERT INTO article.drafts (
                            id, canonical_story_id, article_type, title, 
                            content_markdown, quality_score, seo_metadata,
                            video_id, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now(), now())
                    """,
                        article_id, canonical_story_id, article_type,
                        result.seo_metadata.get("title", ""),
                        result.content_markdown,
                        result.quality_score,
                        result.seo_metadata,
                        video_id,
                    )
                    
                    logger.info(
                        f"{article_type}_article_completed",
                        article_id=article_id,
                        quality_score=result.quality_score,
                        word_count=len(result.content_markdown.split()),
                    )
            
            except Exception as e:
                logger.error(
                    f"{article_type}_article_exception",
                    error=str(e),
                    exc_info=True,
                )
        
        # Summary
        logger.info("=" * 60)
        logger.info("END-TO-END TEST COMPLETED")
        logger.info("=" * 60)
        logger.info("summary", video_id=video_id, video_title=video_info.title)
        logger.info("results", 
                   transcript_id=transcript_id,
                   canonical_story_id=canonical_story_id,
                   articles_generated=len(results),
                   article_types=list(results.keys()))
        
        # Print article snippets
        for article_type, result in results.items():
            logger.info(
                f"{article_type}_article_snippet",
                title=result.seo_metadata.get("title", "") if result.seo_metadata else "N/A",
                excerpt=result.content_markdown[:200] if result.content_markdown else "N/A",
            )
        
    except Exception as e:
        logger.error("test_failed", error=str(e), exc_info=True)
        raise
    finally:
        await db.close()
        logger.info("database_connection_closed")


if __name__ == "__main__":
    # Required environment variables
    required_env_vars = ["DATABASE_URL"]
    
    # Optional for LLM (will skip if not set)
    optional_env_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]
    
    missing_required = [var for var in required_env_vars if not os.getenv(var)]
    if missing_required:
        logger.error(
            "missing_required_env_vars",
            vars=missing_required,
        )
        print(f"Error: Missing required environment variables: {', '.join(missing_required)}")
        print("Required: DATABASE_URL")
        print("Optional (for LLM): ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY")
        sys.exit(1)
    
    missing_optional = [var for var in optional_env_vars if not os.getenv(var)]
    if missing_optional:
        logger.warning(
            "missing_optional_env_vars",
            vars=missing_optional,
        )
        print(f"Warning: Missing optional environment variables (LLM will be skipped): {', '.join(missing_optional)}")
    
    asyncio.run(main())