"""Article generation pipeline with Story Canonicalization.

Pipeline:
    Transcript + Knowledge Objects
        ↓
    Story Canonicalization (single prompt → canonical record)
        ↓
    Narrative Article | Knowledge Article | News Article | Creative Article

All 4 article types derive from the SAME canonical story record,
ensuring consistency across all generated content.
"""

import json
import structlog
import time
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from jinja2 import Template

logger = structlog.get_logger(__name__)


# ============================================================
# Dataclasses
# ============================================================

@dataclass
class CanonicalStory:
    """Canonical story record — single source of truth for all articles.
    
    Produced by Story Canonicalization before any article generation.
    All 4 article types derive from this same record.
    """
    story_id: str = ""
    title: str = ""
    summary: str = ""
    canonical_story: dict = field(default_factory=dict)  # Cleaned, structured narrative
    entities: list = field(default_factory=list)
    themes: list = field(default_factory=list)
    motifs: list = field(default_factory=list)
    beliefs: list = field(default_factory=list)
    rituals: list = field(default_factory=list)
    claims: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)
    narrative_patterns: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    locations: list = field(default_factory=list)
    witnesses: list = field(default_factory=list)
    timeline: list = field(default_factory=list)  # Chronological events
    open_questions: list = field(default_factory=list)
    cultural_context: str = ""


@dataclass
class ArticleMetrics:
    confidence_score: float = 0.0
    quality_score: float = 0.0
    body_word_count: int = 0
    citation_count: int = 0
    has_seo_title: bool = False
    has_seo_description: bool = False
    has_excerpt: bool = False
    has_tags: bool = False
    hallucination_risk: float = 0.0


@dataclass
class GenerationUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    model_name: str = ""


# ============================================================
# Gemini Client
# ============================================================

class GeminiClient:
    """Gemini API client for article generation."""

    MODEL_COST = 0.075  # $0.075 per 1M input tokens

    def __init__(self, api_key: str = "", model: str = "gemini-1.5-flash"):
        import google.generativeai as genai
        self.api_key = api_key or ""
        genai.configure(api_key=self.api_key) 
        self.model = genai.GenerativeModel(model)
        self.model_name = model
        logger.info("gemini_initialized", model=model)

    async def generate(self, prompt: str, max_tokens: int = 8192, temperature: float = 0.3) -> tuple[str, GenerationUsage]:
        """Generate text content using Gemini."""
        import google.generativeai as genai
        start = time.time()

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            duration_ms = (time.time() - start) * 1000
            text = response.text

            input_tokens = len(prompt) // 4
            output_tokens = len(text) // 4
            cost = (input_tokens / 1_000_000) * self.MODEL_COST

            usage = GenerationUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=round(cost, 8),
                duration_ms=round(duration_ms, 2),
                model_name=self.model_name,
            )

            return text, usage

        except Exception as e:
            logger.error("generation_failed", error=str(e))
            raise

    async def generate_structured(self, prompt: str, response_schema: dict, max_tokens: int = 8192, temperature: float = 0.3) -> tuple[dict, GenerationUsage]:
        """Generate structured JSON content using Gemini."""
        import google.generativeai as genai
        start = time.time()

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            duration_ms = (time.time() - start) * 1000

            input_tokens = len(prompt) // 4
            output_tokens = len(str(response.text)) // 4
            cost = (input_tokens / 1_000_000) * self.MODEL_COST

            usage = GenerationUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=round(cost, 8),
                duration_ms=round(duration_ms, 2),
                model_name=self.model_name,
            )

            result = response.parsed if hasattr(response, 'parsed') and response.parsed else json.loads(response.text)
            return result, usage

        except Exception as e:
            logger.error("structured_generation_failed", error=str(e))
            raise


# ============================================================
# Step 1: Story Canonicalization
# ============================================================

