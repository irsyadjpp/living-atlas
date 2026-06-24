"""Third-party Speech-to-Text API clients.

Google Cloud STT (primary) → AssemblyAI (secondary) → Deepgram (fallback).
No local ASR models. Audio is streamed — NOT stored.
"""

import os
import structlog
import asyncio
from dataclasses import dataclass
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from extraction.application.transcriber import TranscriptionResult

logger = structlog.get_logger(__name__)


class STTError(Exception):
    """Base exception for STT API errors."""
    pass


class STTRateLimitError(STTError):
    """Raised when STT API rate limit is exceeded."""
    pass


class STTQuotaExceededError(STTError):
    """Raised when STT API quota is exceeded."""
    pass


@dataclass
class STTConfig:
    """Configuration for STT API clients."""
    google_credentials_path: str = ""
    assemblyai_api_key: str = ""
    deepgram_api_key: str = ""
    language: str = "id-ID"
    max_retries: int = 3
    timeout_seconds: int = 300


class GoogleSTTClient:
    """Google Cloud Speech-to-Text API client.

    Primary STT provider. Best accuracy for Bahasa Indonesia.
    Audio is referenced via URL — NOT stored locally.
    """

    def __init__(self, config: STTConfig):
        self.config = config
        self.client = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Google STT client."""
        if self._initialized:
            return
        try:
            from google.cloud import speech
            if self.config.google_credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.config.google_credentials_path
            self.client = speech.SpeechAsyncClient()
            self._initialized = True
            logger.info("google_stt_initialized")
        except ImportError:
            logger.error("google_cloud_speech_not_installed")
            raise STTError("google-cloud-speech package not installed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((STTRateLimitError, ConnectionError)),
        reraise=True,
    )
    async def transcribe(self, audio_url: str, language: str = "id-ID") -> Optional[TranscriptionResult]:
        """Transcribe audio from a URL using Google Cloud STT.

        Args:
            audio_url: URL of the audio to transcribe (YouTube video URL)
            language: Language code (default: id-ID for Indonesian)

        Returns:
            TranscriptionResult with segments and metadata

        Raises:
            STTError: If transcription fails after all retries
        """
        self._ensure_initialized()
        logger.info("google_stt_transcribing", audio_url=audio_url, language=language)

        try:
            from google.cloud import speech_v1p1beta1 as speech

            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language,
                enable_automatic_punctuation=True,
                model="latest_long",
                use_enhanced=True,
            )

            # Use audio from URL
            audio = speech.RecognitionAudio(uri=audio_url)

            # Start long-running recognition
            operation = await self.client.long_running_recognize(config=config, audio=audio)

            # Wait for completion with timeout
            response = await operation.result(timeout=self.config.timeout_seconds)

            # Parse results into segments
            segments = []
            total_confidence = 0.0
            word_count = 0

            for result in response.results:
                if not result.alternatives:
                    continue

                best = result.alternatives[0]
                words = len(best.transcript.split())
                word_count += words

                # Get per-word timestamps if available
                if best.words:
                    for word_info in best.words:
                        segments.append({
                            "start": word_info.start_time.total_seconds()
                            if word_info.start_time else 0.0,
                            "end": word_info.end_time.total_seconds()
                            if word_info.end_time else 0.0,
                            "content": word_info.word,
                            "confidence": word_info.confidence,
                        })
                        total_confidence += word_info.confidence
                else:
                    # No word-level timestamps — use result-level
                    segments.append({
                        "start": 0.0,
                        "end": 0.0,
                        "content": best.transcript,
                        "confidence": result.alternatives[0].confidence,
                    })
                    total_confidence += result.alternatives[0].confidence

            avg_confidence = total_confidence / max(len(segments), 1)
            cost = self._estimate_cost(word_count)
            duration = sum(s["end"] - s["start"] for s in segments if s["end"] > s["start"])

            logger.info(
                "google_stt_completed",
                segments=len(segments),
                words=word_count,
                duration_seconds=duration,
                cost=cost,
            )

            return TranscriptionResult(
                segments=segments,
                language=language.replace("-ID", "").lower(),
                word_count=word_count,
                source_type="google_stt",
                avg_confidence=round(avg_confidence, 3),
                cost_usd=round(cost, 6),
            )

        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "quota" in error_str:
                logger.warning("google_stt_rate_limited", error=str(e))
                raise STTRateLimitError(f"Google STT rate limited: {e}")
            logger.error("google_stt_failed", error=str(e))
            raise STTError(f"Google STT transcription failed: {e}")

    @staticmethod
    def _estimate_cost(word_count: int) -> float:
        """Estimate cost based on word count.
        Google STT: $0.006 per 15 seconds of audio.
        Rough estimate: ~2 words/second → $0.006 per 30 words.
        """
        estimated_seconds = word_count / 2.0  # ~2 words/second
        cost_per_15s = 0.006
        cost = (estimated_seconds / 15.0) * cost_per_15s
        return cost


class AssemblyAIClient:
    """AssemblyAI API client.

    Secondary STT provider. Used if Google STT is unavailable or rate-limited.
    Audio is fetched by AssemblyAI servers — NOT stored locally.
    """

    def __init__(self, config: STTConfig):
        self.config = config
        self.client = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        try:
            import assemblyai as aai
            api_key = self.config.assemblyai_api_key or os.getenv("ASSEMBLYAI_API_KEY")
            if not api_key:
                raise STTError("ASSEMBLYAI_API_KEY not configured")
            aai.settings.api_key = api_key
            self._initialized = True
            logger.info("assemblyai_initialized")
        except ImportError:
            logger.error("assemblyai_not_installed")
            raise STTError("assemblyai package not installed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((STTRateLimitError, ConnectionError)),
        reraise=True,
    )
    async def transcribe(self, audio_url: str, language: str = "id") -> Optional[TranscriptionResult]:
        """Transcribe audio from a URL using AssemblyAI.

        Args:
            audio_url: URL of the audio to transcribe
            language: Language code (default: id for Indonesian)

        Returns:
            TranscriptionResult with segments and metadata
        """
        self._ensure_initialized()
        logger.info("assemblyai_transcribing", audio_url=audio_url, language=language)

        try:
            import assemblyai as aai

            # Configure transcriber
            config = aai.TranscriptionConfig(
                language_code=language,
                punctuate=True,
                speaker_labels=False,  # No diarization per PRD v2.0 A9
            )

            transcriber = aai.Transcriber()
            # Use audio URL directly — AssemblyAI fetches it
            transcript = await transcriber.transcribe_async(audio_url, config=config)

            if transcript.status == aai.TranscriptStatus.error:
                error_msg = transcript.error or "Unknown AssemblyAI error"
                logger.error("assemblyai_transcription_error", error=error_msg)
                raise STTError(f"AssemblyAI transcription failed: {error_msg}")

            # Parse segments
            segments = []
            for utterance in transcript.utterances:
                segments.append({
                    "start": utterance.start / 1000.0,  # ms to seconds
                    "end": utterance.end / 1000.0,
                    "content": utterance.text,
                    "confidence": utterance.confidence if hasattr(utterance, 'confidence') else 0.95,
                })

            # If no utterances, fall back to paragraphs
            if not segments and transcript.text:
                segments.append({
                    "start": 0.0,
                    "end": 0.0,
                    "content": transcript.text,
                    "confidence": transcript.confidence if hasattr(transcript, 'confidence') else 0.90,
                })

            word_count = len(transcript.text.split()) if transcript.text else 0
            cost = self._estimate_cost(word_count)

            logger.info(
                "assemblyai_completed",
                segments=len(segments),
                words=word_count,
                cost=cost,
            )

            return TranscriptionResult(
                segments=segments,
                language=language,
                word_count=word_count,
                source_type="assemblyai",
                avg_confidence=round(transcript.confidence if hasattr(transcript, 'confidence') else 0.90, 3),
                cost_usd=round(cost, 6),
            )

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str:
                raise STTRateLimitError(f"AssemblyAI rate limited: {e}")
            logger.error("assemblyai_failed", error=str(e))
            raise STTError(f"AssemblyAI transcription failed: {e}")

    @staticmethod
    def _estimate_cost(word_count: int) -> float:
        """AssemblyAI: $0.015 per minute of audio.
        Rough estimate: ~120 words/minute → $0.015 per 120 words.
        """
        minutes = word_count / 120.0
        return minutes * 0.015


class DeepgramClient:
    """Deepgram API client.

    Tertiary STT provider. Used as final fallback.
    """

    def __init__(self, config: STTConfig):
        self.config = config
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        api_key = self.config.deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise STTError("DEEPGRAM_API_KEY not configured")
        self.api_key = api_key
        self._initialized = True
        logger.info("deepgram_initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((STTRateLimitError, ConnectionError)),
        reraise=True,
    )
    async def transcribe(self, audio_url: str, language: str = "id") -> Optional[TranscriptionResult]:
        """Transcribe audio from a URL using Deepgram.

        Args:
            audio_url: URL of the audio to transcribe
            language: Language code (default: id for Indonesian)

        Returns:
            TranscriptionResult with segments and metadata
        """
        self._ensure_initialized()
        logger.info("deepgram_transcribing", audio_url=audio_url, language=language)

        try:
            import httpx
            url = "https://api.deepgram.com/v1/listen"
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            }
            params = {
                "language": language,
                "punctuate": "true",
                "model": "nova-2",
                "diarize": "false",  # No diarization per PRD v2.0
            }
            payload = {"url": audio_url}

            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(url, headers=headers, params=params, json=payload)
                response.raise_for_status()
                data = response.json()

            # Parse results
            channels = data.get("results", {}).get("channels", [])
            segments = []
            word_count = 0

            for channel in channels:
                alternatives = channel.get("alternatives", [])
                for alt in alternatives:
                    for word_info in alt.get("words", []):
                        segments.append({
                            "start": word_info.get("start", 0.0),
                            "end": word_info.get("end", 0.0),
                            "content": word_info.get("word", ""),
                            "confidence": word_info.get("confidence", 0.95),
                        })
                        word_count += 1

            if not segments:
                # Fall back to full transcript
                for alt in channels[0].get("alternatives", []):
                    if alt.get("transcript"):
                        segments.append({
                            "start": 0.0,
                            "end": 0.0,
                            "content": alt["transcript"],
                            "confidence": alt.get("confidence", 0.90),
                        })
                        word_count = len(alt["transcript"].split())

            avg_confidence = sum(s.get("confidence", 0.9) for s in segments) / max(len(segments), 1)
            cost = self._estimate_cost(word_count)

            logger.info("deepgram_completed", segments=len(segments), words=word_count, cost=cost)

            return TranscriptionResult(
                segments=segments,
                language=language,
                word_count=word_count,
                source_type="deepgram",
                avg_confidence=round(avg_confidence, 3),
                cost_usd=round(cost, 6),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise STTRateLimitError(f"Deepgram rate limited: {e}")
            raise STTError(f"Deepgram HTTP error: {e}")
        except Exception as e:
            logger.error("deepgram_failed", error=str(e))
            raise STTError(f"Deepgram transcription failed: {e}")

    @staticmethod
    def _estimate_cost(word_count: int) -> float:
        """Deepgram: $0.0059 per minute of audio (nova-2).
        Rough estimate: ~120 words/minute.
        """
        minutes = word_count / 120.0
        return minutes * 0.0059


class STTClientRouter:
    """Router that tries STT providers in order with fallback.

    Google Cloud STT → AssemblyAI → Deepgram
    """

    def __init__(self, config: Optional[STTConfig] = None):
        self.config = config or STTConfig()
        self.clients = []
        self._init_clients()

    def _init_clients(self):
        """Initialize STT clients in priority order."""
        try:
            self.clients.append(GoogleSTTClient(self.config))
            logger.info("stt_client_added", provider="google_stt")
        except Exception as e:
            logger.warning("stt_client_unavailable", provider="google_stt", error=str(e))

        try:
            self.clients.append(AssemblyAIClient(self.config))
            logger.info("stt_client_added", provider="assemblyai")
        except Exception as e:
            logger.warning("stt_client_unavailable", provider="assemblyai", error=str(e))

        try:
            self.clients.append(DeepgramClient(self.config))
            logger.info("stt_client_added", provider="deepgram")
        except Exception as e:
            logger.warning("stt_client_unavailable", provider="deepgram", error=str(e))

        if not self.clients:
            logger.warning("no_stt_clients_available", message="No STT API clients could be initialized")

    async def transcribe(self, audio_url: str) -> Optional[TranscriptionResult]:
        """Try each STT client in order until one succeeds.

        Args:
            audio_url: YouTube video URL to transcribe

        Returns:
            TranscriptionResult from the first successful provider
        """
        last_error = None
        for client in self.clients:
            try:
                result = await client.transcribe(audio_url)
                if result and result.segments:
                    logger.info(
                        "stt_transcription_succeeded",
                        provider=result.source_type,
                        segments=len(result.segments),
                        cost=result.cost_usd,
                    )
                    return result
            except STTRateLimitError as e:
                logger.warning("stt_rate_limited_try_next", provider=type(client).__name__, error=str(e))
                last_error = e
                continue
            except STTError as e:
                logger.warning("stt_failed_try_next", provider=type(client).__name__, error=str(e))
                last_error = e
                continue

        logger.error("all_stt_providers_failed", last_error=str(last_error))
        return None