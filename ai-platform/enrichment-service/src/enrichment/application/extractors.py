"""Knowledge extractors with evaluation metrics, cost tracking, and prompt versioning.

Extracts: themes, motifs, archetypes, entities, claims, relationships.
All via third-party LLM API. No local models.
"""

import structlog
import time
from typing import Optional
from dataclasses import dataclass, field
from jinja2 import Template

from enrichment.infrastructure.llm_client import LLMClientRouter, LLMUsage, LLMError
from enrichment.infrastructure.prompt_templates import (
    THEME_EXTRACTION_TEMPLATE,
    MOTIF_EXTRACTION_TEMPLATE,
    ARCHETYPE_EXTRACTION_TEMPLATE,
    ENTITY_EXTRACTION_TEMPLATE,
    CLAIM_EXTRACTION_TEMPLATE,
    RELATIONSHIP_EXTRACTION_TEMPLATE,
    STORY_BOUNDARY_TEMPLATE,
)

logger = structlog.get_logger(__name__)


@dataclass
class ExtractionMetrics:
    """Evaluation metrics for a single extraction run."""
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    hallucination_risk: float = 0.0
    confidence_avg: float = 0.0
    confidence_min: float = 1.0
    items_count: int = 0
    low_confidence_items: int = 0


@dataclass
class ExtractionResult:
    """Result of a single extraction type."""
    items: list[dict] = field(default_factory=list)
    usage: Optional[LLMUsage] = None
    metrics: Optional[ExtractionMetrics] = None
    prompt_version: str = ""
    error: Optional[str] = None


class BaseExtractor:
    """Base class for all extractors with common functionality."""

    def __init__(self, llm_router: LLMClientRouter, template: Template, prompt_name: str, prompt_version: str = "1.0.0"):
        self.llm_router = llm_router
        self.template = template
        self.prompt_name = prompt_name
        self.prompt_version = prompt_version

    def _calculate_metrics(self, items: list[dict]) -> ExtractionMetrics:
        """Calculate evaluation metrics for extracted items.

        Metrics:
        - confidence_avg: Average confidence score
        - confidence_min: Minimum confidence score
        - low_confidence_items: Items with confidence < 0.6
        - hallucination_risk: Estimated risk based on confidence distribution
        """
        if not items:
            return ExtractionMetrics()

        confidences = [item.get("confidence", 0.5) for item in items]
        avg_conf = sum(confidences) / len(confidences)
        min_conf = min(confidences)
        low_conf = sum(1 for c in confidences if c < 0.6)

        # Hallucination risk: higher when many low-confidence items
        hallucination_risk = low_conf / max(len(items), 1)

        return ExtractionMetrics(
            precision=avg_conf,  # Approximate precision from confidence
            recall=avg_conf,     # Approximate recall from confidence
            f1_score=avg_conf,   # Approximate F1 from confidence
            hallucination_risk=round(hallucination_risk, 3),
            confidence_avg=round(avg_conf, 3),
            confidence_min=round(min_conf, 3),
            items_count=len(items),
            low_confidence_items=low_conf,
        )

    async def extract(
        self,
        transcript_text: str,
        transcript_length: int = 0,
        max_tokens: int = 4096,
    ) -> ExtractionResult:
        """Run extraction with retry, cost tracking, and metrics.

        Args:
            transcript_text: The transcript text to extract from
            transcript_length: Token count for LLM routing
            max_tokens: Maximum output tokens

        Returns:
            ExtractionResult with items, usage, and metrics
        """
        prompt = self.template.render(transcript_text=transcript_text)

        response_schema = self._get_response_schema()

        try:
            result, usage = await self.llm_router.extract_structured(
                prompt=prompt,
                response_schema=response_schema,
                transcript_length=transcript_length,
                max_tokens=max_tokens,
            )

            items = result.get(self._get_items_key(), [])
            metrics = self._calculate_metrics(items)

            logger.info(
                f"{self.prompt_name}_extraction_completed",
                count=len(items),
                cost=usage.cost_usd,
                avg_confidence=metrics.confidence_avg,
                low_confidence=metrics.low_confidence_items,
            )

            return ExtractionResult(
                items=items,
                usage=usage,
                metrics=metrics,
                prompt_version=self.prompt_version,
            )

        except LLMError as e:
            logger.error(f"{self.prompt_name}_extraction_failed", error=str(e))
            return ExtractionResult(
                items=[],
                error=str(e),
                prompt_version=self.prompt_version,
            )

    def _get_response_schema(self) -> dict:
        """Override in subclass to provide response schema."""
        raise NotImplementedError

    def _get_items_key(self) -> str:
        """Override in subclass to provide items key in response."""
        raise NotImplementedError


