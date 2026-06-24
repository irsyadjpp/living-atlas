"""Cloud Transcription Providers for Tier 3 Ingestion.

Supports multiple transcription APIs with automatic fallback:
- OpenAI Whisper
- Gemini Speech (planned)
- Deepgram (planned)
- AssemblyAI (planned)
"""

from ai_shared.transcription.openai_whisper import OpenAIWhisperClient, TranscriptionResult

__all__ = [
    "OpenAIWhisperClient",
    "TranscriptionResult",
]