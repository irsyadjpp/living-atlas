#!/usr/bin/env python3
"""Test script: crawl a YouTube channel and output metadata + subtitles.

Usage:
    # Install dependencies first
    pip install yt-dlp

    # Run with a YouTube handle
    python test_crawl.py --handle RJL5-FAJARADITYA --limit 5

    # Or specify max videos
    python test_crawl.py --handle JurnalRisa --limit 3

Output:
    - Prints metadata for each video
    - Shows subtitle preview (first 500 chars)
    - Saves full results to output/{channel_name}_results.json
"""

import argparse
import json
import os
import sys
import re
import hashlib
import time
from pathlib import Path
from datetime import datetime


def resolve_channel_url(handle: str) -> str:
    """Convert YouTube handle to URL.
    
    Updated to directly target /videos tab for better results.
    """
    handle = handle.strip()
    if handle.startswith("http://") or handle.startswith("https://"):
        # If already a full URL, ensure it points to videos tab
        if "/videos" not in handle and "/shorts" not in handle and "/@" in handle:
            # Convert channel URL to videos tab
            return handle.rstrip("/") + "/videos"
        return handle
    if handle.startswith("@"):
        return f"https://www.youtube.com/{handle}/videos"
    if handle.startswith("UC") and len(handle) == 24:
        return f"https://www.youtube.com/channel/{handle}/videos"
    return f"https://www.youtube.com/@{handle}/videos"


def filter_out_shorts(info, *, incomplete):
    """Filter out YouTube Shorts from crawl results.
    
    YouTube Shorts are identified by:
    1. URL containing /shorts/ pattern
    2. Vertical aspect ratio (width < height)
    3. Short duration (< 60 seconds) - optional criteria
    
    This filter ensures we only crawl regular horizontal videos.
    """
    # Check URL pattern for shorts
    url = info.get('webpage_url', '')
    if '/shorts/' in url.lower():
        return f'URL is a YouTube Short: {url}'
    
    # Check aspect ratio (vertical videos are likely shorts)
    width = info.get('width')
    height = info.get('height')
    if width and height and width < height:
        return f'Video has vertical aspect ratio ({width}x{height}), likely a Short'
    
    # Check duration (shorts are typically under 60 seconds)
    # But we allow short regular videos, so this is secondary check
    duration = info.get('duration')
    if duration is not None and duration < 30:  # Very short threshold
        return f'Video is very short ({duration}s), likely a Short'
    
    return None


def fetch_channel_videos(channel_url: str, max_videos: int = 5) -> list[dict]:
    """Fetch video metadata from a YouTube channel using yt-dlp.
    
    Uses extract_flat=True to get all video entries without downloading.
    Filters out shorts (< 60 seconds) to ensure only regular videos are crawled.
    """
    import yt_dlp
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  # Only metadata, no download
        "match_filter": filter_out_shorts,  # Filter out shorts
    }
    
    print(f"\n📡 Fetching channel: {channel_url}")
    print(f"   Max videos: {max_videos}")
    print("   🔍 Filter: Excluding YouTube Shorts (URL pattern, vertical video, very short duration)")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        
        channel_info = {
            "channel_id": info.get("channel_id", ""),
            "channel_name": info.get("channel", ""),
            "channel_url": info.get("channel_url", ""),
            "subscriber_count": info.get("subscriber_count", 0),
            "video_count": info.get("video_count", 0),
            "description": (info.get("description", "") or "")[:500],
        }
        
        # Get videos from entries
        entries = info.get("entries", [])
        if not entries:
            print("   ⚠️  No videos found in channel entries")
            # Try getting from uploads
            if "entries" not in info:
                print("   ℹ️  Trying alternative extraction method...")
                # Some channels need different handling
                entries = [info]
        
        videos = []
        shorts_filtered = 0
        for i, entry in enumerate(entries):
            if len(videos) >= max_videos:
                break
            if entry:
                # Check if entry is a short using multiple criteria
                entry_url = entry.get("url", "") or entry.get("webpage_url", "")
                duration = entry.get("duration", 0)
                width = entry.get("width")
                height = entry.get("height")
                
                is_short = False
                if '/shorts/' in entry_url.lower():
                    is_short = True
                elif width and height and width < height:
                    is_short = True
                elif duration and duration < 30:  # Very short threshold
                    is_short = True
                
                if is_short:
                    shorts_filtered += 1
                    continue
                    
                videos.append({
                    "video_id": entry.get("id", ""),
                    "title": entry.get("title", ""),
                    "duration": entry.get("duration", 0),
                    "url": entry.get("url", "") or f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                })
        
        print(f"   ✅ Found {len(videos)} regular videos (filtered {shorts_filtered} shorts)")
        
        return videos, channel_info


