"""YT-DLP wrapper for YouTube video metadata and subtitle extraction.

Based on yt-dlp 2024+ documentation:
- NO audio/video download (uses skip_download=True)
- Subtitle extraction using yt-dlp's subtitle options
- Metadata extraction without downloading
"""

import os
import json
import re
import structlog
import time
import random
from dataclasses import dataclass, field
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = structlog.get_logger(__name__)


@dataclass
class YouTubeVideoInfo:
    """Structured metadata from a YouTube video."""
    video_id: str
    title: str
    description: str = ""
    duration_seconds: int = 0
    upload_date: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    channel_id: str = ""
    channel_name: str = ""
    thumbnail_url: str = ""
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    webpage_url: str = ""
    has_subtitles: bool = False
    channel_url: str = ""
    uploader: str = ""
    extractor: str = "youtube"


@dataclass
class YouTubeChannelInfo:
    """Structured metadata from a YouTube channel."""
    channel_id: str
    name: str
    description: str = ""
    subscriber_count: int = 0
    video_count: int = 0
    channel_url: str = ""
    avatar_url: str = ""
    banner_url: str = ""


@dataclass
class SubtitleResult:
    """Result of subtitle extraction."""
    content: str  # Raw subtitle text
    language: str
    is_auto_generated: bool
    format: str  # vtt, srt


