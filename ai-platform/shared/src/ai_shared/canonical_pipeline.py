"""Story Canonicalization Orchestrator - Implementation.

The MOST IMPORTANT component in the entire system.
Transforms raw transcripts into structured canonical cultural knowledge using LLM.
"""

import structlog
from typing import Optional
from dataclasses import dataclass

from ai_shared.canonical import CanonicalStory
from ai_shared.prompts import (
    STORY_CANONICALIZATION_SYSTEM_PROMPT,
    STORY_CANONICALIZATION_USER_PROMPT,
)
from ai_shared.config import ServiceConfig
from ai_shared.database import Database

from enrichment.infrastructure.llm_client import LLMClientRouter, LLMUsage

logger = structlog.get_logger(__name__)


@dataclass
class CanonicalizationResult:
    """Result from story canonicalization."""
    canonical_story: CanonicalStory
    usage: Optional[LLMUsage] = None
    error: Optional[str] = None
    metadata: dict = None


class StoryCanonicalizationOrchestrator:
    """Transforms raw transcripts into structured canonical cultural knowledge.
    
    This is the core knowledge extraction component. All downstream systems
    (knowledge graph, article generation, research) depend on this output.
    
    Workflow:
    1. Receive raw transcript + metadata
    2. Use LLM to extract canonical knowledge
    3. Validate output against schema
    4. Return structured CanonicalStory
    """
    
    def __init__(self, llm_router: LLMClientRouter, config: ServiceConfig):
        self.llm_router = llm_router
        self.config = config
        self.system_prompt = STORY_CANONICALIZATION_SYSTEM_PROMPT
        self.user_prompt_template = STORY_CANONICALIZATION_USER_PROMPT
    
    async def canonicalize(
        self,
        transcript_text: str,
        video_metadata: dict,
        transcript_length: int = 0,
        max_tokens: int = 8192,
    ) -> CanonicalizationResult:
        """Transform transcript into canonical story.
        
        Args:
            transcript_text: Raw transcript text (may be messy)
            video_metadata: Metadata from YouTube (title, description, channel, etc.)
            transcript_length: Token count for LLM routing
            max_tokens: Maximum output tokens
            
        Returns:
            CanonicalizationResult with CanonicalStory and usage metrics
        """
        logger.info(
            "story_canonicalization_started",
            video_id=video_metadata.get("video_id"),
            transcript_length=transcript_length,
        )
        
        # Truncate transcript if too long (15K chars limit)
        max_transcript_length = 15000
        if len(transcript_text) > max_transcript_length:
            transcript_text = transcript_text[:max_transcript_length]
            logger.warning(
                "transcript_truncated",
                original_length=len(transcript_text),
                truncated_length=max_transcript_length,
            )
        
        # Prepare metadata JSON
        import json
        metadata_json = json.dumps(video_metadata, ensure_ascii=False, indent=2)
        
        # Construct full prompt
        user_prompt = self.user_prompt_template.render(
            transcript_text=transcript_text,
            metadata_json=metadata_json,
        )
        
        full_prompt = f"{self.system_prompt}\n\n{user_prompt}"
        
        try:
            # Get response schema from CanonicalStory
            response_schema = CanonicalStory.model_json_schema()
            
            # Call LLM
            result_dict, usage = await self.llm_router.extract_structured(
                prompt=full_prompt,
                response_schema=response_schema,
                transcript_length=transcript_length,
                max_tokens=max_tokens,
            )
            
            # Parse result into CanonicalStory
            canonical_story = CanonicalStory(**result_dict)
            
            # Add metadata
            canonical_story.source_video_id = video_metadata.get("video_id")
            canonical_story.source_transcript_id = video_metadata.get("transcript_id")
            canonical_story.extraction_date = video_metadata.get("timestamp")
            
            logger.info(
                "story_canonicalization_completed",
                video_id=video_metadata.get("video_id"),
                entity_count=len(canonical_story.entities),
                claim_count=len(canonical_story.claims),
                theme_count=len(canonical_story.themes),
                cost_usd=usage.cost_usd if usage else 0.0,
            )
            
            return CanonicalizationResult(
                canonical_story=canonical_story,
                usage=usage,
                metadata={
                    "input_length": len(transcript_text),
                    "truncated": len(transcript_text) > max_transcript_length,
                },
            )
            
        except Exception as e:
            logger.error(
                "story_canonicalization_failed",
                video_id=video_metadata.get("video_id"),
                error=str(e),
                exc_info=True,
            )
            return CanonicalizationResult(
                canonical_story=None,
                error=str(e),
            )


