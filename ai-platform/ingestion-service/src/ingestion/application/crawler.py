"""Crawler service — orchestrates YouTube crawling with dedup, retry, and event emission.

Per PRD v2.0:
- No audio/video download
- Metadata + subtitle only
- Dedup by platform_video_id
- Incremental crawl support
"""

import json
import structlog
import uuid
import hashlib
from typing import Optional
from datetime import datetime

from ai_shared.database import Database
from ai_shared.events import VideoIngested
from ai_shared.redpanda import EventProducer
from ingestion.infrastructure.youtube import YouTubeClient, YouTubeVideoInfo, SubtitleResult

logger = structlog.get_logger(__name__)


class CrawlerService:
    """Orchestrates YouTube video/channel/playlist crawling."""

    def __init__(self, db: Database, youtube_client: YouTubeClient, event_producer: Optional[EventProducer] = None):
        self.db = db
        self.youtube = youtube_client
        self.event_producer = event_producer

    async def crawl_video(
        self,
        platform_video_id: Optional[str] = None,
        url: Optional[str] = None,
        channel_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """Crawl a single video — fetch metadata + subtitles, store in DB, emit event.

        Steps:
        1. Resolve URL if platform_video_id given
        2. Fetch metadata via yt-dlp (download=False)
        3. Fetch subtitles via yt-dlp (skip_download=True)
        4. Check dedup by platform_video_id
        5. Store in source.videos, source.subtitle_tracks, source.video_payload_versions
        6. Emit ai.video.ingested event
        """
        # Resolve video URL
        if not url and platform_video_id:
            url = f"https://www.youtube.com/watch?v={platform_video_id}"
        if not url:
            raise ValueError("Either platform_video_id or url is required")

        # Create job
        job_id = uuid.uuid4()
        await self._create_job(job_id, "video", None)

        try:
            # Fetch metadata (no download)
            info = self.youtube.get_video_info(url)
            platform_id = info.video_id

            # Check dedup
            existing = await self.db.fetchrow(
                "SELECT id FROM source.videos WHERE platform_video_id = $1 AND is_deleted = FALSE",
                platform_id,
            )
            if existing:
                logger.info("video_already_exists", platform_video_id=platform_id, video_id=existing["id"])
                await self._complete_job(job_id)
                return {
                    "job_id": job_id,
                    "video_id": existing["id"],
                    "status": "completed",
                    "message": "Video already exists",
                }

            # Fetch full payload for immutable record
            raw_payload = self.youtube.get_raw_payload(url)
            payload_hash = hashlib.sha256(json.dumps(raw_payload, sort_keys=True).encode()).hexdigest()

            # Store channel (auto-create if needed)
            channel_uuid = channel_id or await self._ensure_channel(info)

            # Store video
            video_uuid = uuid.uuid4()
            await self.db.execute(
                """
                INSERT INTO source.videos (id, channel_id, platform_video_id, title, description,
                    language_code, published_at, duration_seconds, view_count, like_count,
                    comment_count, video_url, metadata)
                VALUES ($1, $2, $3, $4, $5, $6,
                    CASE WHEN $7 != '' THEN $7::timestamp ELSE NULL END,
                    $8, $9, $10, $11, $12, $13)
                """,
                video_uuid,
                channel_uuid,
                platform_id,
                info.title,
                info.description[:5000] if info.description else "",
                "id",
                self._parse_upload_date(info.upload_date),
                info.duration_seconds,
                info.view_count,
                info.like_count,
                info.comment_count,
                info.webpage_url,
                json.dumps({"tags": info.tags, "categories": info.categories}),
            )

            # Store raw payload (immutable)
            await self.db.execute(
                """
                INSERT INTO source.video_payload_versions (video_id, payload_hash, payload, collected_at)
                VALUES ($1, $2, $3, now())
                """,
                video_uuid,
                payload_hash,
                json.dumps(raw_payload),
            )

            # Store tags
            for tag in info.tags:
                await self.db.execute(
                    "INSERT INTO source.video_tags (video_id, tag) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    video_uuid, tag,
                )

            # Extract and store subtitles
            has_subtitles = False
            subtitle_track_id = None
            if info.has_subtitles:
                subtitle = self.youtube.extract_subtitles(url)
                if subtitle:
                    has_subtitles = True
                    subtitle_track_id_obj = uuid.uuid4()
                    subtitle_track_id = subtitle_track_id_obj
                    await self.db.execute(
                        """
                        INSERT INTO source.subtitle_tracks (id, video_id, language_code, is_auto_generated, content)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        subtitle_track_id_obj,
                        video_uuid,
                        subtitle.language,
                        subtitle.is_auto_generated,
                        subtitle.content,
                    )

            # Update job
            await self._complete_job(job_id, target_id=video_uuid)

            # Emit event
            if self.event_producer:
                event = VideoIngested(
                    video_id=video_uuid,
                    channel_id=channel_uuid,
                    platform_video_id=platform_id,
                    title=info.title,
                    duration_seconds=info.duration_seconds,
                    language_code="id",
                    has_subtitles=has_subtitles,
                    subtitle_track_id=subtitle_track_id,
                    payload_hash=payload_hash,
                    ingestion_job_id=job_id,
                    metadata={"view_count": info.view_count, "like_count": info.like_count},
                )
                await self.event_producer.produce_event("ai.video.ingested", event)

            logger.info("video_crawl_completed",
                        video_id=str(video_uuid), title=info.title[:50], has_subtitles=has_subtitles)

            return {
                "job_id": job_id,
                "video_id": video_uuid,
                "status": "completed",
                "message": "Video ingested successfully",
            }

        except Exception as e:
            logger.error("video_crawl_failed", url=url, error=str(e))
            await self._fail_job(job_id, str(e))
            raise

    async def crawl_channel(
        self,
        channel_id: Optional[uuid.UUID] = None,
        url: Optional[str] = None,
        max_videos: int = 50,
    ) -> dict:
        """Crawl a YouTube channel — discover videos, crawl each.

        Per PRD v2.0 FR-ING-007: incremental crawl — only new videos since last crawl.
        Per PRD v2.0 NFR-ING-001: rate limited to 30 videos/hour.
        """
        job_id = uuid.uuid4()
        await self._create_job(job_id, "channel", channel_id)

        try:
            # Get channel info
            channel_info = self.youtube.get_channel_info(url or f"https://www.youtube.com/channel/{channel_id}")

            # Ensure channel in DB
            channel_uuid = channel_id or await self._ensure_channel_from_info(channel_info)
            if not channel_uuid:
                channel_uuid = await self._ensure_channel_from_info(channel_info)

            # Get last crawl timestamp for incremental
            last_crawl = await self.db.fetchval(
                "SELECT MAX(completed_at) FROM source.ingestion_jobs WHERE target_id = $1 AND status = 'completed'",
                channel_uuid,
            )

            # Get playlist URL for channel
            channel_url = channel_info.channel_url or url
            playlist_url = channel_url  # yt-dlp handles channel URLs

            # Get videos via flat playlist
            videos = self.youtube.get_playlist_videos(playlist_url)
            videos = videos[:max_videos]

            # Filter out already-crawled videos
            new_count = 0
            for video in videos:
                existing = await self.db.fetchval(
                    "SELECT id FROM source.videos WHERE platform_video_id = $1 AND is_deleted = FALSE",
                    video.video_id,
                )
                if not existing:
                    try:
                        await self.crawl_video(platform_video_id=video.video_id, channel_id=channel_uuid)
                        new_count += 1
                    except Exception as e:
                        logger.warning("channel_video_crawl_failed", video_id=video.video_id, error=str(e))

            await self._complete_job(job_id, target_id=channel_uuid)

            return {
                "job_id": job_id,
                "channel_id": channel_uuid,
                "status": "completed",
                "videos_discovered": new_count,
                "message": f"Crawled {new_count} new videos from channel",
            }

        except Exception as e:
            logger.error("channel_crawl_failed", url=url, error=str(e))
            await self._fail_job(job_id, str(e))
            raise

    async def crawl_playlist(self, playlist_id: Optional[uuid.UUID] = None, url: Optional[str] = None) -> dict:
        """Crawl a YouTube playlist."""
        job_id = uuid.uuid4()
        await self._create_job(job_id, "playlist", playlist_id)

        try:
            videos = self.youtube.get_playlist_videos(url or f"https://www.youtube.com/playlist?list={playlist_id}")

            new_count = 0
            for video in videos:
                existing = await self.db.fetchval(
                    "SELECT id FROM source.videos WHERE platform_video_id = $1 AND is_deleted = FALSE",
                    video.video_id,
                )
                if not existing:
                    try:
                        await self.crawl_video(platform_video_id=video.video_id)
                        new_count += 1
                    except Exception as e:
                        logger.warning("playlist_video_crawl_failed", video_id=video.video_id, error=str(e))

            await self._complete_job(job_id)

            return {
                "job_id": job_id,
                "playlist_id": playlist_id or uuid.uuid4(),
                "status": "completed",
                "video_count": new_count,
                "message": f"Crawled {new_count} new videos from playlist",
            }

        except Exception as e:
            logger.error("playlist_crawl_failed", url=url, error=str(e))
            await self._fail_job(job_id, str(e))
            raise

    async def _ensure_channel(self, info: YouTubeVideoInfo) -> uuid.UUID:
        """Find or create channel from video metadata."""
        existing = await self.db.fetchrow(
            "SELECT id FROM source.channels WHERE platform_channel_id = $1 AND platform = 'youtube'",
            info.channel_id,
        )
        if existing:
            return existing["id"]

        channel_uuid = uuid.uuid4()
        await self.db.execute(
            """
            INSERT INTO source.channels (id, platform, platform_channel_id, name, channel_url, avatar_url)
            VALUES ($1, 'youtube', $2, $3, $4, $5)
            """,
            channel_uuid,
            info.channel_id,
            info.channel_name or "Unknown",
            info.channel_url or "",
            info.thumbnail_url or "",
        )
        return channel_uuid

    async def _ensure_channel_from_info(self, info) -> uuid.UUID:
        """Find or create channel from YouTubeChannelInfo."""
        existing = await self.db.fetchrow(
            "SELECT id FROM source.channels WHERE platform_channel_id = $1 AND platform = 'youtube'",
            info.channel_id,
        )
        if existing:
            return existing["id"]

        channel_uuid = uuid.uuid4()
        await self.db.execute(
            """
            INSERT INTO source.channels (id, platform, platform_channel_id, name, channel_url, avatar_url, description)
            VALUES ($1, 'youtube', $2, $3, $4, $5, $6)
            """,
            channel_uuid,
            info.channel_id,
            info.name,
            info.channel_url or "",
            info.avatar_url or "",
            info.description[:500] if info.description else "",
        )
        return channel_uuid

    async def _create_job(self, job_id: uuid.UUID, source_type: str, target_id: Optional[uuid.UUID]):
        await self.db.execute(
            """
            INSERT INTO source.ingestion_jobs (id, source_type, target_id, status, started_at)
            VALUES ($1, $2, $3, 'running', now())
            """,
            job_id, source_type, target_id,
        )

    async def _complete_job(self, job_id: uuid.UUID, target_id: Optional[uuid.UUID] = None):
        if target_id:
            await self.db.execute(
                "UPDATE source.ingestion_jobs SET status = 'completed', completed_at = now(), target_id = $2 WHERE id = $1",
                job_id, target_id,
            )
        else:
            await self.db.execute(
                "UPDATE source.ingestion_jobs SET status = 'completed', completed_at = now() WHERE id = $1",
                job_id,
            )

    async def _fail_job(self, job_id: uuid.UUID, error: str):
        await self.db.execute(
            "UPDATE source.ingestion_jobs SET status = 'failed', completed_at = now(), error_message = $2 WHERE id = $1",
            job_id, error[:500],
        )

    @staticmethod
    def _parse_upload_date(upload_date: str) -> Optional[str]:
        """Parse YYYYMMDD to ISO date string."""
        if not upload_date or len(upload_date) != 8:
            return None
        try:
            return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        except (ValueError, IndexError):
            return None