"""YouTube subtitle parser — converts VTT/SRT subtitle text to segment format.

No local ASR models, no GPU required.
Handles YouTube's various subtitle formats.
"""

import re
import structlog
from typing import Optional, List
from collections import defaultdict

logger = structlog.get_logger(__name__)


class TranscriptCleaner:
    """Advanced transcript cleaning for subtitle text.
    
    Removes:
    - Timestamps and formatting artifacts
    - HTML/XML tags and styling
    - Duplicate phrases and repetitive segments
    - Cue settings (align, position, line)
    - Music/Sound effect markers
    - Speaker labels and annotations
    - Multiple spaces and line breaks
    
    Produces clean, readable transcript text.
    """
    
    def __init__(self):
        self.duplicate_threshold = 0.8  # Threshold for detecting duplicates
    
    def clean_vtt_to_text(self, vtt_content: str, remove_duplicates: bool = True) -> str:
        """Convert VTT subtitle to clean text transcript.
        
        Args:
            vtt_content: Raw VTT subtitle content
            remove_duplicates: Whether to remove duplicate phrases
            
        Returns:
            Clean transcript text
        """
        # Remove VTT header
        lines = vtt_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip VTT header and empty lines
            if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                continue
            # Skip timestamp lines
            if '-->' in line:
                continue
            # Skip empty lines
            if not line:
                continue
            
            cleaned_lines.append(line)
        
        # Join and clean
        text = ' '.join(cleaned_lines)
        
        # Remove HTML/XML tags and artifacts
        text = self._remove_html_tags(text)
        text = self._remove_cue_settings(text)
        text = self._remove_sound_markers(text)
        text = self._remove_speaker_labels(text)
        text = self._normalize_whitespace(text)
        
        # Remove duplicate phrases
        if remove_duplicates:
            text = self._remove_duplicate_phrases(text)
        
        return text.strip()
    
    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML/XML tags and karaoke timing tags."""
        # Remove standard HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove karaoke timing tags like <00:00:01.234>
        text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', text)
        return text
    
    def _remove_cue_settings(self, text: str) -> str:
        """Remove VTT cue settings (align, position, line, etc)."""
        text = re.sub(r'align:\w+\s*', '', text)
        text = re.sub(r'position:\d+%?\s*', '', text)
        text = re.sub(r'line:\d+%?\s*', '', text)
        text = re.sub(r'size:\d+%?\s*', '', text)
        return text
    
    def _remove_sound_markers(self, text: str) -> str:
        """Remove music and sound effect markers."""
        text = re.sub(r'\[musik\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[music\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[suara\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[sound\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\♪', '', text)
        text = re.sub(r'\♫', '', text)
        return text
    
    def _remove_speaker_labels(self, text: str) -> str:
        """Remove speaker labels and annotations."""
        text = re.sub(r'>>\s*\w+\s*:', '', text)
        text = re.sub(r'SPEAKER\s*\d+:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\w+\s*:', '', text)  # Generic speaker: pattern
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks."""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def _remove_duplicate_phrases(self, text: str) -> str:
        """Remove duplicate consecutive phrases using advanced detection.
        
        This handles cases like:
        "Jadi malam ini adalah malam satu suro, Guys. Dan gua lagi ada di Jogja pengen"
        "Jadi malam ini adalah malam satu suro, Guys. Dan gua lagi ada di Jogja pengen"
        
        Where subtitles often repeat due to karaoke-style timing.
        """
        words = text.split()
        if len(words) < 5:
            return text
        
        cleaned_words = []
        window_size = 4  # Check 4-word sequences
        
        for i in range(len(words)):
            current_word = words[i]
            should_skip = False
            
            if i >= window_size:
                current_sequence = words[i-window_size:i]
                current_sequence_str = ' '.join(current_sequence)
                
                # Look back for similar sequences (but not too far back)
                lookback_range = min(15, i - window_size)
                for j in range(max(0, i - window_size - lookback_range), i - window_size):
                    if j + window_size <= len(words):
                        prev_sequence = words[j:j+window_size]
                        prev_sequence_str = ' '.join(prev_sequence)
                        
                        similarity = self._similarity(current_sequence_str, prev_sequence_str)
                        
                        # If very similar and close in position, it's likely a duplicate
                        if similarity > 0.9 and (i - window_size - j) < 8:
                            should_skip = True
                            break
            
            if not should_skip:
                cleaned_words.append(current_word)
        
        return ' '.join(cleaned_words)
    
    def _similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using simple overlap."""
        if not str1 or not str2:
            return 0.0
        
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class SubtitleParser:
    """Parse YouTube subtitle text into structured segment format.

    Handles VTT (WebVTT) and SRT subtitle formats.
    Includes advanced transcript cleaning capabilities.
    """

    def __init__(self):
        self.cleaner = TranscriptCleaner()

    async def parse(self, subtitle_text: str, source_format: Optional[str] = None) -> list[dict]:
        """Parse subtitle text into structured segments.

        Args:
            subtitle_text: Raw subtitle text (VTT or SRT format)
            source_format: Format hint ('vtt', 'srt', or None for auto-detect)

        Returns:
            List of dicts: [{start, end, content}]
        """
        if not subtitle_text or not subtitle_text.strip():
            return []

        # Auto-detect format
        if source_format is None:
            if subtitle_text.strip().startswith("WEBVTT"):
                source_format = "vtt"
            elif re.match(r'^\d+\n\d{2}:\d{2}:\d{2}', subtitle_text.strip()):
                source_format = "srt"
            else:
                # Try VTT first, then SRT
                source_format = "vtt"

        if source_format == "vtt":
            return self._parse_vtt(subtitle_text)
        elif source_format == "srt":
            return self._parse_srt(subtitle_text)
        else:
            logger.warning("unknown_subtitle_format", format=source_format)
            return []
    
    async def to_clean_transcript(self, subtitle_text: str, source_format: Optional[str] = None, 
                                 remove_duplicates: bool = True) -> str:
        """Convert subtitle text to clean transcript without timestamps and artifacts.
        
        Args:
            subtitle_text: Raw subtitle text (VTT or SRT format)
            source_format: Format hint ('vtt', 'srt', or None for auto-detect)
            remove_duplicates: Whether to remove duplicate phrases
            
        Returns:
            Clean transcript text suitable for LLM processing
        """
        if not subtitle_text or not subtitle_text.strip():
            return ""
        
        # Use the cleaner to produce clean text
        if source_format is None:
            if subtitle_text.strip().startswith("WEBVTT"):
                return self.cleaner.clean_vtt_to_text(subtitle_text, remove_duplicates)
            else:
                return self.cleaner.clean_vtt_to_text(subtitle_text, remove_duplicates)
        
        return self.cleaner.clean_vtt_to_text(subtitle_text, remove_duplicates)

    def _parse_vtt(self, vtt_content: str) -> list[dict]:
        """Parse WebVTT subtitle format.

        VTT Format:
        WEBVTT

        00:00:01.234 --> 00:00:04.567 align:start position:0%
        Some text here

        00:00:05.000 --> 00:00:08.123 align:start position:0%
        Another subtitle line
        """
        segments = []
        
        # Skip header and process line by line
        lines = vtt_content.split('\n')
        current_start = None
        current_end = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            
            # Skip header and empty lines
            if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                continue
            if not line:
                # End of current subtitle block
                if current_start is not None and current_end is not None and current_text:
                    text_content = ' '.join(current_text)
                    text_content = re.sub(r'<[^>]+>', '', text_content)  # Remove HTML tags
                    text_content = re.sub(r'align:\w+\s*', '', text_content)  # Remove cue settings
                    text_content = re.sub(r'position:\d+%?\s*', '', text_content)
                    text_content = text_content.strip()
                    
                    if text_content:
                        segments.append({
                            "start": self._timestamp_to_seconds(current_start),
                            "end": self._timestamp_to_seconds(current_end),
                            "content": text_content,
                        })
                
                current_start = None
                current_end = None
                current_text = []
                continue
            
            # Check for timestamp line
            if '-->' in line:
                # Extract timestamps
                timestamp_pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})'
                match = re.search(timestamp_pattern, line)
                if match:
                    current_start = match.group(1)
                    current_end = match.group(2)
                else:
                    current_start = None
                    current_end = None
                    current_text = []
                continue
            
            # If we have timestamps and this is text, add to current text
            if current_start is not None and current_end is not None:
                # Skip empty lines or cue settings
                if line and not line.startswith('align:') and not line.startswith('position:'):
                    current_text.append(line)

        logger.debug("vtt_parsed", segments=len(segments))
        return segments

    def _parse_srt(self, srt_content: str) -> list[dict]:
        """Parse SRT (SubRip) subtitle format.

        SRT Format:
        1
        00:00:01,234 --> 00:00:04,567
        Some text here

        2
        00:00:05,000 --> 00:00:08,123
        Another subtitle line
        """
        segments = []
        # SRT block pattern
        block_pattern = re.compile(
            r'\d+\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n(.+?)(?=\n\n|\Z)',
            re.DOTALL,
        )

        for match in block_pattern.finditer(srt_content):
            start_str, end_str, text = match.groups()
            # Normalize comma to dot for SRT timestamps
            start_str = start_str.replace(',', '.')
            end_str = end_str.replace(',', '.')
            text = text.strip().replace('\n', ' ')

            if text:
                segments.append({
                    "start": self._timestamp_to_seconds(start_str),
                    "end": self._timestamp_to_seconds(end_str),
                    "content": text,
                })

        logger.debug("srt_parsed", segments=len(segments))
        return segments

    @staticmethod
    def _timestamp_to_seconds(timestamp: str) -> float:
        """Convert HH:MM:SS.mmm to seconds.

        Args:
            timestamp: Time string in format HH:MM:SS.mmm

        Returns:
            Total seconds as float
        """
        parts = timestamp.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        return 0.0

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean subtitle text by removing formatting artifacts.

        - Removes HTML/XML tags
        - Removes speaker labels if present (e.g., ">> SPEAKER:")
        - Normalizes whitespace
        """
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'>>\s*\w+\s*:', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()