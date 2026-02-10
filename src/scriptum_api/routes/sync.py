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
            - video: video file
            - subtitle: SRT file

        Response: JSON with result
        """
        if 'video' not in request.files or 'subtitle' not in request.files:
            logger.warning("sync: Missing video or subtitle file in request")
            return jsonify({'error': 'Missing video or subtitle file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']
        subtitle_file = request.files['subtitle']

        if not subtitle_file.filename.endswith('.srt'):
            logger.warning(f"sync: Invalid subtitle format: {subtitle_file.filename}")
            return jsonify({'error': 'Subtitle must be .srt format'}), HTTP_BAD_REQUEST

        logger.info(
            f"Starting sync process - Video: {video_file.filename}, "
            f"Subtitle: {subtitle_file.filename}"
        )

        # Save files to persistent location for download later
        timestamp = int(time.time())
        video_path = UPLOAD_FOLDER / f"sync_video_{timestamp}_{video_file.filename}"
        subtitle_path = UPLOAD_FOLDER / f"sync_sub_{timestamp}_{subtitle_file.filename}"
        output_filename = f'synced_{timestamp}_{subtitle_file.filename}'
        output_path = UPLOAD_FOLDER / output_filename

        # Create log file for progress
        log_filename = f'sync_log_{timestamp}.txt'
        log_path = UPLOAD_FOLDER / log_filename

        try:
            video_file.save(str(video_path))
            subtitle_file.save(str(subtitle_path))

            logger.debug(
                f"Files saved - Video: {video_path}, "
                f"Subtitle: {subtitle_path}, Log: {log_path}"
            )

            # Create temp directory for processing
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)

                # Sync using service with logging
                result = services.sync_service.sync_subtitles_with_log(
                    video_path,
                    subtitle_path,
                    output_path,
                    tmpdir_path,
                    log_path
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