STORY_CANONICALIZATION_PROMPT = Template("""
You are a senior editor for The Living Atlas of Indonesian Mystery Culture.

Your task is to analyze the provided transcript and extracted knowledge objects, then produce a CANONICAL STORY RECORD.

This canonical record will be the SINGLE SOURCE OF TRUTH for ALL subsequent article generations (narrative, knowledge, news, creative).

CRITICAL RULES:
- Do NOT invent facts.
- Do NOT add events not present in the source.
- Do NOT speculate.
- Preserve uncertainty when uncertainty exists.
- Distinguish: observation, testimony, interpretation, conclusion.
- Identify contradictions explicitly.
- Identify confidence levels for each claim.

INPUT:

TRANSCRIPT:
{{transcript}}

KNOWLEDGE OBJECTS:
{{knowledge_objects}}

Produce a comprehensive JSON object with ALL of the following fields.
Be thorough. This is the foundation for all articles.

{
  "story_id": "string (unique identifier)",
  "title": "string (descriptive title)",
  "summary": "string (2-3 sentence summary)",
  "canonical_story": {
    "background": "string (context and setup)",
    "chronological_narrative": "string (what happened, in order)",
    "key_moments": ["string (list of pivotal moments)"],
    "resolution_or_current_state": "string"
  },
  "entities": [
    {
      "name": "string",
      "type": "string (person|spirit|creature|location|object|organization)",
      "description": "string",
      "role_in_story": "string",
      "confidence": "float (0.0-1.0)"
    }
  ],
  "locations": [
    {
      "name": "string",
      "type": "string (village|forest|river|mountain|house|temple|etc)",
      "significance": "string",
      "cultural_context": "string"
    }
  ],
  "themes": ["string"],
  "motifs": ["string"],
  "narrative_patterns": ["string"],
  "beliefs": [
    {
      "belief": "string",
      "culture": "string",
      "evidence": "string"
    }
  ],
  "rituals": [
    {
      "name": "string",
      "purpose": "string",
      "description": "string"
    }
  ],
  "witnesses": [
    {
      "name": "string",
      "role": "string",
      "testimony_summary": "string"
    }
  ],
  "timeline": [
    {
      "event": "string",
      "timestamp_or_order": "string",
      "description": "string"
    }
  ],
  "claims": [
    {
      "claim": "string",
      "claimant": "string",
      "type": "string (observation|testimony|belief|interpretation|hearsay)",
      "confidence": "float (0.0-1.0)",
      "evidence": "string",
      "status": "string (verified|unverified|contradicted|cultural_belief)"
    }
  ],
  "contradictions": [
    {
      "description": "string",
      "sources": ["string"],
      "resolution": "string or null"
    }
  ],
  "open_questions": ["string"],
  "cultural_context": "string (broader cultural significance)",
  "evidence": [
    {
      "type": "string (direct_testimony|physical_evidence|cultural_reference|historical_record)",
      "description": "string",
      "reliability": "string (high|medium|low)"
    }
  ]
}
""")


async def canonicalize_story(
    gemini: GeminiClient,
    transcript: str,
    knowledge_objects: dict,
) -> tuple[CanonicalStory, GenerationUsage]:
    """Step 1: Produce canonical story record from transcript + knowledge.
    
    This single canonical record is the source of truth for ALL article types.
    """
    logger.info("story_canonicalization_started")

    prompt = STORY_CANONICALIZATION_PROMPT.render(
        transcript=transcript[:15000],  # Limit transcript length
        knowledge_objects=json.dumps(knowledge_objects, indent=2)[:5000],
    )

    response_schema = {
        "type": "object",
        "properties": {
            "story_id": {"type": "string"},
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "canonical_story": {
                "type": "object",
                "properties": {
                    "background": {"type": "string"},
                    "chronological_narrative": {"type": "string"},
                    "key_moments": {"type": "array", "items": {"type": "string"}},
                    "resolution_or_current_state": {"type": "string"},
                },
            },
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "description": {"type": "string"},
                        "role_in_story": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                },
            },
            "locations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "significance": {"type": "string"},
                        "cultural_context": {"type": "string"},
                    },
                },
            },
            "themes": {"type": "array", "items": {"type": "string"}},
            "motifs": {"type": "array", "items": {"type": "string"}},
            "narrative_patterns": {"type": "array", "items": {"type": "string"}},
            "beliefs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "belief": {"type": "string"},
                        "culture": {"type": "string"},
                        "evidence": {"type": "string"},
                    },
                },
            },
            "rituals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "purpose": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
            "witnesses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                        "testimony_summary": {"type": "string"},
                    },
                },
            },
            "timeline": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "event": {"type": "string"},
                        "timestamp_or_order": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "claimant": {"type": "string"},
                        "type": {"type": "string"},
                        "confidence": {"type": "number"},
                        "evidence": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
            },
            "contradictions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "sources": {"type": "array", "items": {"type": "string"}},
                        "resolution": {"type": "string"},
                    },
                },
            },
            "open_questions": {"type": "array", "items": {"type": "string"}},
            "cultural_context": {"type": "string"},
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "description": {"type": "string"},
                        "reliability": {"type": "string"},
                    },
                },
            },
        },
    }

    result, usage = await gemini.generate_structured(prompt, response_schema, max_tokens=16384, temperature=0.2)

    canonical = CanonicalStory(
        story_id=result.get("story_id", str(uuid4())),
        title=result.get("title", ""),
        summary=result.get("summary", ""),
        canonical_story=result.get("canonical_story", {}),
        entities=result.get("entities", []),
        themes=result.get("themes", []),
        motifs=result.get("motifs", []),
        beliefs=result.get("beliefs", []),
        rituals=result.get("rituals", []),
        claims=result.get("claims", []),
        contradictions=result.get("contradictions", []),
        narrative_patterns=result.get("narrative_patterns", []),
        evidence=result.get("evidence", []),
        locations=result.get("locations", []),
        witnesses=result.get("witnesses", []),
        timeline=result.get("timeline", []),
        open_questions=result.get("open_questions", []),
        cultural_context=result.get("cultural_context", ""),
    )

    logger.info("story_canonicalized", story_id=canonical.story_id, title=canonical.title[:50])
    return canonical, usage


