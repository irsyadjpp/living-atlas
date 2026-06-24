"""OpenAI Whisper Client for Cloud Transcription (Tier 3).

Handles audio transcription using OpenAI's Whisper API for videos
without subtitles. Extracts audio temporarily, transcribes, then deletes.
"""

import os
import tempfile
import structlog
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = structlog.get_logger(__name__)


@dataclass
class TranscriptionResult:
    """Result from audio transcription."""
    text: str
    language: str
    duration_seconds: float
    cost_usd: float
    provider: str = "openai_whisper"
    model: str = "whisper-1"


class OpenAIWhisperClient:
    """Client for OpenAI Whisper audio transcription.
    
    Pricing (as of 2025):
    - whisper-1: $0.006 per minute
    - whisper-large-v3-turbo: $0.006 per minute
    
    Use Cases:
    - Tier 3 of 4-tier ingestion strategy
    - Videos without subtitles (20% of YouTube videos)
    - Videos with poor subtitle quality (30% of YouTube videos)
    
    Workflow:
    1. Extract audio to temporary file
    2. Upload to OpenAI Whisper API
    3. Get transcription
    4. Delete temporary audio file
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: str = "id",  # Indonesian by default
    ):
        """
        Initialize OpenAI Whisper client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Whisper model to use (whisper-1, whisper-large-v3-turbo)
            language: Language code for transcription (id for Indonesian)
        """
        if AsyncOpenAI is None:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model = model
        self.language = language
        
        # Cost per minute for each model
        self.cost_per_minute = {
            "whisper-1": 0.006,
            "whisper-large-v3-turbo": 0.006,
        }.get(model, 0.006)
        
        # Initialize async client
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(
            "openai_whisper_client_initialized",
            model=model,
            language=language,
        )

    async def transcribe_file(self, audio_path: str) -> TranscriptionResult:
        """
        Transcribe audio file using OpenAI Whisper.
        
        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            
        Returns:
            TranscriptionResult with text, language, duration, and cost
            
        Raises:
            Exception: If transcription fails
        """
        import time
        
        logger.info(
            "transcription_started",
            audio_path=audio_path,
            model=self.model,
        )
        
        start_time = time.time()
        
        try:
            # Get file size and estimate duration
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            
            # Transcribe using OpenAI API
            with open(audio_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=self.language,
                    response_format="text",
                    timestamp_granularities=["segment"] if self.model == "whisper-1" else None,
                )
            
            elapsed_time = time.time() - start_time
            
            # Estimate duration from file size (rough approximation)
            # For typical audio: 1 minute ≈ 1 MB for 128 kbps
            estimated_duration_minutes = file_size_mb  # Rough approximation
            duration_seconds = estimated_duration_minutes * 60
            
            # Calculate cost
            cost_usd = estimated_duration_minutes * self.cost_per_minute
            
            logger.info(
                "transcription_completed",
                audio_path=audio_path,
                text_length=len(transcript),
                estimated_duration_minutes=estimated_duration_minutes,
                cost_usd=cost_usd,
                elapsed_seconds=elapsed_time,
            )
            
            return TranscriptionResult(
                text=transcript,
                language=self.language,
                duration_seconds=duration_seconds,
                cost_usd=cost_usd,
                provider="openai_whisper",
                model=self.model,
            )
            
        except Exception as e:
            logger.error(
                "transcription_failed",
                audio_path=audio_path,
                error=str(e),
                exc_info=True,
            )
            raise

    async def transcribe_from_url(
        self,
        video_url: str,
        audio_extractor,
    ) -> TranscriptionResult:
        """
        Extract audio from video URL, transcribe, then delete audio.
        
        Args:
            video_url: YouTube or other video URL
            audio_extractor: Function to extract audio from video URL
            
        Returns:
            TranscriptionResult with transcription details
            
        Raises:
            Exception: If audio extraction or transcription fails
        """
        temp_audio_path = None
        
        try:
            # Extract audio to temporary file
            logger.info("audio_extraction_started", video_url=video_url)
            temp_audio_path = await audio_extractor.extract_audio(video_url)
            
            if not temp_audio_path or not os.path.exists(temp_audio_path):
                raise ValueError("Audio extraction failed - no audio file created")
            
            # Transcribe the audio
            result = await self.transcribe_file(temp_audio_path)
            
            return result
            
        finally:
            # Cleanup: Delete temporary audio file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    logger.info(
                        "audio_cleanup_completed",
                        audio_path=temp_audio_path,
                    )
                except Exception as e:
                    logger.warning(
                        "audio_cleanup_failed",
                        audio_path=temp_audio_path,
                        error=str(e),
                    )

    async def transcribe_with_retry(
        self,
        audio_path: str,
        max_retries: int = 3,
    ) -> TranscriptionResult:
        """
        Transcribe with retry logic for transient failures.
        
        Args:
            audio_path: Path to audio file
            max_retries: Maximum number of retry attempts
            
        Returns:
            TranscriptionResult
            
        Raises:
            Exception: If all retries fail
        """
        import asyncio
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self.transcribe_file(audio_path)
            except Exception as e:
                last_error = e
                logger.warning(
                    "transcription_retry",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
        
        raise last_error or Exception("All transcription attempts failed")

    async def close(self):
        """Close the OpenAI client."""
        if self.client:
            await self.client.close()
            logger.info("openai_whisper_client_closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()