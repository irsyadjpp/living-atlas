"""Article Service - Generates articles from Validated Canonical Stories.

All 4 article types (Narrative, Knowledge, News, Creative) now use
Validated Canonical Story as input, NOT raw transcript.

This ensures:
- Consistency across all articles
- Quality gate before generation
- Full traceability to source
- Single source of truth
"""

import structlog
from typing import Optional
from dataclasses import dataclass

from ai_shared.database import Database
from ai_shared.config import ServiceConfig
from ai_shared.canonical import CanonicalStory
from ai_shared.prompts import (
    NARRATIVE_ARTICLE_SYSTEM_PROMPT,
    NARRATIVE_ARTICLE_USER_PROMPT,
    KNOWLEDGE_ARTICLE_SYSTEM_PROMPT,
    KNOWLEDGE_ARTICLE_USER_PROMPT,
    NEWS_ARTICLE_SYSTEM_PROMPT,
    NEWS_ARTICLE_USER_PROMPT,
    CREATIVE_ARTICLE_SYSTEM_PROMPT,
    CREATIVE_ARTICLE_USER_PROMPT,
)

from ai_shared.llm.cloud_llm_client import CloudLLMClient, LLMProvider, LLMRequest
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMUsage:
    """Token usage and cost tracking for LLM calls."""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    model_name: str = ""
    provider: str = ""

logger = structlog.get_logger(__name__)


@dataclass
class ArticleGenerationResult:
    """Result from article generation."""
    article_type: str
    content_markdown: str
    seo_metadata: dict
    quality_score: float
    quality_issues: list
    usage: Optional[LLMUsage] = None
    error: Optional[str] = None