def fetch_video_details(video_url: str, delay_between_requests: float = 2.0) -> dict:
    """Fetch detailed metadata and subtitles for a single video.
    
    Uses yt-dlp with:
    - skip_download=True (no video/audio download)
    - writesubtitles=True (get subtitles)
    - writeautomaticsub=True (get auto-generated subs)
    - Focus on Indonesian subtitles first
    - Added delay to avoid rate limiting
    """
    import yt_dlp
    import tempfile
    
    # Add delay to avoid rate limiting
    time.sleep(delay_between_requests)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,  # CRITICAL: no video download
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["id"],  # Focus on Indonesian only
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmpdir, "%(id)s"),
            "keepvideo": False,
            # Add socket timeout to avoid hanging
            "socket_timeout": 30,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            # Read subtitle files if any were written
            subtitles = {}
            video_id = info.get("id", "")
            
            # Only focus on Indonesian subtitles
            for ext in ["vtt", "srt"]:
                sub_path = os.path.join(tmpdir, f"{video_id}.id.{ext}")
                if os.path.exists(sub_path):
                    with open(sub_path, "r", encoding="utf-8") as f:
                        subtitles["id"] = f.read()
                    os.remove(sub_path)
            
            # Fallback: check for any subtitle file
            if not subtitles:
                import glob
                for sub_file in glob.glob(os.path.join(tmpdir, f"{video_id}.*")):
                    basename = os.path.basename(sub_file)
                    parts = basename.split(".")
                    if len(parts) >= 3:
                        file_lang = parts[-2]
                        file_ext = parts[-1]
                        if file_ext in ("vtt", "srt"):
                            with open(sub_file, "r", encoding="utf-8") as f:
                                subtitles[file_lang] = f.read()
                            os.remove(sub_file)
            
            # Also check requested_subtitles from yt-dlp response
            requested_subs = info.get("requested_subtitles") or {}
            
            return {
                "video_id": info.get("id", ""),
                "title": info.get("title", ""),
                "description": (info.get("description", "") or "")[:2000],
                "duration": info.get("duration", 0),
                "duration_string": info.get("duration_string", ""),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "comment_count": info.get("comment_count", 0),
                "channel_id": info.get("channel_id", ""),
                "channel_name": info.get("channel", ""),
                "channel_url": info.get("channel_url", ""),
                "uploader": info.get("uploader", ""),
                "webpage_url": info.get("webpage_url", ""),
                "thumbnail": info.get("thumbnail", ""),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "language": info.get("language", ""),
                "is_live": info.get("is_live", False),
                "was_live": info.get("was_live", False),
                "availability": info.get("availability", ""),
                "has_subtitles": bool(subtitles) or len(requested_subs) > 0,
                "subtitle_languages": list(subtitles.keys()) or list(requested_subs.keys()),
                "subtitle_text": subtitles,  # Raw subtitle text (VTT format)
                "raw_payload_fields": {
                    k: info[k] for k in [
                        "id", "title", "description", "duration", "view_count",
                        "like_count", "comment_count", "channel_id", "channel",
                        "uploader", "upload_date", "tags", "categories",
                        "webpage_url", "thumbnail"
                    ] if k in info
                },
            }


