"""
Video processing service
Handles video analysis, conversion, and remuxing operations
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional


class VideoService:
    """Service for video processing operations"""

    @staticmethod
    def get_video_info(video_path: Path) -> Dict[str, Any]:
        """
        Extract comprehensive video metadata using ffprobe

        Args:
            video_path: Path to video file

        Returns:
            Dictionary containing video metadata
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ], capture_output=True, text=True, check=True)

            data = json.loads(result.stdout)
            format_info = data.get('format', {})
            video_stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                {}
            )

            # Extract key information
            duration = float(format_info.get('duration', 0))
            size_mb = float(format_info.get('size', 0)) / (1024 * 1024)

            width = video_stream.get('width', 0)
            height = video_stream.get('height', 0)
            codec = video_stream.get('codec_name', 'unknown')

            # Calculate FPS
            fps_str = video_stream.get('r_frame_rate', '0/1')
            try:
                num, den = map(int, fps_str.split('/'))
                fps = num / den if den != 0 else 0
            except:
                fps = 0

            # Format duration
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            if hours > 0:
                duration_formatted = f"{hours}h {minutes}m"
            else:
                duration_formatted = f"{minutes}m"

            return {
                'format': format_info.get('format_name', '').upper().split(',')[0],
                'size_mb': round(size_mb, 2),
                'resolution': f"{width}x{height}" if width and height else 'unknown',
                'duration': duration,
                'duration_formatted': duration_formatted,
                'codec': codec,
                'fps': round(fps, 3),
                'width': width,
                'height': height
            }

        except Exception as e:
            print(f"❌ Error extracting video info: {e}")
            return {}

    @staticmethod
    def can_convert_to_mp4(video_path: Path) -> bool:
        """
        Check if video format can be converted to MP4

        Args:
            video_path: Path to video file

        Returns:
            True if conversion is supported
        """
        supported_formats = ['.mkv', '.avi', '.webm', '.flv', '.wmv']
        return video_path.suffix.lower() in supported_formats

    @staticmethod
    def can_remux_to_mp4(video_path: Path) -> bool:
        """
        Check if video can be remuxed (fast copy) to MP4
        Requires H.264/H.265 video and AAC audio

        Args:
            video_path: Path to video file

        Returns:
            True if remuxing is possible
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                str(video_path)
            ], capture_output=True, text=True, check=True)

            data = json.loads(result.stdout)

            video_stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                None
            )
            audio_stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'audio'),
                None
            )

            if not video_stream:
                return False

            # Check video codec
            video_codec = video_stream.get('codec_name', '').lower()
            video_compatible = video_codec in ['h264', 'hevc', 'h265']

            # Check audio codec (if present)
            if audio_stream:
                audio_codec = audio_stream.get('codec_name', '').lower()
                audio_compatible = audio_codec in ['aac', 'mp3']
            else:
                audio_compatible = True  # No audio is fine

            return video_compatible and audio_compatible

        except Exception as e:
            print(f"❌ Error checking remux compatibility: {e}")
            return False

    @staticmethod
    def remux_to_mp4(input_path: Path, output_path: Path) -> bool:
        """
        Remux video to MP4 (fast, no re-encoding)

        Args:
            input_path: Input video file
            output_path: Output MP4 file

        Returns:
            True if successful
        """
        try:
            print(f"⚡ Remuxing {input_path.name} to MP4...")

            subprocess.run([
                'ffmpeg', '-y',
                '-i', str(input_path),
                '-c', 'copy',  # Copy streams without re-encoding
                '-movflags', '+faststart',  # Optimize for web streaming
                str(output_path)
            ], check=True, capture_output=True)

            print(f"✅ Remux complete: {output_path.name}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Remux failed: {e.stderr.decode()}")
            return False

    @staticmethod
    def convert_to_mp4(input_path: Path, output_path: Path, quality: str = 'balanced') -> bool:
        """
        Convert video to MP4 with re-encoding

        Args:
            input_path: Input video file
            output_path: Output MP4 file
            quality: Conversion quality (fast, balanced, high)

        Returns:
            True if successful
        """
        # Quality presets
        presets = {
            'fast': {'crf': '28', 'preset': 'veryfast'},
            'balanced': {'crf': '23', 'preset': 'medium'},
            'high': {'crf': '18', 'preset': 'slow'}
        }

        settings = presets.get(quality, presets['balanced'])

        try:
            print(f"🎬 Converting {input_path.name} to MP4 (quality: {quality})...")

            subprocess.run([
                'ffmpeg', '-y',
                '-i', str(input_path),
                '-c:v', 'libx264',
                '-crf', settings['crf'],
                '-preset', settings['preset'],
                '-c:a', 'aac',
                '-b:a', '192k',
                '-movflags', '+faststart',
                str(output_path)
            ], check=True, capture_output=True)

            print(f"✅ Conversion complete: {output_path.name}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Conversion failed: {e.stderr.decode()}")
            return False

    @staticmethod
    def extract_mkv_subtitles(video_path: Path, output_dir: Path) -> list:
        """
        Extract all subtitle tracks from MKV file

        Args:
            video_path: Path to MKV file
            output_dir: Directory to save extracted subtitles

        Returns:
            List of extracted subtitle info dictionaries
        """
        try:
            # Get subtitle tracks info
            result = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 's',
                str(video_path)
            ], capture_output=True, text=True, check=True)

            data = json.loads(result.stdout)
            subtitle_streams = data.get('streams', [])

            if not subtitle_streams:
                return []

            extracted = []

            for idx, stream in enumerate(subtitle_streams):
                stream_index = stream.get('index')
                codec = stream.get('codec_name', 'unknown')
                language = stream.get('tags', {}).get('language', 'unknown')
                title = stream.get('tags', {}).get('title', f'Track {idx + 1}')

                # Determine file extension based on codec
                ext = 'srt' if codec == 'subrip' else codec

                output_file = output_dir / f"subtitle_{idx}_{language}.{ext}"

                try:
                    # Extract subtitle
                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', str(video_path),
                        '-map', f'0:{stream_index}',
                        str(output_file)
                    ], check=True, capture_output=True)

                    extracted.append({
                        'index': idx,
                        'language': language,
                        'title': title,
                        'codec': codec,
                        'file_path': str(output_file),
                        'file_name': output_file.name
                    })

                except subprocess.CalledProcessError:
                    print(f"⚠️  Failed to extract subtitle track {idx}")
                    continue

            return extracted

        except Exception as e:
            print(f"❌ Error extracting MKV subtitles: {e}")
            return []