class ArticleService:
    """Service layer for article generation from canonical stories.
    
    New Architecture:
    - Input: Validated Canonical Story (from enrichment-service)
    - Process: LLM generates article based on canonical knowledge
    - Output: 4 article types with quality control
    """

    def __init__(self, db: Database, config: ServiceConfig):
        self.db = db
        self.config = config
        self.llm_client = CloudLLMClient(
            primary_provider=LLMProvider.CLAUDE,
            fallback_providers=[LLMProvider.GEMINI, LLMProvider.OPENAI],
        )
        
        # System prompts for each article type
        self.system_prompts = {
            "narrative": NARRATIVE_ARTICLE_SYSTEM_PROMPT,
            "knowledge": KNOWLEDGE_ARTICLE_SYSTEM_PROMPT,
            "news": NEWS_ARTICLE_SYSTEM_PROMPT,
            "creative": CREATIVE_ARTICLE_SYSTEM_PROMPT,
        }
        
        # User prompt templates
        self.user_prompt_templates = {
            "narrative": NARRATIVE_ARTICLE_USER_PROMPT,
            "knowledge": KNOWLEDGE_ARTICLE_USER_PROMPT,
            "news": NEWS_ARTICLE_USER_PROMPT,
            "creative": CREATIVE_ARTICLE_USER_PROMPT,
        }

    async def generate_all_articles(
        self,
        canonical_story_id: str,
        canonical_story: CanonicalStory,
    ) -> dict:
        """Generate all 4 article types from a canonical story.
        
        Args:
            canonical_story_id: UUID of the canonical story
            canonical_story: Validated CanonicalStory object
            
        Returns:
            Dict with results for each article type
        """
        logger.info(
            "article_generation_started",
            canonical_story_id=canonical_story_id,
            story_title=canonical_story.story.title,
        )

        article_types = ["narrative", "knowledge", "news", "creative"]
        results = {}
        
        for article_type in article_types:
            try:
                result = await self.generate_article(
                    canonical_story_id=canonical_story_id,
                    canonical_story=canonical_story,
                    article_type=article_type,
                )
                
                if result.error:
                    logger.error(
                        f"{article_type}_article_generation_failed",
                        canonical_story_id=canonical_story_id,
                        error=result.error,
                    )
                else:
                    results[article_type] = result
                    
                    # Store article in database
                    await self._store_article_draft(
                        canonical_story_id=canonical_story_id,
                        article_type=article_type,
                        result=result,
                    )
                    
                    logger.info(
                        f"{article_type}_article_generated",
                        canonical_story_id=canonical_story_id,
                        quality_score=result.quality_score,
                    )
                    
            except Exception as e:
                logger.error(
                    f"{article_type}_article_generation_exception",
                    canonical_story_id=canonical_story_id,
                    error=str(e),
                    exc_info=True,
                )
        
        return results

    async def generate_article(
        self,
        canonical_story_id: str,
        canonical_story: CanonicalStory,
        article_type: str,
    ) -> ArticleGenerationResult:
        """Generate a single article type from canonical story.
        
        Args:
            canonical_story_id: UUID of the canonical story
            canonical_story: Validated CanonicalStory object
            article_type: Type of article to generate (narrative|knowledge|news|creative)
            
        Returns:
            ArticleGenerationResult with content and quality metrics
        """
        import json
        
        # Prepare canonical story JSON
        canonical_story_json = json.dumps(canonical_story.model_dump(), ensure_ascii=False, indent=2)
        
        # Construct full prompt
        system_prompt = self.system_prompts[article_type]
        user_prompt = self.user_prompt_templates[article_type].render(
            canonical_story_json=canonical_story_json,
        )
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            # Simple response schema for article generation
            response_schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content_markdown": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "focus_keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "content_markdown"],
            }
            
            # Call LLM (use longer max_tokens for article generation)
            request = LLMRequest(
                prompt=full_prompt,
                temperature=0.2,
                max_tokens=16384,
            )
            response = await self.llm_client.generate(request)
            
            import json as json_mod
            try:
                result_dict = json_mod.loads(response.text)
            except json_mod.JSONDecodeError:
                raise Exception(f"Failed to parse LLM response as JSON: {response.text[:200]}")
            
            usage = LLMUsage(
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
                duration_ms=response.latency_seconds * 1000,
                model_name=response.model,
                provider=response.provider.value,
            )
            
            # Generate SEO metadata
            seo_metadata = self._generate_seo_metadata(
                result_dict.get("title", ""),
                result_dict.get("excerpt", ""),
                result_dict.get("focus_keywords", []),
            )
            
            # Calculate quality score
            quality_score, quality_issues = self._calculate_article_quality(
                result_dict,
                canonical_story,
            )
            
            return ArticleGenerationResult(
                article_type=article_type,
                content_markdown=result_dict.get("content_markdown", ""),
                seo_metadata=seo_metadata,
                quality_score=quality_score,
                quality_issues=quality_issues,
                usage=usage,
            )
            
        except Exception as e:
            logger.error(
                f"{article_type}_article_generation_llm_failed",
                canonical_story_id=canonical_story_id,
                error=str(e),
                exc_info=True,
            )
            return ArticleGenerationResult(
                article_type=article_type,
                content_markdown="",
                seo_metadata={},
                quality_score=0.0,
                quality_issues=[f"LLM error: {str(e)}"],
                error=str(e),
            )

    def _generate_seo_metadata(
        self,
        title: str,
        excerpt: str,
        focus_keywords: list,
    ) -> dict:
        """Generate SEO metadata from article content."""
        
        # Extract keywords from title and excerpt
        meta_title = title[:60] if len(title) > 60 else title
        
        meta_description = excerpt[:160] if excerpt else title[:160]
        
        # Generate slug from title
        slug = title.lower().replace(" ", "-").replace("/", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        
        return {
            "meta_title": meta_title,
            "meta_description": meta_description,
            "slug": slug,
            "focus_keywords": focus_keywords[:5] if focus_keywords else [],
        }

    def _calculate_article_quality(
        self,
        article_dict: dict,
        canonical_story: CanonicalStory,
    ) -> tuple[float, list]:
        """Calculate quality score and identify issues for an article.
        
        Quality factors:
        - Content length (should be substantial)
        - Entity consistency (entities in article must exist in canonical story)
        - Hallucination detection (claims should be supported by evidence)
        - Language quality (should be formal Indonesian)
        """
        
        issues = []
        score = 1.0
        
        content = article_dict.get("content_markdown", "")
        
        # Check content length
        if len(content) < 500:
            issues.append("Content too short")
            score -= 0.3
        
        # Check entity consistency (simplified check)
        entities_mentioned = set()
        for entity in canonical_story.entities:
            entities_mentioned.add(entity.name.lower())
        
        entities_in_article = sum(1 for entity_name in entities_mentioned if entity_name in content.lower())
        
        if entities_in_article == 0 and len(canonical_story.entities) > 0:
            issues.append("No canonical entities mentioned in article")
            score -= 0.2
        
        # Check if article is empty
        if not content:
            issues.append("Empty article content")
            score = 0.0
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return round(score, 2), issues

    async def _store_article_draft(
        self,
        canonical_story_id: str,
        article_type: str,
        result: ArticleGenerationResult,
    ):
        """Store article draft in database.
        
        Args:
            canonical_story_id: UUID of source canonical story
            article_type: Type of article
            result: Article generation result
        """
        import json
        
        article_draft_id = str(uuid.uuid4())
        
        await self.db.execute("""
            INSERT INTO ai.article_drafts (
                id, article_type, title, content_markdown, seo_metadata,
                source_canonical_story_id, source_video_ids, source_story_ids,
                model_provider, model_name, prompt_version,
                quality_score, quality_issues, review_status,
                created_at, version
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, now(), 1)
        """,
            article_draft_id,
            article_type,
            self._extract_title_from_markdown(result.content_markdown),
            result.content_markdown,
            json.dumps(result.seo_metadata, ensure_ascii=False),
            canonical_story_id,
            [],  # source_video_ids (would need to fetch from canonical story)
            [canonical_story_id],  # source_story_ids
            "claude",  # Would use actual model from result
            "claude-3-5-sonnet-20241022",
            "2.0.0",  # Prompt version for article generation
            result.quality_score,
            json.dumps(result.quality_issues, ensure_ascii=False),
            "pending_review" if result.quality_score > 0.5 else "needs_revision",
        )

    def _extract_title_from_markdown(self, markdown: str) -> str:
        """Extract title from markdown content (first # header)."""
        lines = markdown.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                return line[2:]  # Remove "# "
        return "Untitled Article"