class KnowledgeNormalizer:
    """Normalizes canonical story by resolving duplicates and aliases.
    
    Stage 2 of the knowledge pipeline.
    """
    
    def __init__(self, llm_router: LLMClientRouter):
        self.llm_router = llm_router
    
    async def normalize(
        self,
        canonical_story: CanonicalStory,
    ) -> CanonicalizationResult:
        """Normalize canonical story to resolve duplicates.
        
        Args:
            canonical_story: Raw canonical story from Stage 1
            
        Returns:
            CanonicalizationResult with normalized CanonicalStory
        """
        logger.info(
            "knowledge_normalization_started",
            story=canonical_story.story.title,
            entity_count=len(canonical_story.entities),
        )
        
        # Convert to JSON
        import json
        canonical_story_json = json.dumps(canonical_story.model_dump(), ensure_ascii=False, indent=2)
        
        # Construct prompt
        from ai_shared.prompts import (
            KNOWLEDGE_NORMALIZATION_SYSTEM_PROMPT,
            KNOWLEDGE_NORMALIZATION_USER_PROMPT,
        )
        
        user_prompt = KNOWLEDGE_NORMALIZATION_USER_PROMPT.render(
            canonical_story_json=canonical_story_json,
        )
        
        full_prompt = f"{KNOWLEDGE_NORMALIZATION_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        try:
            response_schema = CanonicalStory.model_json_schema()
            
            result_dict, usage = await self.llm_router.extract_structured(
                prompt=full_prompt,
                response_schema=response_schema,
                transcript_length=len(canonical_story_json) // 4,
                max_tokens=8192,
            )
            
            normalized_story = CanonicalStory(**result_dict)
            
            logger.info(
                "knowledge_normalization_completed",
                story=normalized_story.story.title,
                entity_count=len(normalized_story.entities),
                cost_usd=usage.cost_usd if usage else 0.0,
            )
            
            return CanonicalizationResult(
                canonical_story=normalized_story,
                usage=usage,
            )
            
        except Exception as e:
            logger.error(
                "knowledge_normalization_failed",
                error=str(e),
                exc_info=True,
            )
            return CanonicalizationResult(
                canonical_story=canonical_story,  # Return original if normalization fails
                error=str(e),
            )


