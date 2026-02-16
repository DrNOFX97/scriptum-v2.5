"""
Audio extraction endpoints for dual video+audio playback.

Extracts audio from MKV and converts to AAC (much faster than full conversion).
This enables dual-player setup: original video + converted audio played separately.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import uuid
import threading
import subprocess

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR

logger = setup_logger(__name__)


def create_audio_extraction_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create audio extraction blueprint with injected dependencies.

    This blueprint provides endpoints to extract audio from video files
    and convert it to browser-compatible AAC format.

    Args:
        services: Service container with all initialized services
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('audio_extraction', __name__)

    def _extract_audio_background(job_id: str, video_path: Path, output_path: Path):
        """Background task for audio extraction and conversion"""
        temp_ac3_path = None

        def update_progress(percentage: int, message: str, stage: str):
            """Helper to update job progress"""
            services.job_storage_service.update_job(job_id, {
                'progress': {
                    'percentage': percentage,
                    'message': message,
                    'stage': stage
                }
            })
            logger.debug(f"Job {job_id}: {stage} - {percentage}% - {message}")

        try:
            # Step 1: Extract AC3/DTS audio stream (fast - just copy)
            update_progress(10, 'Extraindo stream de áudio...', 'extracting')

            temp_ac3_path = output_path.parent / f"{output_path.stem}_temp.ac3"

            logger.info(f"Job {job_id}: Extracting audio to {temp_ac3_path}")

            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-vn',  # No video
                '-c:a', 'copy',  # Copy audio codec (fast!)
                str(temp_ac3_path)
            ], capture_output=True, text=True, check=True)

            if not temp_ac3_path.exists() or temp_ac3_path.stat().st_size == 0:
                raise Exception("Audio extraction failed - no output file")

            logger.info(f"Job {job_id}: Audio extracted ({temp_ac3_path.stat().st_size / (1024*1024):.1f}MB)")

            # Step 2: Convert to AAC
            update_progress(50, 'Convertendo AC3 → AAC...', 'converting')

            logger.info(f"Job {job_id}: Converting to AAC: {output_path}")

            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', str(temp_ac3_path),
                '-c:a', 'aac',
                '-b:a', '192k',  # Good quality for movies
                str(output_path)
            ], capture_output=True, text=True, check=True)

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise Exception("AAC conversion failed - no output file")

            # Get output size
            output_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Job {job_id}: Conversion complete ({output_size_mb:.1f}MB)")

            # Clean up temp files
            if temp_ac3_path and temp_ac3_path.exists():
                temp_ac3_path.unlink()
            if video_path.exists():
                video_path.unlink()

            # Mark as completed
            services.job_storage_service.update_job(job_id, {
                'status': 'completed',
                'output_file': str(output_path),
                'output_size_mb': round(output_size_mb, 2),
                'progress': {
                    'percentage': 100,
                    'message': 'Conversão concluída!',
                    'stage': 'completed'
                }
            })

            logger.info(f"Job {job_id}: Audio extraction completed successfully")

        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg error: {e.stderr}"
            logger.error(f"Job {job_id}: {error_msg}")

            services.job_storage_service.update_job(job_id, {
                'status': 'error',
                'error': error_msg,
                'progress': {
                    'percentage': 0,
                    'message': f'Erro: {str(e)}',
                    'stage': 'error'
                }
            })

            # Clean up on error
            if temp_ac3_path and temp_ac3_path.exists():
                temp_ac3_path.unlink()
            if video_path.exists():
                video_path.unlink()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job {job_id}: Unexpected error - {error_msg}", exc_info=True)

            services.job_storage_service.update_job(job_id, {
                'status': 'error',
                'error': error_msg,
                'progress': {
                    'percentage': 0,
                    'message': f'Erro: {error_msg}',
                    'stage': 'error'
                }
            })

            # Clean up on error
            if temp_ac3_path and temp_ac3_path.exists():
                temp_ac3_path.unlink()
            if video_path.exists():
                video_path.unlink()

    @bp.route('/extract-convert-audio', methods=['POST'])
    def extract_convert_audio():
        """
        Extract audio from video and convert to AAC.
        Much faster than full video conversion (only processes audio).

        Request: multipart/form-data
            - video: video file (MKV with AC3/DTS)

        Response: JSON with job_id
        """
        if 'video' not in request.files:
            logger.warning("extract-convert-audio: Missing video file in request")
            return jsonify({'success': False, 'error': 'Missing video file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']

        logger.info(f"Starting audio extraction job: {video_file.filename}")

        # Create unique job ID
        job_id = f"audio_extract_{uuid.uuid4()}"

        # Create persistent temp directory for this job
        job_folder = config.TEMP_DIR / f'audio_extract_{job_id}'
        job_folder.mkdir(parents=True, exist_ok=True)

        # Save video temporarily
        video_path = job_folder / video_file.filename
        video_file.save(str(video_path))

        # Output will be AAC audio file
        output_path = job_folder / f"audio_{job_id}.aac"

        # Get file size for estimation
        file_size_gb = video_path.stat().st_size / (1024 ** 3)
        # Audio extraction is MUCH faster - roughly 30 seconds per GB
        estimated_minutes = max(2, int(file_size_gb * 0.5))

        logger.info(f"Job {job_id}: File size {file_size_gb:.2f}GB, estimated time {estimated_minutes} minutes")

        # Initialize job status in Firestore
        job_data = {
            'status': 'pending',
            'filename': video_file.filename,
            'output_filename': f"audio_{job_id}.aac",
            'file_size_gb': round(file_size_gb, 2),
            'estimated_time': f"{estimated_minutes} minutos",
            'progress': {
                'percentage': 0,
                'message': 'Aguardando processamento...',
                'stage': 'pending'
            }
        }
        services.job_storage_service.create_job(job_id, job_data)

        # Start extraction in background thread
        thread = threading.Thread(
            target=_extract_audio_background,
            args=(job_id, video_path, output_path)
        )
        thread.daemon = True
        thread.start()

        logger.info(f"Job {job_id}: Background extraction started")

        return jsonify({
            'success': True,
            'job_id': job_id,
            'file_size_gb': round(file_size_gb, 2),
            'estimated_time': f"{estimated_minutes} minutos"
        })

    @bp.route('/extract-audio-status/<job_id>', methods=['GET'])
    def get_extraction_status(job_id: str):
        """
        Get audio extraction job status.

        Returns: JSON with current progress
        """
        job = services.job_storage_service.get_job(job_id)

        if not job:
            logger.warning(f"Status check for non-existent job: {job_id}")
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        response = {
            'success': True,
            'job_id': job_id,
            'status': job['status'],
            'filename': job.get('filename'),
            'output_filename': job.get('output_filename'),
            'file_size_gb': job.get('file_size_gb'),
            'estimated_time': job.get('estimated_time'),
            'progress': job.get('progress', {})
        }

        if job['status'] == 'completed':
            response['output_size_mb'] = job.get('output_size_mb')

        if job['status'] == 'error':
            response['error'] = job.get('error', 'Unknown error')

        return jsonify(response)

    @bp.route('/extract-audio-download/<job_id>', methods=['GET'])
    def download_extracted_audio(job_id: str):
        """
        Download extracted AAC audio file.

        Returns: AAC audio file
        """
        job = services.job_storage_service.get_job(job_id)

        if not job:
            logger.warning(f"Download attempt for non-existent job: {job_id}")
            return jsonify({'error': 'Job not found'}), 404

        if job['status'] != 'completed':
            return jsonify({'error': 'Extraction not yet complete'}), HTTP_BAD_REQUEST

        output_file = job.get('output_file')
        if not output_file or not Path(output_file).exists():
            logger.error(f"Job {job_id}: Output file not found at {output_file}")
            return jsonify({'error': 'Output file not found'}), 404

        logger.info(f"Job {job_id}: Downloading extracted audio: {job.get('output_filename')}")

        return send_file(
            output_file,
            mimetype='audio/aac',
            as_attachment=True,
            download_name=job.get('output_filename', 'audio.aac')
        )

    return bp