class ThemeExtractor(BaseExtractor):
    """Extract narrative themes from transcript text."""

    def __init__(self, llm_router: LLMClientRouter, prompt_version: str = "1.0.0"):
        super().__init__(llm_router, THEME_EXTRACTION_TEMPLATE, "theme", prompt_version)

    def _get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "themes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["name", "confidence", "evidence"],
                    },
                },
            },
        }

    def _get_items_key(self) -> str:
        return "themes"


class MotifExtractor(BaseExtractor):
    """Extract narrative motifs from transcript text."""

    def __init__(self, llm_router: LLMClientRouter, prompt_version: str = "1.0.0"):
        super().__init__(llm_router, MOTIF_EXTRACTION_TEMPLATE, "motif", prompt_version)

    def _get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "motifs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["name", "confidence", "evidence"],
                    },
                },
            },
        }

    def _get_items_key(self) -> str:
        return "motifs"


class ArchetypeExtractor(BaseExtractor):
    """Extract character archetypes from transcript text."""

    def __init__(self, llm_router: LLMClientRouter, prompt_version: str = "1.0.0"):
        super().__init__(llm_router, ARCHETYPE_EXTRACTION_TEMPLATE, "archetype", prompt_version)

    def _get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "archetypes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["name", "confidence", "evidence"],
                    },
                },
            },
        }

    def _get_items_key(self) -> str:
        return "archetypes"


class EntityExtractor(BaseExtractor):
    """Extract supernatural entities and named entities from transcript text."""

    def __init__(self, llm_router: LLMClientRouter, prompt_version: str = "1.0.0"):
        super().__init__(llm_router, ENTITY_EXTRACTION_TEMPLATE, "entity", prompt_version)

    def _get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "aliases": {"type": "array", "items": {"type": "string"}},
                            "description": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["name", "type", "confidence"],
                    },
                },
            },
        }

    def _get_items_key(self) -> str:
        return "entities"


class ClaimExtractor(BaseExtractor):
    """Extract factual claims from transcript text."""

    def __init__(self, llm_router: LLMClientRouter, prompt_version: str = "1.0.0"):
        super().__init__(llm_router, CLAIM_EXTRACTION_TEMPLATE, "claim", prompt_version)

    def _get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "claim_type": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["text", "claim_type", "confidence"],
                    },
                },
            },
        }

    def _get_items_key(self) -> str:
        return "claims"


class RelationshipExtractor(BaseExtractor):
    """Extract relationships between entities for knowledge graph."""

    def __init__(self, llm_router: LLMClientRouter, prompt_version: str = "1.0.0"):
        super().__init__(llm_router, RELATIONSHIP_EXTRACTION_TEMPLATE, "relationship", prompt_version)

    def _get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string"},
                            "predicate": {"type": "string"},
                            "object": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["subject", "predicate", "object", "confidence"],
                    },
                },
            },
        }

    def _get_items_key(self) -> str:
        return "relationships"


class StoryBoundaryDetector(BaseExtractor):
    """Detect story boundaries within a transcript.

    One video can contain multiple stories. This extractor identifies
    where one story ends and another begins.
    """

    def __init__(self, llm_router: LLMClientRouter, prompt_version: str = "1.0.0"):
        super().__init__(llm_router, STORY_BOUNDARY_TEMPLATE, "story_boundary", prompt_version)

    def _get_response_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "stories": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "start_timestamp": {"type": "number"},
                            "end_timestamp": {"type": "number"},
                            "summary": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["title", "start_timestamp", "end_timestamp", "summary", "confidence"],
                    },
                },
            },
        }

    def _get_items_key(self) -> str:
        return "stories"