# ============================================================
# Step 2a: Narrative Article Generator
# ============================================================

NARRATIVE_ARTICLE_PROMPT = Template("""
You are an investigative long-form editor for The Living Atlas of Indonesian Mystery Culture.

Your task is to transform the provided canonical story record into a high-quality NARRATIVE ARTICLE.

CRITICAL RULES:
- Do NOT invent facts.
- Do NOT add events that are not present in the source.
- Do NOT speculate.
- Do NOT create dialogue that does not exist.
- Preserve uncertainty when uncertainty exists.
- Distinguish observation, testimony, interpretation, and conclusion.

ARTICLE TYPE: Narrative Article

GOAL: Create a compelling, readable article that reconstructs the story as faithfully as possible while improving clarity and readability.

TARGET AUDIENCE: General readers interested in mystery culture, folklore, paranormal investigations, anthropology, and Indonesian storytelling.

STYLE:
- Documentary style
- Investigative journalism style
- Long-form storytelling
- Neutral and respectful tone
- Rich sensory descriptions only if supported by source evidence

OUTPUT STRUCTURE:
1. Headline
2. Short Summary
3. Background Context
4. Chronological Story Reconstruction
5. Key Moments
6. Witness Statements
7. Cultural Context
8. Observations and Findings
9. Open Questions
10. Sources and Provenance

CANONICAL STORY:
{{canonical_json}}

Generate Markdown.
""")


async def generate_narrative_article(
    gemini: GeminiClient,
    canonical: CanonicalStory,
) -> tuple[str, ArticleMetrics, GenerationUsage]:
    """Generate narrative article from canonical story.
    
    For general readers. Long-form investigative style.
    100% based on sources — no fiction.
    """
    prompt = NARRATIVE_ARTICLE_PROMPT.render(
        canonical_json=_canonical_to_prompt(canonical),
    )
    markdown, usage = await gemini.generate(prompt, max_tokens=16384, temperature=0.3)
    metrics = _calculate_metrics(markdown)
    logger.info("narrative_article_generated", quality=metrics.quality_score)
    return markdown, metrics, usage


# ============================================================
# Step 2b: Knowledge Article Generator
# ============================================================

KNOWLEDGE_ARTICLE_PROMPT = Template("""
You are a cultural knowledge editor for The Living Atlas of Indonesian Mystery Culture.

Your task is to convert the canonical story record into a structured KNOWLEDGE ARTICLE.

This article is NOT storytelling.
This article must focus on extracted knowledge.

CRITICAL RULES:
- Use only information supported by source material.
- Separate facts, claims, beliefs, and interpretations.
- Identify contradictions.
- Identify confidence levels.
- Preserve cultural nuance.
- Avoid sensationalism.

ARTICLE TYPE: Knowledge Article

TARGET AUDIENCE: Researchers, anthropologists, folklorists, creators, production houses.

OUTPUT STRUCTURE:

# Overview

# Story Metadata
- Source
- Creator
- Date
- Story Type
- Region
- Culture

# Entities
For each entity:
- Name
- Type
- Description
- Evidence
- Confidence

# Locations

# Themes

# Motifs

# Narrative Patterns

# Beliefs

# Rituals

# Traditions

# Folklore References

# Claims
For each claim:
- Claim
- Evidence
- Confidence

# Contradictions

# Related Stories

# Research Notes

# Knowledge Graph Summary

CANONICAL STORY:
{{canonical_json}}

Generate Markdown.
""")


async def generate_knowledge_article(
    gemini: GeminiClient,
    canonical: CanonicalStory,
) -> tuple[str, ArticleMetrics, GenerationUsage]:
    """Generate knowledge article from canonical story.
    
    For researchers and knowledge graph. Structured, factual, no storytelling.
    """
    prompt = KNOWLEDGE_ARTICLE_PROMPT.render(
        canonical_json=_canonical_to_prompt(canonical),
    )
    markdown, usage = await gemini.generate(prompt, max_tokens=16384, temperature=0.2)
    metrics = _calculate_metrics(markdown)
    logger.info("knowledge_article_generated", quality=metrics.quality_score)
    return markdown, metrics, usage


