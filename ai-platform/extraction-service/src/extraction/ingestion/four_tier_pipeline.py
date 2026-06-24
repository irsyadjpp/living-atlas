"""4-Tier Ingestion Strategy Implementation.

Implements fallback strategy for transcript extraction:
Tier 1: Manual subtitles (YouTube manual, free, high quality)
Tier 2: Auto subtitles (YouTube auto, free, medium quality)
Tier 3: Cloud transcription (OpenAI/Gemini, paid, high quality)
Tier 4: Manual curation (important channels, manual effort)
"""

import uuid
import structlog
from typing import Optional, List
from dataclasses import dataclass

from extraction.infrastructure.youtube import YouTubeClient
from ai_shared.transcription import OpenAIWhisperClient, TranscriptionResult
from ai_shared.database import Database

logger = structlog.get_logger(__name__)


@dataclass
class TranscriptMetadata:
    """Metadata about extracted transcript."""
    source_tier: str  # TIER1_MANUAL, TIER2_AUTO, TIER3_CLOUD, TIER4_MANUAL
    source_type: str  # youtube_manual, youtube_auto, openai_whisper, manual_review
    quality_score: float  # 0.0 - 1.0
    language: str
    word_count: int
    duration_seconds: float
    cost_usd: float
    manual_review_required: bool = False


class Tier1ManualSubtitleStrategy:
    """Tier 1: Manual YouTube subtitles (free, high quality)."""

    def __init__(self, youtube_client: YouTubeClient):
        self.youtube_client = youtube_client

    async def extract_transcript(
        self,
        video_url: str,
    ) -> Optional[tuple[TranscriptResult, TranscriptMetadata]]:
        """Extract manual subtitles if available."""
        logger.info("tier1_manual_check_started", video_url=video_url)

        try:
            # Check for manual subtitles
            video_info = self.youtube_client.get_video_info(video_url)
            
            if video_info.has_subtitles:
                # Try to download manual subtitles
                subtitle_result = self.youtube_client.extract_subtitles(
                    video_url,
                    language="id",
                    sub_format="vtt",
                )

                if subtitle_result and not subtitle_result.is_auto_generated:
                    logger.info("tier1_manual_subtitles_found", video_url=video_url)

                    # Parse VTT to plain text
                    from extraction.infrastructure.subtitle_parser import SubtitleParser
                    parser = SubtitleParser()
                    segments = await parser.parse(subtitle_result.content)
                    transcript_text = " ".join(seg["content"] for seg in segments)

                    word_count = len(transcript_text.split())

                    return (
                        TranscriptResult(
                            text=transcript_text,
                            language="id",
                            duration_seconds=video_info.duration_seconds,
                            cost_usd=0.0,
                            provider="youtube_manual",
                            model="n/a",
                        ),
                        TranscriptMetadata(
                            source_tier="TIER1_MANUAL",
                            source_type="youtube_manual",
                            quality_score=0.95,  # Manual subtitles are high quality
                            language="id",
                            word_count=word_count,
                            duration_seconds=video_info.duration_seconds,
                            cost_usd=0.0,
                            manual_review_required=False,
                        ),
                    )

        except Exception as e:
            logger.warning(
                "tier1_manual_check_failed",
                video_url=video_url,
                error=str(e),
            )

        return None