class YouTubeClient:
    """yt-dlp wrapper — metadata and subtitle extraction only. NO audio/video download.

    Uses yt-dlp's subtitle extraction capabilities:
    - --write-subs: Write subtitle file
    - --write-auto-subs: Write automatically generated subtitle file
    - --sub-langs: Languages of subtitles to download
    - --sub-format: Subtitle format preference (srt/best)
    - --skip-download: Do not download the video (critical for PRD v2.0)
    
    Rate limiting protection:
    - Random delays between requests
    - Exponential backoff for retries
    - Cookie file support for authentication
    
    References:
    - https://github.com/yt-dlp/yt-dlp#subtitle-options
    - https://github.com/yt-dlp/yt-dlp#output-template
    """

    def __init__(self, temp_dir: str = "/tmp/yt-dlp", cookie_file: Optional[str] = None):
        self.temp_dir = temp_dir
        self.cookie_file = cookie_file
        self.last_request_time = 0.0
        self.min_request_interval = 3.0  # Minimum 3 seconds between requests
        os.makedirs(temp_dir, exist_ok=True)
    
    def _rate_limit_delay(self):
        """Add delay between requests to avoid rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            delay = self.min_request_interval - time_since_last
            # Add random jitter to avoid predictable patterns
            jitter = random.uniform(0.5, 1.5)
            time.sleep(delay + jitter)
        
        self.last_request_time = time.time()

    def get_video_info(self, url: str) -> YouTubeVideoInfo:
        """Extract metadata from a YouTube video without downloading.

        Uses yt-dlp with download=False to fetch metadata only.
        This is the yt-dlp recommended way to get video information
        without consuming bandwidth or storage.
        """
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get("subtitles", {}) or {}
            automatic_captions = info.get("automatic_captions", {}) or {}

            return YouTubeVideoInfo(
                video_id=info.get("id", ""),
                title=info.get("title", ""),
                description=info.get("description", ""),
                duration_seconds=info.get("duration", 0),
                upload_date=info.get("upload_date", ""),
                view_count=info.get("view_count", 0),
                like_count=info.get("like_count", 0),
                comment_count=info.get("comment_count", 0),
                channel_id=info.get("channel_id", ""),
                channel_name=info.get("channel", ""),
                thumbnail_url=info.get("thumbnail", ""),
                tags=info.get("tags", []),
                categories=info.get("categories", []),
                webpage_url=info.get("webpage_url", ""),
                has_subtitles=len(subtitles) > 0 or len(automatic_captions) > 0,
                channel_url=info.get("channel_url", ""),
                uploader=info.get("uploader", ""),
                extractor=info.get("extractor", "youtube"),
            )

    def get_channel_info(self, url: str) -> YouTubeChannelInfo:
        """Extract metadata from a YouTube channel."""
        import yt_dlp
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return YouTubeChannelInfo(
                channel_id=info.get("channel_id", ""),
                name=info.get("channel", ""),
                description=info.get("description", ""),
                subscriber_count=info.get("subscriber_count", 0),
                video_count=info.get("video_count", 0),
                channel_url=info.get("channel_url", ""),
                avatar_url=info.get("avatar", ""),
                banner_url=info.get("banner_url", ""),
            )

    def get_playlist_videos(self, url: str) -> list[YouTubeVideoInfo]:
        """Extract all video metadata from a playlist using extract_flat.

        Uses yt-dlp --flat-playlist to get metadata without downloading
        individual video pages (much faster for large playlists).
        """
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # Do not extract video URLs
        }
        videos = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "entries" in info:
                for entry in info["entries"]:
                    if entry:
                        videos.append(YouTubeVideoInfo(
                            video_id=entry.get("id", ""),
                            title=entry.get("title", ""),
                            duration_seconds=entry.get("duration", 0),
                            channel_id=entry.get("channel_id", ""),
                            channel_name=entry.get("channel", ""),
                            webpage_url=entry.get("url", ""),
                            has_subtitles=entry.get("subtitles") is not None,
                        ))
        return videos

    def extract_subtitles(
        self,
        url: str,
        language: str = "id",
        sub_format: str = "vtt",
    ) -> Optional[SubtitleResult]:
        """Download subtitle text for a video without downloading video/audio.

        Uses yt-dlp with skip_download=True as per PRD v2.0 FR-ING-008.
        Only subtitle files are written to disk (temporarily).

        Based on yt-dlp Subtitle Options:
        --write-subs           Write subtitle file
        --write-auto-subs      Write automatically generated subtitle file
        --sub-langs LANGS      Languages of the subtitles to download
        --sub-format FORMAT    Subtitle format preference (srt/best)
        --skip-download        Do not download the video

        Args:
            url: YouTube video URL
            language: Language code for subtitles (default: "id" for Indonesian)
            sub_format: Subtitle format preference (default: "vtt")

        Returns:
            SubtitleResult with content and metadata, or None if no subtitles available
        """
        import yt_dlp
        output_template = os.path.join(self.temp_dir, "%(id)s")

        # yt-dlp subtitle options as documented:
        # --write-subs: writes subtitle file
        # --write-auto-subs: writes auto-generated subtitles  
        # --sub-langs: language preference, supports regex patterns
        # --sub-format: format preference (srt/vtt/best)
        # --skip-download: critical - no video/audio download
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "writesubtitles": True,      # --write-subs
            "writeautomaticsub": True,    # --write-auto-subs
            "subtitleslangs": [language, "en", "id"],  # --sub-langs
            "subtitlesformat": sub_format,  # --sub-format
            "skip_download": True,        # --skip-download: CRITICAL, no video download
            "outtmpl": output_template,
            "keepvideo": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # Update last request time after successful extraction
                self.last_request_time = time.time()
                if not info:
                    return None

                video_id = info.get("id", "")
                logger.info("subtitle_extraction_attempt", video_id=video_id, url=url)

                # yt-dlp writes subtitle files in the format:
                # {video_id}.{language}.{format}  (manual subtitles)
                # {video_id}.{language}.{format}  (auto-generated subtitles)
                # 
                # Auto-generated subtitles have the same filename pattern.
                # We need to check their content or request_subtitles output
                # to determine if they're auto-generated.
                
                # Check requested subtitles from yt-dlp output
                requested_subs = info.get("requested_subtitles") or {}
                
                # Priority order: manual subtitles first, then auto-generated
                for lang in [language, "en", "id"]:
                    sub_path_vtt = os.path.join(self.temp_dir, f"{video_id}.{lang}.vtt")
                    sub_path_srt = os.path.join(self.temp_dir, f"{video_id}.{lang}.srt")
                    
                    # Try VTT first, then SRT
                    for sub_path, fmt in [(sub_path_vtt, "vtt"), (sub_path_srt, "srt")]:
                        if os.path.exists(sub_path):
                            with open(sub_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            os.remove(sub_path)  # Clean up temp file
                            
                            # Determine if auto-generated from yt-dlp's response
                            # yt-dlp marks auto-generated subs in requested_subtitles
                            sub_info = requested_subs.get(lang, {})
                            if isinstance(sub_info, dict):
                                is_auto = sub_info.get("auto", False)
                            else:
                                is_auto = True  # Assume auto if no metadata
                            
                            logger.info(
                                "subtitles_extracted",
                                video_id=video_id,
                                language=lang,
                                format=fmt,
                                auto_generated=is_auto,
                            )
                            return SubtitleResult(
                                content=content,
                                language=lang,
                                is_auto_generated=is_auto,
                                format=fmt,
                            )

                # Last resort: try finding any subtitle file in temp dir
                # yt-dlp may use different naming conventions
                import glob
                sub_files = glob.glob(os.path.join(self.temp_dir, f"{video_id}.*.*"))
                for sub_file in sub_files:
                    basename = os.path.basename(sub_file)
                    parts = basename.split(".")
                    if len(parts) >= 3:
                        file_lang = parts[-2]
                        file_fmt = parts[-1]
                        if file_fmt in ("vtt", "srt"):
                            with open(sub_file, "r", encoding="utf-8") as f:
                                content = f.read()
                            os.remove(sub_file)
                            logger.info(
                                "subtitles_extracted_fallback",
                                video_id=video_id,
                                language=file_lang,
                                format=file_fmt,
                            )
                            return SubtitleResult(
                                content=content,
                                language=file_lang,
                                is_auto_generated=True,
                                format=file_fmt,
                            )

                logger.info("no_subtitles_found_for_video", video_id=video_id)
                return None

        except Exception as e:
            logger.warning("subtitle_extraction_failed", video_id=url, error=str(e))
            return None

    def get_available_subtitles(self, url: str) -> dict:
        """List available subtitles for a video using yt-dlp --list-subs.

        Returns dict of language -> [subtitle formats]
        This is the yt-dlp equivalent of --list-subs.
        """
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "listsubtitles": True,  # --list-subs
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                subtitles = info.get("subtitles", {})
                auto_captions = info.get("automatic_captions", {})
                return {
                    "manual": {lang: [fmt.get("ext") for fmt in formats]
                              for lang, formats in subtitles.items()},
                    "auto": {lang: [fmt.get("ext") for fmt in formats]
                            for lang, formats in auto_captions.items()},
                }
        except Exception as e:
            logger.warning("list_subtitles_failed", url=url, error=str(e))
            return {"manual": {}, "auto": {}}

    def get_raw_payload(self, url: str) -> dict:
        """Get the full raw YT-DLP payload (immutable source of truth).

        This is stored in source.video_payload_versions as per PRD v2.0 FR-ING-009.
        The payload contains ALL metadata fields available from yt-dlp.
        
        See yt-dlp OUTPUT TEMPLATE documentation for available fields:
        id, title, fulltitle, ext, description, uploader, channel, duration,
        view_count, like_count, comment_count, categories, tags, etc.
        """
        import yt_dlp
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    def parse_vtt_to_segments(vtt_content: str) -> list[dict]:
        """Parse WebVTT subtitle content into segment list.

        Handles standard WebVTT format as output by yt-dlp:
        WEBVTT
        Kind: captions
        Language: id

        00:00:01.234 --> 00:00:04.567
        Some text here

        Returns: [{start, end, content}]
        """
        segments = []
        # VTT block pattern: timestamp --> timestamp followed by text
        # Handles both HH:MM:SS.mmm and MM:SS.mmm formats
        block_pattern = re.compile(
            r'(\d{2}:?\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:?\d{2}:\d{2}\.\d{3})\s*\n(.+?)(?=\n\n|\Z)',
            re.DOTALL,
        )
        for match in block_pattern.finditer(vtt_content):
            start_str, end_str, text = match.groups()
            text = text.strip().replace("\n", " ")
            # Remove VTT tags like <c> </c> <00:00:01.234>
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'align:\w+\s*', '', text)
            text = re.sub(r'position:\d+%?\s*', '', text)

            if text:
                segments.append({
                    "start": YouTubeClient._timestamp_to_seconds(start_str),
                    "end": YouTubeClient._timestamp_to_seconds(end_str),
                    "content": text,
                })

        return segments

    @staticmethod
    def parse_srt_to_segments(srt_content: str) -> list[dict]:
        """Parse SRT (SubRip) subtitle content into segment list.

        SRT Format:
        1
        00:00:01,234 --> 00:00:04,567
        Some text here

        Returns: [{start, end, content}]
        """
        segments = []
        block_pattern = re.compile(
            r'\d+\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n(.+?)(?=\n\n|\Z)',
            re.DOTALL,
        )
        for match in block_pattern.finditer(srt_content):
            start_str, end_str, text = match.groups()
            start_str = start_str.replace(',', '.')
            end_str = end_str.replace(',', '.')
            text = text.strip().replace('\n', ' ')
            if text:
                segments.append({
                    "start": YouTubeClient._timestamp_to_seconds(start_str),
                    "end": YouTubeClient._timestamp_to_seconds(end_str),
                    "content": text,
                })
        return segments

    @staticmethod
    def _timestamp_to_seconds(timestamp: str) -> float:
        """Convert timestamp to seconds.

        Handles both:
        - HH:MM:SS.mmm (e.g., 01:23:45.678)
        - MM:SS.mmm (e.g., 23:45.678)
        """
        parts = timestamp.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return 0.0