"""Transcript extraction pipeline — subtitle-first, STT API fallback.

Updated for PRD v2.0:
- No WhisperX or local ASR models
- No GPU required
- No speaker diarization
- YouTube subtitles primary source
- Google Cloud STT API fallback
"""

import structlog
from dataclasses import dataclass, field
from typing import Optional

logger = structlog.get_logger(__name__)


@dataclass
class TranscriptionResult:
    """Result of a transcription job.
    
    v2: Removed speaker_count, storage_path.
    Added source_type, cost_usd.
    """
    segments: list[dict] = field(default_factory=list)  # [{start, end, content, confidence}]
    language: str = ""
    word_count: int = 0
    source_type: str = "youtube_subtitle"  # youtube_subtitle | google_stt | assemblyai
    avg_confidence: float = 0.0
    cost_usd: float = 0.0


class TranscriptPipeline:
    """Orchestrate transcript extraction from subtitles or STT API.
    
    Priority:
    1. YouTube subtitles (auto-generated or manual) — FREE
    2. Google Cloud Speech-to-Text — PAID
    3. AssemblyAI — PAID fallback
    """

    def __init__(self, subtitle_parser=None, stt_client=None):
        self.subtitle_parser = subtitle_parser
        self.stt_client = stt_client

    async def extract_from_subtitles(self, subtitle_text: str) -> Optional[TranscriptionResult]:
        """Extract transcript from parsed YouTube subtitle text.
        
        Subtitle text is already parsed by ingestion-service into VTT format.
        """
        if not subtitle_text or not self.subtitle_parser:
            return None

        segments = await self.subtitle_parser.parse(subtitle_text)
        if not segments:
            return None

        word_count = sum(len(s["content"].split()) for s in segments)
        avg_conf = sum(s.get("confidence", 0.95) for s in segments) / len(segments)

        logger.info("transcript_from_subtitles", segments=len(segments), words=word_count)
        return TranscriptionResult(
            segments=segments,
            language="id",
            word_count=word_count,
            source_type="youtube_subtitle",
            avg_confidence=avg_conf,
            cost_usd=0.0,
        )

    async def extract_from_stt(self, video_url: str) -> Optional[TranscriptionResult]:
        """Extract transcript using third-party STT API.
        
        Audio is streamed to the API — NOT stored locally.
        """
        if not video_url or not self.stt_client:
            return None

        result = await self.stt_client.transcribe(video_url)
        if result and result.segments:
            logger.info(
                "transcript_from_stt",
                source=result.source_type,
                segments=len(result.segments),
                cost=result.cost_usd,
            )
        return result

    async def extract(
        self,
        subtitle_text: Optional[str] = None,
        video_url: Optional[str] = None,
    ) -> TranscriptionResult:
        """Extract transcript — try subtitles first, fall back to STT API.
        
        Args:
            subtitle_text: Parsed YouTube subtitle text (if available)
            video_url: YouTube video URL for STT API fallback
            
        Returns:
            TranscriptionResult with segments
            
        Raises:
            ValueError: If neither subtitle nor video_url is available
        """
        # Priority 1: Use YouTube subtitles (free)
        if subtitle_text:
            result = await self.extract_from_subtitles(subtitle_text)
            if result:
                return result

        # Priority 2: Use third-party STT API (paid)
        if video_url:
            result = await self.extract_from_stt(video_url)
            if result:
                return result

        raise ValueError("No transcript could be extracted. No subtitles available and no video URL provided.")