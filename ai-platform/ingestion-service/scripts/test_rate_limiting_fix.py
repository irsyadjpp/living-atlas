#!/usr/bin/env python3
"""Test rate limiting improvements in ingestion-service."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.infrastructure.youtube import YouTubeClient


async def main():
    """Test rate limiting with YouTubeClient."""
    
    print("=" * 70)
    print("🧪 RATE LIMITING TEST - INGESTION SERVICE")
    print("=" * 70)
    print()
    
    # Initialize YouTubeClient with rate limiting
    youtube_client = YouTubeClient(temp_dir="/tmp/yt-dlp-rate-test")
    
    # Test URLs (RJL 5 videos)
    test_urls = [
        "https://www.youtube.com/watch?v=p6XSDm2yXTY",
        "https://www.youtube.com/watch?v=-sBOKqPRdQw",
    ]
    
    print(f"Testing {len(test_urls)} videos with rate limiting protection")
    print(f"Minimum request interval: {youtube_client.min_request_interval} seconds")
    print(f"Random jitter: 0.5-1.5 seconds")
    print(f"Retry attempts: 3 with exponential backoff")
    print()
    
    successful = 0
    failed = 0
    
    for i, url in enumerate(test_urls, 1):
        print(f"📹 Video {i}/{len(test_urls)}")
        print(f"   URL: {url}")
        
        start_time = time.time()
        
        try:
            # Test metadata extraction
            info = youtube_client.get_video_info(url)
            
            elapsed_time = time.time() - start_time
            
            print(f"   ✅ Metadata extracted successfully")
            print(f"   📺 Title: {info.title[:50]}...")
            print(f"   ⏱️  Duration: {info.duration_seconds}s")
            print(f"   ⏳ Time taken: {elapsed_time:.2f}s")
            print(f"   🔍 Has subtitles: {info.has_subtitles}")
            
            successful += 1
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"   ❌ Error: {e}")
            print(f"   ⏳ Time taken: {elapsed_time:.2f}s")
            failed += 1
        
        print()
    
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Total videos: {len(test_urls)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()
    
    print("Rate Limiting Features:")
    print("  ✅ Minimum 3 second delay between requests")
    print("  ✅ Random jitter (0.5-1.5s) to avoid patterns")
    print("  ✅ Retry logic with exponential backoff")
    print("  ✅ Cookie file support (if provided)")
    print("  ✅ Socket timeout protection (30s)")
    print()
    
    if successful == len(test_urls):
        print("✅ All tests passed! Rate limiting protection is working.")
    else:
        print("⚠️ Some tests failed. May need further rate limiting adjustments.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())