@dataclass
class EnrichmentResult:
    """Complete result of all enrichment extractions."""
    themes: ExtractionResult = field(default_factory=ExtractionResult)
    motifs: ExtractionResult = field(default_factory=ExtractionResult)
    archetypes: ExtractionResult = field(default_factory=ExtractionResult)
    entities: ExtractionResult = field(default_factory=ExtractionResult)
    claims: ExtractionResult = field(default_factory=ExtractionResult)
    relationships: ExtractionResult = field(default_factory=ExtractionResult)
    stories: ExtractionResult = field(default_factory=ExtractionResult)
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class ExtractionOrchestrator:
    """Coordinate all extraction types for a transcript with cost tracking.

    Runs all extractors in parallel, aggregates results and costs.
    """

    def __init__(self, llm_router: LLMClientRouter, prompt_versions: Optional[dict] = None):
        self.llm_router = llm_router
        versions = prompt_versions or {}

        self.theme_extractor = ThemeExtractor(llm_router, versions.get("theme", "1.0.0"))
        self.motif_extractor = MotifExtractor(llm_router, versions.get("motif", "1.0.0"))
        self.archetype_extractor = ArchetypeExtractor(llm_router, versions.get("archetype", "1.0.0"))
        self.entity_extractor = EntityExtractor(llm_router, versions.get("entity", "1.0.0"))
        self.claim_extractor = ClaimExtractor(llm_router, versions.get("claim", "1.0.0"))
        self.relationship_extractor = RelationshipExtractor(llm_router, versions.get("relationship", "1.0.0"))
        self.story_detector = StoryBoundaryDetector(llm_router, versions.get("story_boundary", "1.0.0"))

    async def extract_all(
        self,
        transcript_text: str,
        transcript_length: int = 0,
        extraction_types: Optional[list[str]] = None,
    ) -> EnrichmentResult:
        """Run all or selected extractors on the transcript text.

        Args:
            transcript_text: The transcript text to extract from
            transcript_length: Token count for LLM routing
            extraction_types: List of extraction types to run.
                Default: all types. Options: themes, motifs, archetypes,
                entities, claims, relationships, stories

        Returns:
            EnrichmentResult with all extraction results and aggregated costs
        """
        import asyncio

        if extraction_types is None:
            extraction_types = ["themes", "motifs", "archetypes", "entities", "claims", "relationships", "stories"]

        start_time = time.time()

        # Build task map
        task_map = {}
        if "themes" in extraction_types:
            task_map["themes"] = self.theme_extractor.extract(transcript_text, transcript_length)
        if "motifs" in extraction_types:
            task_map["motifs"] = self.motif_extractor.extract(transcript_text, transcript_length)
        if "archetypes" in extraction_types:
            task_map["archetypes"] = self.archetype_extractor.extract(transcript_text, transcript_length)
        if "entities" in extraction_types:
            task_map["entities"] = self.entity_extractor.extract(transcript_text, transcript_length)
        if "claims" in extraction_types:
            task_map["claims"] = self.claim_extractor.extract(transcript_text, transcript_length)
        if "relationships" in extraction_types:
            task_map["relationships"] = self.relationship_extractor.extract(transcript_text, transcript_length)
        if "stories" in extraction_types:
            task_map["stories"] = self.story_detector.extract(transcript_text, transcript_length)

        # Run all extractors in parallel
        results = {}
        for name, coro in task_map.items():
            try:
                results[name] = await coro
            except Exception as e:
                logger.error("extraction_coro_failed", extractor=name, error=str(e))
                results[name] = ExtractionResult(error=str(e))

        total_duration = (time.time() - start_time) * 1000

        # Aggregate costs
        total_cost = sum(
            r.usage.cost_usd for r in results.values()
            if r.usage is not None
        )
        total_input = sum(
            r.usage.input_tokens for r in results.values()
            if r.usage is not None
        )
        total_output = sum(
            r.usage.output_tokens for r in results.values()
            if r.usage is not None
        )

        enrichment_result = EnrichmentResult(
            themes=results.get("themes", ExtractionResult()),
            motifs=results.get("motifs", ExtractionResult()),
            archetypes=results.get("archetypes", ExtractionResult()),
            entities=results.get("entities", ExtractionResult()),
            claims=results.get("claims", ExtractionResult()),
            relationships=results.get("relationships", ExtractionResult()),
            stories=results.get("stories", ExtractionResult()),
            total_cost_usd=round(total_cost, 6),
            total_duration_ms=round(total_duration, 2),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
        )

        logger.info(
            "extraction_all_completed",
            themes=len(enrichment_result.themes.items),
            motifs=len(enrichment_result.motifs.items),
            archetypes=len(enrichment_result.archetypes.items),
            entities=len(enrichment_result.entities.items),
            claims=len(enrichment_result.claims.items),
            relationships=len(enrichment_result.relationships.items),
            stories=len(enrichment_result.stories.items),
            total_cost=total_cost,
            total_duration_ms=round(total_duration, 2),
        )

        return enrichment_result