#!/usr/bin/env python3
"""Extract subtitle from a single YouTube video and save as .vtt file."""

import sys
import time
from pathlib import Path

import yt_dlp


def extract_subtitle_to_vtt(video_url: str, output_dir: str = "/tmp/subtitles_vtt"):
    """Extract subtitle from a single video and save as .vtt file."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Try to get video ID from URL
    video_id = video_url.split("v=")[-1].split("&")[0] if "v=" in video_url else "video"
    
    output_file = output_path / f"{video_id}_id.vtt"
    
    print(f"Extracting subtitle from: {video_url}")
    print(f"Output file: {output_file}")
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["id", "en"],
        "subtitlesformat": "vtt",
        "skip_download": True,
        "outtmpl": str(output_path / "%(id)s"),
        "keepvideo": False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            # Find the subtitle file that was downloaded
            subtitle_file = None
            for ext in [".id.vtt", ".en.vtt", ".vtt"]:
                potential_file = output_path / f"{video_id}{ext}"
                if potential_file.exists():
                    subtitle_file = potential_file
                    break
            
            if subtitle_file:
                print(f"✅ Subtitle saved to: {subtitle_file}")
                
                # Show preview
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"📊 File size: {len(content)} characters")
                print(f"\n📄 First 500 characters:")
                print(content[:500])
                
                return str(subtitle_file)
            else:
                print("❌ No subtitle file found")
                # List all files in directory
                print(f"Files in {output_path}:")
                for file in output_path.glob("*"):
                    print(f"  - {file.name}")
                return None
                
    except Exception as e:
        print(f"❌ Error extracting subtitle: {e}")
        return None


if __name__ == "__main__":
    # Use the RJL 5 video that we know has subtitles
    video_url = "https://www.youtube.com/watch?v=p6XSDm2yXTY"
    
    print("=" * 70)
    print("🔍 SUBTITLE EXTRACTION TO .VTT")
    print("=" * 70)
    print()
    
    result = extract_subtitle_to_vtt(video_url)
    
    if result:
        print()
        print("=" * 70)
        print("✅ SUBTITLE EXTRACTION SUCCESSFUL")
        print("=" * 70)
        print(f"📁 File: {result}")
        print()
        print("📝 Full transcript can be viewed with:")
        print(f"   cat {result}")
    else:
        print()
        print("❌ Failed to extract subtitle")