class Tier2AutoSubtitleStrategy:
    """Tier 2: Auto-generated YouTube subtitles (free, medium quality)."""

    def __init__(self, youtube_client: YouTubeClient):
        self.youtube_client = youtube_client

    async def extract_transcript(
        self,
        video_url: str,
    ) -> Optional[tuple[TranscriptResult, TranscriptMetadata]]:
        """Extract auto-generated captions if available."""
        logger.info("tier2_auto_check_started", video_url=video_url)

        try:
            # Get video info
            video_info = self.youtube_client.get_video_info(video_url)

            # Try to download auto subtitles
            subtitle_result = self.youtube_client.extract_subtitles(
                video_url,
                language="id",
                sub_format="vtt",
            )

            if subtitle_result and subtitle_result.is_auto_generated:
                logger.info("tier2_auto_subtitles_found", video_url=video_url)

                # Parse VTT to plain text
                from extraction.infrastructure.subtitle_parser import SubtitleParser
                parser = SubtitleParser()
                segments = await parser.parse(subtitle_result.content)
                transcript_text = " ".join(seg["content"] for seg in segments)

                word_count = len(transcript_text.split())

                # Quality score for auto captions (lower than manual)
                quality_score = self._assess_auto_quality(transcript_text, segments)

                return (
                    TranscriptResult(
                        text=transcript_text,
                        language="id",
                        duration_seconds=video_info.duration_seconds,
                        cost_usd=0.0,
                        provider="youtube_auto",
                        model="n/a",
                    ),
                    TranscriptMetadata(
                        source_tier="TIER2_AUTO",
                        source_type="youtube_auto",
                        quality_score=quality_score,
                        language="id",
                        word_count=word_count,
                        duration_seconds=video_info.duration_seconds,
                        cost_usd=0.0,
                        manual_review_required=quality_score < 0.5,
                    ),
                )

        except Exception as e:
            logger.warning(
                "tier2_auto_check_failed",
                video_url=video_url,
                error=str(e),
            )

        return None

    def _assess_auto_quality(self, transcript_text: str, segments: List[dict]) -> float:
        """Assess quality of auto-generated subtitles."""
        quality_score = 0.75  # Base score for auto captions

        # Check for music labels (indicates poor auto captions)
        if "[music]" in transcript_text.lower() or "(music)" in transcript_text.lower():
            quality_score -= 0.15

        # Check for short segments (indicates poor segmentation)
        avg_segment_length = sum(len(seg["content"].split()) for seg in segments) / len(segments) if segments else 0
        if avg_segment_length < 3:
            quality_score -= 0.1

        # Check for repeated text (indicates caption errors)
        words = transcript_text.split()
        if len(set(words)) / len(words) < 0.5:
            quality_score -= 0.2

        return max(0.0, min(1.0, quality_score))


class Tier3CloudTranscriptionStrategy:
    """Tier 3: Cloud transcription API (paid, high quality)."""

    def __init__(
        self,
        whisper_client: OpenAIWhisperClient,
        youtube_client: YouTubeClient,
    ):
        self.whisper_client = whisper_client
        self.youtube_client = youtube_client

    async def extract_transcript(
        self,
        video_url: str,
    ) -> Optional[tuple[TranscriptResult, TranscriptMetadata]]:
        """Extract transcript using cloud transcription API."""
        logger.info("tier3_cloud_transcription_started", video_url=video_url)

        try:
            # Extract audio and transcribe
            transcript_result = await self.whisper_client.transcribe_from_url(
                video_url,
                self.youtube_client,
            )

            word_count = len(transcript_result.text.split())

            return (
                transcript_result,
                TranscriptMetadata(
                    source_tier="TIER3_CLOUD",
                    source_type="openai_whisper",
                    quality_score=0.90,  # Cloud transcription is high quality
                    language=transcript_result.language,
                    word_count=word_count,
                    duration_seconds=transcript_result.duration_seconds,
                    cost_usd=transcript_result.cost_usd,
                    manual_review_required=False,
                ),
            )

        except Exception as e:
            logger.error(
                "tier3_cloud_transcription_failed",
                video_url=video_url,
                error=str(e),
                exc_info=True,
            )
            return None


