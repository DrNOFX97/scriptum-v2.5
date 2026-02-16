#!/usr/bin/env python3
"""
Test script for audio extraction endpoint.

Tests the new /extract-convert-audio endpoint locally.
"""

import requests
import time
import sys
from pathlib import Path


API_BASE = "http://localhost:5001"


def test_audio_extraction(video_path: str):
    """Test audio extraction workflow"""

    print("=" * 70)
    print("🎵 Testing Audio Extraction Endpoint")
    print("=" * 70)
    print()

    # Check if file exists
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Error: File not found: {video_path}")
        sys.exit(1)

    file_size_mb = video_file.stat().st_size / (1024 * 1024)
    print(f"📁 File: {video_file.name}")
    print(f"📊 Size: {file_size_mb:.1f}MB")
    print()

    # Step 1: Upload and start extraction
    print("📤 Step 1: Uploading and starting extraction...")

    with open(video_file, 'rb') as f:
        files = {'video': (video_file.name, f, 'video/x-matroska')}

        try:
            response = requests.post(
                f"{API_BASE}/extract-convert-audio",
                files=files
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            sys.exit(1)

    if not result.get('success'):
        print(f"❌ Extraction start failed: {result.get('error')}")
        sys.exit(1)

    job_id = result['job_id']
    estimated_time = result['estimated_time']

    print(f"✅ Job created: {job_id}")
    print(f"⏱️  Estimated time: {estimated_time}")
    print()

    # Step 2: Poll for completion
    print("📊 Step 2: Polling for completion...")
    print()

    last_percentage = -1

    while True:
        time.sleep(2)

        try:
            response = requests.get(f"{API_BASE}/extract-audio-status/{job_id}")
            response.raise_for_status()
            status = response.json()
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            sys.exit(1)

        current_status = status['status']
        progress = status.get('progress', {})
        percentage = progress.get('percentage', 0)
        message = progress.get('message', '')
        stage = progress.get('stage', '')

        # Only print if percentage changed
        if percentage != last_percentage:
            print(f"  {percentage:3d}% | {stage:12s} | {message}")
            last_percentage = percentage

        if current_status == 'completed':
            print()
            print(f"✅ Extraction completed!")
            print(f"📦 Output size: {status.get('output_size_mb', 0):.1f}MB")
            print(f"📁 Output filename: {status.get('output_filename')}")
            break

        elif current_status == 'error':
            print()
            print(f"❌ Extraction failed: {status.get('error')}")
            sys.exit(1)

    # Step 3: Download extracted audio
    print()
    print("📥 Step 3: Downloading extracted audio...")

    try:
        response = requests.get(
            f"{API_BASE}/extract-audio-download/{job_id}",
            stream=True
        )
        response.raise_for_status()

        # Save to file
        output_path = Path(__file__).parent / 'test_output' / status['output_filename']
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        actual_size_mb = output_path.stat().st_size / (1024 * 1024)

        print(f"✅ Audio downloaded: {output_path}")
        print(f"📊 Actual size: {actual_size_mb:.1f}MB")

    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

    print()
    print("=" * 70)
    print("🎉 Test completed successfully!")
    print("=" * 70)
    print()
    print(f"📁 Test output: {output_path}")
    print(f"🎵 You can now play this AAC file with any audio player")
    print()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_audio_extraction.py <video_file.mkv>")
        print()
        print("Example:")
        print("  python test_audio_extraction.py ~/Downloads/movie.mkv")
        sys.exit(1)

    video_path = sys.argv[1]
    test_audio_extraction(video_path)