# ============================================================
# Step 2c: News Article Generator
# ============================================================

NEWS_ARTICLE_PROMPT = Template("""
You are a news editor for The Living Atlas of Indonesian Mystery Culture.

Create a factual NEWS-STYLE ARTICLE based on the canonical story record.

CRITICAL RULES:
- Do not exaggerate.
- Do not use clickbait.
- Do not claim supernatural events as proven facts.
- Attribute all statements to witnesses, creators, or sources.

ARTICLE TYPE: News Article

TARGET AUDIENCE: SEO, homepage visitors, Google Discover, social media sharing, trending stories.

STYLE:
- Professional journalism
- Concise
- Informative
- Neutral

OUTPUT STRUCTURE:
1. Headline
2. Lead Paragraph
3. Main Event Summary
4. Important Statements
5. Cultural Background
6. Why This Story Matters
7. Source Information

Target length: 800-1500 words.

CANONICAL STORY:
{{canonical_json}}

Generate Markdown.
""")


async def generate_news_article(
    gemini: GeminiClient,
    canonical: CanonicalStory,
) -> tuple[str, ArticleMetrics, GenerationUsage]:
    """Generate news article from canonical story.
    
    For SEO, homepage, social sharing. Concise and professional.
    """
    prompt = NEWS_ARTICLE_PROMPT.render(
        canonical_json=_canonical_to_prompt(canonical),
    )
    markdown, usage = await gemini.generate(prompt, max_tokens=8192, temperature=0.3)
    metrics = _calculate_metrics(markdown)
    logger.info("news_article_generated", quality=metrics.quality_score)
    return markdown, metrics, usage


# ============================================================
# Step 2d: Creative Article Generator
# ============================================================

CREATIVE_ARTICLE_PROMPT = Template("""
You are a fiction writer for The Living Atlas of Indonesian Mystery Culture.

Your task is to create an original fictional story INSPIRED by the provided canonical knowledge.

CRITICAL RULES:
- This is ENTERTAINMENT ONLY.
- This article is NOT considered factual.
- This article must NOT be treated as canonical knowledge.
- This article must NOT introduce new knowledge graph entities.
- Use the source only as inspiration.

GOAL:
Create a compelling mystery-horror story inspired by Indonesian folklore, beliefs, themes, motifs, and narrative patterns extracted from the source.

STYLE:
- Atmospheric
- Literary
- Immersive
- Emotional
- Modern Indonesian horror

OUTPUT STRUCTURE:
1. Title
2. Disclaimer: "This story is a fictional work inspired by cultural knowledge and folklore."
3. Story
4. Cultural Inspiration Notes

INPUT KNOWLEDGE:
{{canonical_json}}

Generate Markdown.
""")


async def generate_creative_article(
    gemini: GeminiClient,
    canonical: CanonicalStory,
) -> tuple[str, ArticleMetrics, GenerationUsage]:
    """Generate creative article from canonical story.
    
    Entertainment only. NOT canonical knowledge. Inspired by source.
    """
    prompt = CREATIVE_ARTICLE_PROMPT.render(
        canonical_json=_canonical_to_prompt(canonical),
    )
    markdown, usage = await gemini.generate(prompt, max_tokens=16384, temperature=0.8)
    metrics = _calculate_metrics(markdown)
    logger.info("creative_article_generated", quality=metrics.quality_score)
    return markdown, metrics, usage


# ============================================================
# Quality Score Calculator
# ============================================================

QUALITY_THRESHOLDS = {
    "min_quality_score": 0.5,
    "min_body_words": 150,
}


def _calculate_metrics(markdown: str) -> ArticleMetrics:
    """Calculate quality metrics for a generated article."""
    words = markdown.split()
    body_word_count = len(words)

    # English sentence detection
    english_sentences = len(re.findall(r'\b(the|is|are|was|were|has|have|been|will|would|could|should|may|might)\b', markdown, re.IGNORECASE))
    total_sentences = max(len(re.findall(r'[.!?]+', markdown)), 1)
    english_ratio = english_sentences / total_sentences

    # Citation count
    citations = len(re.findall(r'\[.*?\]', markdown))

    # Score components
    length_score = min(body_word_count / QUALITY_THRESHOLDS["min_body_words"], 1.0)
    language_score = max(0.0, 1.0 - english_ratio)
    citation_score = min(citations / 3.0, 1.0)

    quality_score = length_score * 0.40 + language_score * 0.30 + citation_score * 0.30
    hallucination_risk = max(0.0, 1.0 - (citation_score * 0.5 + length_score * 0.3 + language_score * 0.2))

    return ArticleMetrics(
        confidence_score=min(quality_score + 0.2, 1.0),
        quality_score=round(quality_score, 2),
        body_word_count=body_word_count,
        citation_count=citations,
        hallucination_risk=round(hallucination_risk, 2),
    )