class KnowledgeValidator:
    """Validates normalized canonical story and assigns quality score.
    
    Stage 3 of the knowledge pipeline.
    """
    
    def __init__(self, llm_router: LLMClientRouter):
        self.llm_router = llm_router
    
    async def validate(
        self,
        canonical_story: CanonicalStory,
    ) -> dict:
        """Validate canonical story and return quality assessment.
        
        Args:
            canonical_story: Normalized canonical story from Stage 2
            
        Returns:
            Validation result with quality_score, issues, warnings, ready_for_graph
        """
        logger.info(
            "knowledge_validation_started",
            story=canonical_story.story.title,
        )
        
        # Convert to JSON
        import json
        normalized_story_json = json.dumps(canonical_story.model_dump(), ensure_ascii=False, indent=2)
        
        # Construct prompt
        from ai_shared.prompts import (
            KNOWLEDGE_VALIDATION_SYSTEM_PROMPT,
            KNOWLEDGE_VALIDATION_USER_PROMPT,
        )
        
        user_prompt = KNOWLEDGE_VALIDATION_USER_PROMPT.render(
            normalized_story_json=normalized_story_json,
        )
        
        full_prompt = f"{KNOWLEDGE_VALIDATION_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        try:
            # Validation result schema
            validation_schema = {
                "type": "object",
                "properties": {
                    "quality_score": {"type": "number"},
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "severity": {"type": "string"},
                                "category": {"type": "string"},
                                "description": {"type": "string"},
                                "location": {"type": "string"},
                            },
                        },
                    },
                    "warnings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                            },
                        },
                    },
                    "ready_for_graph": {"type": "boolean"},
                    "recommendation": {"type": "string"},
                },
            }
            
            result_dict, usage = await self.llm_router.extract_structured(
                prompt=full_prompt,
                response_schema=validation_schema,
                transcript_length=len(normalized_story_json) // 4,
                max_tokens=4096,
            )
            
            logger.info(
                "knowledge_validation_completed",
                story=canonical_story.story.title,
                quality_score=result_dict.get("quality_score"),
                ready_for_graph=result_dict.get("ready_for_graph"),
                cost_usd=usage.cost_usd if usage else 0.0,
            )
            
            return result_dict
            
        except Exception as e:
            logger.error(
                "knowledge_validation_failed",
                error=str(e),
                exc_info=True,
            )
            # Return default validation on failure
            return {
                "quality_score": 0.5,
                "issues": [{"severity": "error", "category": "validation_failed", "description": str(e), "location": "unknown"}],
                "warnings": [],
                "ready_for_graph": False,
                "recommendation": "review",
            }


class ThreeStageKnowledgePipeline:
    """Orchestrates the 3-stage knowledge pipeline.
    
    Pipeline:
    1. Story Canonicalization (transcript → canonical JSON)
    2. Knowledge Normalization (canonical JSON → normalized JSON)
    3. Knowledge Validation (normalized JSON → validated JSON + quality score)
    
    Output: Validated Canonical Story ready for:
    - Database storage
    - Knowledge graph construction (Neo4j)
    - Article generation (all 4 types)
    """
    
    def __init__(self, llm_router: LLMClientRouter):
        self.llm_router = llm_router
        self.canonicalizer = StoryCanonicalizationOrchestrator(llm_router, ServiceConfig())
        self.normalizer = KnowledgeNormalizer(llm_router)
        self.validator = KnowledgeValidator(llm_router)
    
    async def process(
        self,
        transcript_text: str,
        video_metadata: dict,
    ) -> tuple[CanonicalStory, dict]:
        """Run complete 3-stage pipeline.
        
        Args:
            transcript_text: Raw transcript text
            video_metadata: YouTube video metadata
            
        Returns:
            Tuple of (validated_canonical_story, validation_result)
        """
        logger.info(
            "three_stage_pipeline_started",
            video_id=video_metadata.get("video_id"),
        )
        
        # Stage 1: Story Canonicalization
        stage1_result = await self.canonicalizer.canonicalize(
            transcript_text=transcript_text,
            video_metadata=video_metadata,
        )
        
        if stage1_result.error or not stage1_result.canonical_story:
            raise Exception(f"Stage 1 failed: {stage1_result.error}")
        
        canonical_story = stage1_result.canonical_story
        
        # Stage 2: Knowledge Normalization
        stage2_result = await self.normalizer.normalize(canonical_story)
        
        if stage2_result.error or not stage2_result.canonical_story:
            logger.warning("stage2_failed_using_stage1_output", error=stage2_result.error)
            normalized_story = canonical_story  # Use Stage 1 output if Stage 2 fails
        else:
            normalized_story = stage2_result.canonical_story
        
        # Stage 3: Knowledge Validation
        validation_result = await self.validator.validate(normalized_story)
        
        # If validation passes, mark story as validated
        if validation_result.get("ready_for_graph"):
            normalized_story.extraction_version = "1.0.0-validated"
        
        logger.info(
            "three_stage_pipeline_completed",
            video_id=video_metadata.get("video_id"),
            quality_score=validation_result.get("quality_score"),
            ready_for_graph=validation_result.get("ready_for_graph"),
        )
        
        return normalized_story, validation_result