def parse_vtt_segments(vtt_content: str) -> list[dict]:
    """Parse VTT subtitle content into structured segments.
    
    Returns: [{start, end, content}]
    """
    segments = []
    block_pattern = re.compile(
        r'(\d{2}:?\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:?\d{2}:\d{2}\.\d{3})\s*\n(.+?)(?=\n\n|\Z)',
        re.DOTALL,
    )
    for match in block_pattern.finditer(vtt_content):
        start_str, end_str, text = match.groups()
        text = text.strip().replace("\n", " ")
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'align:\w+\s*', '', text)
        text = re.sub(r'position:\d+%?\s*', '', text)
        
        def ts_to_seconds(ts: str) -> float:
            parts = ts.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            return 0.0
        
        if text:
            segments.append({
                "start_seconds": ts_to_seconds(start_str),
                "end_seconds": ts_to_seconds(end_str),
                "text": text,
            })
    return segments


def main():
    parser = argparse.ArgumentParser(description="Test YouTube channel crawl with metadata + subtitle extraction")
    parser.add_argument("--handle", type=str, default="RJL5-FAJARADITYA", help="YouTube channel handle (e.g., RJL5-FAJARADITYA)")
    parser.add_argument("--limit", type=int, default=5, help="Number of videos to crawl")
    parser.add_argument("--output", type=str, default="output", help="Output directory")
    parser.add_argument("--save-json", action="store_true", default=True, help="Save results to JSON file")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🧪 INGESTION SERVICE — LOCAL TEST")
    print("=" * 70)
    print(f"   Channel: @{args.handle}")
    print(f"   Max Videos: {args.limit}")
    print(f"   Output: {args.output}/")
    print("=" * 70)
    
    # Step 1: Resolve channel URL and fetch video list
    channel_url = resolve_channel_url(args.handle)
    print(f"\n📋 Channel URL: {channel_url}")
    
    videos, channel_info = fetch_channel_videos(channel_url, args.limit)
    
    if not videos:
        print("\n❌ No videos found. The channel might not exist or yt-dlp might need an update.")
        sys.exit(1)
    
    print(f"\n✅ Found {len(videos)} videos in channel '{channel_info['channel_name']}'")
    print(f"   Channel ID: {channel_info['channel_id']}")
    print(f"   Subscribers: {channel_info.get('subscriber_count', 'N/A')}")
    
    # Step 2: Fetch detailed info + subtitles for each video
    results = {
        "channel": {
            "handle": args.handle,
            "name": channel_info["channel_name"],
            "channel_id": channel_info["channel_id"],
            "channel_url": channel_info["channel_url"],
            "subscriber_count": channel_info.get("subscriber_count", 0),
            "video_count": channel_info.get("video_count", 0),
            "description": channel_info.get("description", ""),
        },
        "crawl_timestamp": datetime.now().isoformat(),
        "videos": [],
        "summary": {
            "total_videos": 0,
            "with_subtitles": 0,
            "without_subtitles": 0,
            "total_subtitle_segments": 0,
        }
    }
    
    for i, video_meta in enumerate(videos, 1):
        video_url = video_meta["url"]
        print(f"\n{'─' * 50}")
        print(f"📹 Video {i}/{len(videos)}: {video_meta['title']}")
        print(f"   ID: {video_meta['video_id']}")
        print(f"   Duration: {video_meta.get('duration', 0)}s")
        
        try:
            details = fetch_video_details(video_url, delay_between_requests=3.0)  # 3 second delay
            
            has_subs = details.get("has_subtitles", False)
            sub_langs = details.get("subtitle_languages", [])
            subtitle_text = details.get("subtitle_text", {})
            
            # Parse subtitles into segments
            parsed_segments = {}
            total_segments = 0
            for lang, text in subtitle_text.items():
                segments = parse_vtt_segments(text)
                parsed_segments[lang] = segments
                total_segments += len(segments)
            
            print(f"   Views: {details.get('view_count', 0):,}")
            print(f"   Likes: {details.get('like_count', 0):,}")
            print(f"   Upload: {details.get('upload_date', 'N/A')}")
            print(f"   Subtitles: {'✅ YES' if has_subs else '❌ NO'} {sub_langs}")
            
            if has_subs and parsed_segments:
                for lang, segs in parsed_segments.items():
                    print(f"   ├── {lang}: {len(segs)} segments")
                    if segs:
                        # Show first 3 segments as preview
                        for j, seg in enumerate(segs[:3]):
                            print(f"   │   [{seg['start_seconds']:.1f}s - {seg['end_seconds']:.1f}s] {seg['text'][:80]}...")
                        if len(segs) > 3:
                            print(f"   │   ... and {len(segs) - 3} more segments")
            
            if details.get("tags"):
                print(f"   Tags: {', '.join(details['tags'][:5])}")
                if len(details['tags']) > 5:
                    print(f"         ... and {len(details['tags']) - 5} more")
            
            video_result = {
                "index": i,
                "video_id": details["video_id"],
                "title": details["title"],
                "description": details.get("description", ""),
                "duration_seconds": details.get("duration", 0),
                "duration_string": details.get("duration_string", ""),
                "upload_date": details.get("upload_date", ""),
                "view_count": details.get("view_count", 0),
                "like_count": details.get("like_count", 0),
                "comment_count": details.get("comment_count", 0),
                "channel_name": details.get("channel_name", ""),
                "channel_id": details.get("channel_id", ""),
                "webpage_url": details.get("webpage_url", ""),
                "thumbnail_url": details.get("thumbnail", ""),
                "tags": details.get("tags", []),
                "categories": details.get("categories", []),
                "language": details.get("language", ""),
                "availability": details.get("availability", ""),
                "has_subtitles": has_subs,
                "subtitle_languages": sub_langs,
                "subtitle_segments": {lang: segs for lang, segs in parsed_segments.items()},
                "subtitle_preview": {
                    lang: subtitle_text[lang][:500] 
                    for lang in subtitle_text
                },
                "subtitle_full_text": subtitle_text,  # Full subtitle text
                "raw_payload": details.get("raw_payload_fields", {}),
            }
            
            results["videos"].append(video_result)
            results["summary"]["total_videos"] += 1
            if has_subs:
                results["summary"]["with_subtitles"] += 1
            else:
                results["summary"]["without_subtitles"] += 1
            results["summary"]["total_subtitle_segments"] += total_segments
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results["videos"].append({
                "index": i,
                "video_id": video_meta["video_id"],
                "title": video_meta["title"],
                "error": str(e),
            })
    
    # Step 3: Print summary
    print(f"\n{'=' * 70}")
    print("📊 CRAWL SUMMARY")
    print(f"{'=' * 70}")
    print(f"   Channel: {channel_info.get('channel_name', args.handle)}")
    print(f"   Videos crawled: {results['summary']['total_videos']}")
    print(f"   With subtitles: {results['summary']['with_subtitles']}")
    print(f"   Without subtitles: {results['summary']['without_subtitles']}")
    print(f"   Total subtitle segments: {results['summary']['total_subtitle_segments']}")
    
    available_langs = set()
    for v in results["videos"]:
        for lang in v.get("subtitle_languages", []):
            available_langs.add(lang)
    if available_langs:
        print(f"   Subtitle languages detected: {', '.join(sorted(available_langs))}")
    
    # Step 4: Save to JSON
    if args.save_json:
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        
        # Use channel name for filename
        safe_name = re.sub(r'[^\w-]', '_', channel_info.get("channel_name", args.handle))
        output_file = output_dir / f"{safe_name}_crawl_results.json"
        
        # Custom JSON encoder for datetime
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, cls=DateTimeEncoder)
        
        file_size = output_file.stat().st_size
        print(f"\n💾 Results saved to: {output_file} ({file_size:,} bytes)")
    
    print(f"\n✅ Done! Test completed successfully.")
    print(f"   To view the full JSON results: cat {output_file} | head -200")


if __name__ == "__main__":
    main()