class Tier4ManualCurationStrategy:
    """Tier 4: Manual curation for important videos."""

    def __init__(self, db: Database):
        self.db = db
        self.important_channels = [
            "Jurnal Risa",
            "Nadia Omara",
            "Hirotada Radifan",
        ]

    async def check_manual_review_required(
        self,
        video_url: str,
    ) -> bool:
        """Check if video requires manual review."""
        try:
            video_info = await self._get_video_info(video_url)
            channel_name = video_info.get("channel_name", "")

            return channel_name in self.important_channels

        except Exception as e:
            logger.warning(
                "manual_review_check_failed",
                video_url=video_url,
                error=str(e),
            )
            return False

    async def flag_for_review(self, video_id: str):
        """Flag video for manual review in database."""
        await self.db.execute("""
            UPDATE source.videos
            SET manual_review_required = true,
                manual_review_status = 'pending',
                updated_at = now()
            WHERE id = $1
        """, video_id)

        logger.info("video_flagged_for_manual_review", video_id=video_id)

    async def _get_video_info(self, video_url: str) -> dict:
        """Get video info from database or YouTube."""
        # Try database first
        video = await self.db.fetchrow(
            "SELECT v.*, c.name as channel_name FROM source.videos v JOIN source.channels c ON v.channel_id = c.id WHERE v.url = $1",
            video_url,
        )

        if video:
            return {
                "channel_name": video["channel_name"],
                "video_id": video["id"],
            }

        # Fallback to YouTube client if needed
        # For now, return empty
        return {"channel_name": "", "video_id": None}


class FourTierIngestionPipeline:
    """Unified 4-tier ingestion pipeline with automatic fallback."""

    def __init__(
        self,
        youtube_client: YouTubeClient,
        whisper_client: Optional[OpenAIWhisperClient] = None,
        db: Optional[Database] = None,
    ):
        self.youtube_client = youtube_client
        self.whisper_client = whisper_client
        self.db = db

        # Initialize strategies
        self.tier1 = Tier1ManualSubtitleStrategy(youtube_client)
        self.tier2 = Tier2AutoSubtitleStrategy(youtube_client)
        self.tier4 = Tier4ManualCurationStrategy(db) if db else None

        # Tier 3 only if whisper client is available
        self.tier3 = Tier3CloudTranscriptionStrategy(
            whisper_client,
            youtube_client,
        ) if whisper_client else None

    async def extract_transcript(
        self,
        video_url: str,
        video_id: str,
    ) -> tuple[TranscriptResult, TranscriptMetadata]:
        """
        Extract transcript using 4-tier strategy with automatic fallback.

        Args:
            video_url: YouTube video URL
            video_id: Database video ID

        Returns:
            Tuple of (TranscriptResult, TranscriptMetadata)

        Raises:
            TranscriptExtractionError: If all tiers fail
        """
        logger.info("four_tier_ingestion_started", video_url=video_url, video_id=video_id)

        # Check Tier 4 first (manual review requirement)
        if self.tier4 and await self.tier4.check_manual_review_required(video_url):
            await self.tier4.flag_for_review(video_id)
            raise ManualReviewRequiredError(
                f"Video {video_id} flagged for manual review"
            )

        # Try Tier 1: Manual subtitles
        result = await self.tier1.extract_transcript(video_url)
        if result:
            logger.info("tier1_succeeded", video_url=video_url)
            return result

        # Try Tier 2: Auto subtitles
        result = await self.tier2.extract_transcript(video_url)
        if result:
            logger.info("tier2_succeeded", video_url=video_url)
            return result

        # Try Tier 3: Cloud transcription
        if self.tier3:
            result = await self.tier3.extract_transcript(video_url)
            if result:
                logger.info("tier3_succeeded", video_url=video_url)
                return result

        # All tiers failed
        logger.error("all_tiers_failed", video_url=video_url)
        raise TranscriptExtractionError(
            "No transcript available through any tier (manual, auto, cloud)"
        )


class TranscriptExtractionError(Exception):
    """Raised when transcript extraction fails through all tiers."""
    pass


class ManualReviewRequiredError(Exception):
    """Raised when video requires manual review (Tier 4)."""
    pass