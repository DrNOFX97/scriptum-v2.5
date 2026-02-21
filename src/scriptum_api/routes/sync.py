"""
Subtitle synchronization endpoints.

Handles subtitle synchronization with video using MLX Whisper.
"""

from flask import Blueprint, request, jsonify
from pathlib import Path
import tempfile
import time

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR

logger = setup_logger(__name__)

# Upload folder for temp files
UPLOAD_FOLDER = Path(__file__).parent.parent.parent.parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)


def create_sync_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create subtitle synchronization blueprint with injected dependencies.

    Args:
        services: Service container with all initialized services
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('sync', __name__)

    @bp.route('/sync', methods=['POST'])
    def sync_subtitles():
        """
        Synchronize subtitles with video using MLX Whisper
        Returns JSON with status and download path instead of direct file

        Request: multipart/form-data
            Option 1 (traditional):
                - video: video file
                - subtitle: SRT file
            Option 2 (after parallel upload):
                - video_path: GCS path (string)
                - subtitle: SRT file

        Response: JSON with result
        """
        # Check for subtitle file (required in both modes)
        if 'subtitle' not in request.files:
            logger.warning("sync: Missing subtitle file in request")
            return jsonify({'error': 'Missing subtitle file'}), HTTP_BAD_REQUEST

        subtitle_file = request.files['subtitle']

        if not subtitle_file.filename.endswith('.srt'):
            logger.warning(f"sync: Invalid subtitle format: {subtitle_file.filename}")
            return jsonify({'error': 'Subtitle must be .srt format'}), HTTP_BAD_REQUEST

        # Check for video: either file or GCS path
        video_gcs_path = request.form.get('video_path')  # GCS path from parallel upload
        has_video_file = 'video' in request.files

        if not video_gcs_path and not has_video_file:
            logger.warning("sync: Missing video file or video_path in request")
            return jsonify({'error': 'Missing video file or video_path'}), HTTP_BAD_REQUEST

        timestamp = int(time.time())

        # Handle video source
        if video_gcs_path:
            # Video already uploaded to GCS via parallel upload
            logger.info(f"Using pre-uploaded video from GCS: {video_gcs_path}")

            # Download from GCS to temp location
            from google.cloud import storage as gcs_storage
            gcs_client = gcs_storage.Client()

            # Parse gs://bucket/path
            gcs_path = video_gcs_path[5:]  # strip gs://
            bucket_name, *object_parts = gcs_path.split('/', 1)
            object_name = object_parts[0] if object_parts else ''

            bucket_ref = gcs_client.bucket(bucket_name)
            blob = bucket_ref.blob(object_name)

            # Download to temp location
            video_filename = object_name.split('/')[-1]
            video_path = UPLOAD_FOLDER / f"sync_video_{timestamp}_{video_filename}"
            logger.info(f"Downloading video from GCS to {video_path}...")
            blob.download_to_filename(str(video_path))
            logger.info(f"Video downloaded ({video_path.stat().st_size:,} bytes)")
        else:
            # Traditional file upload
            video_file = request.files['video']
            video_filename = video_file.filename
            video_path = UPLOAD_FOLDER / f"sync_video_{timestamp}_{video_filename}"
            video_file.save(str(video_path))
            logger.info(f"Video file saved from upload: {video_filename}")

        # Save subtitle file
        subtitle_path = UPLOAD_FOLDER / f"sync_sub_{timestamp}_{subtitle_file.filename}"
        output_filename = f'synced_{timestamp}_{subtitle_file.filename}'
        output_path = UPLOAD_FOLDER / output_filename

        # Create log file for progress
        log_filename = f'sync_log_{timestamp}.txt'
        log_path = UPLOAD_FOLDER / log_filename

        logger.info(
            f"Starting sync process - Video: {video_path.name}, "
            f"Subtitle: {subtitle_file.filename}"
        )

        try:
            subtitle_file.save(str(subtitle_path))

            logger.debug(
                f"Files saved - Video: {video_path}, "
                f"Subtitle: {subtitle_path}, Log: {log_path}"
            )

            # Create temp directory for processing
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)

                # Sync using service with logging
                # Pass GCS path if available for AAC caching
                result = services.sync_service.sync_subtitles_with_log(
                    video_path,
                    subtitle_path,
                    output_path,
                    tmpdir_path,
                    log_path,
                    gcs_video_path=video_gcs_path
                )

            # Clean up temp files
            try:
                video_path.unlink()
                subtitle_path.unlink()
                logger.debug("Temporary files cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp files: {cleanup_error}")

            if not result['success']:
                logger.error(f"Sync failed: {result.get('error', 'Unknown error')}")
                return jsonify(result), HTTP_INTERNAL_ERROR

            logger.info(
                f"Sync successful - Offset: {result.get('offset_detected')}, "
                f"Output: {output_filename}"
            )

            return jsonify({
                'success': True,
                'synced_file': output_filename,
                'log_file': log_filename,
                'offset_detected': result.get('offset_detected'),
                'stats': result.get('stats')
            })

        except Exception as e:
            logger.error(f"Sync error: {e}", exc_info=True)

            # Cleanup on error
            try:
                video_path.unlink(missing_ok=True)
                subtitle_path.unlink(missing_ok=True)
            except:
                pass

            return jsonify({
                'success': False,
                'error': str(e)
            }), HTTP_INTERNAL_ERROR

    return bp