def _canonical_to_prompt(canonical: CanonicalStory) -> str:
    """Serialize canonical story for prompt injection."""
    return json.dumps({
        "story_id": canonical.story_id,
        "title": canonical.title,
        "summary": canonical.summary,
        "canonical_story": canonical.canonical_story,
        "entities": canonical.entities,
        "themes": canonical.themes,
        "motifs": canonical.motifs,
        "beliefs": canonical.beliefs,
        "rituals": canonical.rituals,
        "claims": canonical.claims,
        "contradictions": canonical.contradictions,
        "narrative_patterns": canonical.narrative_patterns,
        "evidence": canonical.evidence,
        "locations": canonical.locations,
        "witnesses": canonical.witnesses,
        "timeline": canonical.timeline,
        "open_questions": canonical.open_questions,
        "cultural_context": canonical.cultural_context,
    }, indent=2)


# ============================================================
# Pipeline Orchestrator
# ============================================================

async def generate_all_articles(
    gemini: GeminiClient,
    transcript: str,
    knowledge_objects: dict,
    article_types: Optional[list[str]] = None,
) -> dict:
    """Full article generation pipeline.
    
    Pipeline:
        Transcript + Knowledge Objects
            ↓ Step 1
        Story Canonicalization (single canonical record)
            ↓ Step 2
        Narrative Article | Knowledge Article | News Article | Creative Article
    
    Args:
        gemini: Gemini client instance
        transcript: Full transcript text
        knowledge_objects: Extracted knowledge from enrichment-service
        article_types: Which articles to generate. Default: all 4.
    
    Returns:
        Dict with canonical story + all requested articles
    """
    if article_types is None:
        article_types = ["narrative", "knowledge", "news", "creative"]

    # ── Step 1: Story Canonicalization ──
    logger.info("pipeline_step_1_story_canonicalization")
    canonical, canonical_usage = await canonicalize_story(gemini, transcript, knowledge_objects)

    result = {
        "canonical": {
            "story_id": canonical.story_id,
            "title": canonical.title,
            "summary": canonical.summary,
        },
        "usage": {"canonicalization": canonical_usage},
        "articles": [],
    }

    total_cost = canonical_usage.cost_usd
    total_tokens = canonical_usage.input_tokens + canonical_usage.output_tokens

    # ── Step 2: Generate requested articles ──
    article_generators = {
        "narrative": ("Narrative Article", generate_narrative_article),
        "knowledge": ("Knowledge Article", generate_knowledge_article),
        "news": ("News Article", generate_news_article),
        "creative": ("Creative Article", generate_creative_article),
    }

    for art_type in article_types:
        if art_type not in article_generators:
            logger.warning("unknown_article_type", article_type=art_type)
            continue

        name, generator_func = article_generators[art_type]
        logger.info("pipeline_step_2_generating", article_type=art_type, name=name)

        try:
            markdown, metrics, usage = await generator_func(gemini, canonical)
            result["articles"].append({
                "type": art_type,
                "name": name,
                "markdown": markdown,
                "metrics": {
                    "quality_score": metrics.quality_score,
                    "confidence_score": metrics.confidence_score,
                    "word_count": metrics.body_word_count,
                    "citation_count": metrics.citation_count,
                    "hallucination_risk": metrics.hallucination_risk,
                },
                "usage": {
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cost_usd": usage.cost_usd,
                    "duration_ms": usage.duration_ms,
                },
            })
            total_cost += usage.cost_usd
            total_tokens += usage.input_tokens + usage.output_tokens
            logger.info("article_generated", type=art_type, quality=metrics.quality_score, cost=usage.cost_usd)

        except Exception as e:
            logger.error("article_generation_failed", type=art_type, error=str(e))
            result["articles"].append({
                "type": art_type,
                "name": name,
                "error": str(e),
            })

    result["total_cost_usd"] = round(total_cost, 6)
    result["total_tokens"] = total_tokens
    result["article_count"] = len(result["articles"])

    logger.info(
        "pipeline_completed",
        article_count=len(result["articles"]),
        total_cost=total_cost,
        total_tokens=total_tokens,
    )

    return result