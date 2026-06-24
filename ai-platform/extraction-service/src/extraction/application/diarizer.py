"""Speaker diarization — NOT USED in PRD v2.0.

Diarization is not performed. All transcripts come from YouTube subtitles
or third-party STT APIs without speaker labels.
"""

import structlog

logger = structlog.get_logger(__name__)


class SpeakerDiarizer:
    """Stub — speaker diarization not performed in this version.
    
    PRD v2.0 decision: Speaker diarization is skipped for Phase 1-2.
    Transcript without diarization is sufficient for knowledge extraction.
    """

    def __init__(self, *args, **kwargs):
        logger.warning("diarization_disabled", message="Speaker diarization not used. Transcripts without speaker labels.")

    def initialize(self) -> None:
        pass

    def diarize(self, audio_path: str) -> list[dict]:
        return []

    def assign_speakers_to_segments(self, transcript_segments: list[dict], speaker_segments: list[dict]) -> list[dict]:
        return transcript_segments