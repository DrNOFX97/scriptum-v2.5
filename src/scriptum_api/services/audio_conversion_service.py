"""
Audio conversion service for browser-incompatible audio codecs.

Converts AC3, DTS, and other incompatible audio codecs to AAC for browser playback.
Handles large files that ffmpeg.wasm can't process in the browser.
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AudioConversionService:
    """
    Service for audio conversion operations.

    Handles conversion of incompatible audio codecs (AC3, DTS, etc.) to AAC
    for browser compatibility. Uses server-side ffmpeg for better performance
    and no memory limits.
    """

    # Browser-compatible audio codecs
    COMPATIBLE_CODECS = ['aac', 'mp3', 'opus', 'vorbis']

    # Common incompatible codecs that need conversion
    INCOMPATIBLE_CODECS = ['ac3', 'dts', 'eac3', 'truehd', 'dca', 'pcm_s16le', 'pcm_s24le']

    @staticmethod
    def detect_audio_codec(video_path: Path) -> Optional[Dict[str, Any]]:
        """
        Detect audio codec from video file.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with audio stream info or None if no audio
        """
        try:
            logger.info(f"Detecting audio codec for: {video_path.name}")

            result = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a:0',  # First audio stream
                str(video_path)
            ], capture_output=True, text=True, check=True)

            data = json.loads(result.stdout)
            audio_streams = data.get('streams', [])

            if not audio_streams:
                logger.warning(f"No audio stream found in {video_path.name}")
                return None

            audio_stream = audio_streams[0]
            codec = audio_stream.get('codec_name', 'unknown').lower()
            channels = audio_stream.get('channels', 2)
            sample_rate = audio_stream.get('sample_rate', '48000')

            # Determine channel layout
            channel_layout = audio_stream.get('channel_layout', '')
            if not channel_layout:
                if channels == 1:
                    channel_layout = 'mono'
                elif channels == 2:
                    channel_layout = 'stereo'
                elif channels == 6:
                    channel_layout = '5.1'
                elif channels == 8:
                    channel_layout = '7.1'
                else:
                    channel_layout = f'{channels}ch'

            is_compatible = codec in AudioConversionService.COMPATIBLE_CODECS

            audio_info = {
                'index': audio_stream.get('index', 0),
                'codec': codec,
                'channels': channels,
                'channel_layout': channel_layout,
                'sample_rate': sample_rate,
                'is_compatible': is_compatible
            }

            logger.info(
                f"Audio detected: {codec.upper()} • {channel_layout} • {sample_rate}Hz • "
                f"{'Compatible' if is_compatible else 'Incompatible'}"
            )

            return audio_info

        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error detecting audio codec: {e}", exc_info=True)
            return None

    @staticmethod
    def convert_audio_to_aac(
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """
        Convert video audio from incompatible codec to AAC.

        Copies video stream as-is (no re-encoding), converts audio to AAC,
        and preserves subtitle streams.

        Args:
            input_path: Input video file (MKV, MP4, etc.)
            output_path: Output video file (same container format)
            progress_callback: Optional callback for progress updates

        Returns:
            True if conversion successful
        """
        try:
            logger.info(f"Starting audio conversion: {input_path.name} → AAC")

            if progress_callback:
                progress_callback({
                    'status': 'starting',
                    'percentage': 0,
                    'message': 'Initializing audio conversion...'
                })

            # Get video duration for progress calculation
            duration = AudioConversionService._get_video_duration(input_path)

            # Build ffmpeg command
            cmd = [
                'ffmpeg', '-y',
                '-i', str(input_path),
                '-c:v', 'copy',        # Copy video stream (no re-encoding)
                '-c:a', 'aac',         # Convert audio to AAC
                '-b:a', '192k',        # Audio bitrate 192 kbps
                '-c:s', 'copy',        # Copy subtitle streams
                '-map', '0',           # Map all streams from input
                str(output_path)
            ]

            if progress_callback:
                progress_callback({
                    'status': 'processing',
                    'percentage': 5,
                    'message': 'Converting audio AC3/DTS → AAC...'
                })

            # Run ffmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Monitor progress
            last_percentage = 5
            for line in process.stderr:
                if progress_callback and duration > 0:
                    # Parse ffmpeg progress (time=HH:MM:SS.MS)
                    if 'time=' in line:
                        try:
                            time_str = line.split('time=')[1].split()[0]
                            current_time = AudioConversionService._parse_time(time_str)
                            percentage = min(95, int((current_time / duration) * 100))

                            # Only update on significant changes
                            if percentage > last_percentage:
                                last_percentage = percentage
                                progress_callback({
                                    'status': 'processing',
                                    'percentage': percentage,
                                    'message': f'Converting audio: {percentage}%'
                                })
                        except:
                            pass

            return_code = process.wait()

            if return_code != 0:
                stderr = process.stderr.read() if process.stderr else ''
                logger.error(f"ffmpeg conversion failed: {stderr}")

                if progress_callback:
                    progress_callback({
                        'status': 'error',
                        'percentage': 0,
                        'message': 'Audio conversion failed'
                    })
                return False

            logger.info(f"Audio conversion complete: {output_path.name}")

            if progress_callback:
                progress_callback({
                    'status': 'completed',
                    'percentage': 100,
                    'message': 'Audio conversion completed!'
                })

            return True

        except Exception as e:
            logger.error(f"Error converting audio: {e}", exc_info=True)

            if progress_callback:
                progress_callback({
                    'status': 'error',
                    'percentage': 0,
                    'message': f'Conversion error: {str(e)}'
                })

            return False

    @staticmethod
    def _get_video_duration(video_path: Path) -> float:
        """
        Get video duration in seconds.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds, or 0 if unknown
        """
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(video_path)
            ], capture_output=True, text=True, check=True)

            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            return duration

        except Exception as e:
            logger.debug(f"Could not get video duration: {e}")
            return 0

    @staticmethod
    def _parse_time(time_str: str) -> float:
        """
        Parse ffmpeg time string (HH:MM:SS.MS) to seconds.

        Args:
            time_str: Time string from ffmpeg

        Returns:
            Time in seconds
        """
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            return 0
        except:
            return 0

    @staticmethod
    def get_video_file_size(video_path: Path) -> float:
        """
        Get video file size in GB.

        Args:
            video_path: Path to video file

        Returns:
            File size in GB
        """
        try:
            size_bytes = video_path.stat().st_size
            size_gb = size_bytes / (1024 * 1024 * 1024)
            return round(size_gb, 2)
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0

    @staticmethod
    def estimate_conversion_time(file_size_gb: float) -> str:
        """
        Estimate conversion time based on file size.

        Args:
            file_size_gb: File size in GB

        Returns:
            Estimated time string (e.g., "2-4 minutes")
        """
        # Rough estimate: ~1-2 minutes per GB on modern hardware
        min_minutes = max(1, int(file_size_gb * 1))
        max_minutes = max(2, int(file_size_gb * 2))

        if min_minutes < 60:
            return f"{min_minutes}-{max_minutes} minutes"
        else:
            min_hours = min_minutes / 60
            max_hours = max_minutes / 60
            return f"{min_hours:.1f}-{max_hours:.1f} hours"
