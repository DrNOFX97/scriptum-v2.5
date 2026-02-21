"""
Audio conversion endpoints.

Handles audio conversion from browser-incompatible codecs (AC3, DTS) to AAC.
Uses server-side ffmpeg to handle large files that ffmpeg.wasm can't process.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import uuid
import threading

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR

logger = setup_logger(__name__)


def create_audio_conversion_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create audio conversion blueprint with injected dependencies.

    Args:
        services: Service container with all initialized services
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('audio_conversion', __name__)

    def _convert_background(job_id: str, input_path: Path, output_path: Path):
        """Background task for audio conversion"""
        def progress_update(progress_data):
            """Callback to update progress"""
            services.job_storage_service.update_job(job_id, {'progress': progress_data})
            logger.debug(f"Job {job_id}: {progress_data.get('message', 'Progress update')}")

        try:
            # Import here to avoid circular dependency
            from ..services.audio_conversion_service import AudioConversionService

            success = AudioConversionService.convert_audio_to_aac(
                input_path,
                output_path,
                progress_callback=progress_update
            )

            if success:
                # Get output file size
                output_size_mb = output_path.stat().st_size / (1024 * 1024)

                services.job_storage_service.update_job(job_id, {
                    'status': 'completed',
                    'output_file': str(output_path),
                    'output_size_mb': round(output_size_mb, 2),
                    'progress': {
                        'status': 'completed',
                        'percentage': 100,
                        'message': 'Audio conversion completed!'
                    }
                })
                logger.info(f"Job {job_id}: Audio conversion completed ({output_size_mb:.1f}MB)")
            else:
                services.job_storage_service.update_job(job_id, {
                    'status': 'error',
                    'error': 'Audio conversion failed',
                    'progress': {
                        'status': 'error',
                        'percentage': 0,
                        'message': 'Conversion failed'
                    }
                })
                logger.error(f"Job {job_id}: Audio conversion failed")

        except Exception as e:
            services.job_storage_service.update_job(job_id, {
                'status': 'error',
                'error': str(e),
                'progress': {
                    'status': 'error',
                    'percentage': 0,
                    'message': f'Error: {str(e)}'
                }
            })
            logger.error(f"Job {job_id}: Error - {e}", exc_info=True)

    @bp.route('/detect-audio-codec', methods=['POST'])
    def detect_audio_codec():
        """
        Detect audio codec from video file (quick check, no conversion)

        Request: multipart/form-data
            - video: video file

        Response: JSON with audio codec info
        """
        if 'video' not in request.files:
            logger.warning("detect-audio-codec: Missing video file in request")
            return jsonify({'success': False, 'error': 'Missing video file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']
        logger.info(f"Detecting audio codec: {video_file.filename}")

        # Create temporary file
        temp_dir = config.TEMP_DIR / f'audio_detect_{uuid.uuid4()}'
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            video_path = temp_dir / video_file.filename
            video_file.save(str(video_path))

            # Detect audio codec
            from ..services.audio_conversion_service import AudioConversionService
            audio_info = AudioConversionService.detect_audio_codec(video_path)

            if not audio_info:
                return jsonify({
                    'success': True,
                    'has_audio': False,
                    'message': 'No audio stream found'
                })

            # Get file size for estimation
            file_size_gb = AudioConversionService.get_video_file_size(video_path)
            estimated_time = AudioConversionService.estimate_conversion_time(file_size_gb)

            return jsonify({
                'success': True,
                'has_audio': True,
                'audio_info': audio_info,
                'file_size_gb': file_size_gb,
                'estimated_conversion_time': estimated_time,
                'needs_conversion': not audio_info['is_compatible']
            })

        except Exception as e:
            logger.error(f"Audio codec detection error: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Detection failed: {str(e)}'
            }), HTTP_INTERNAL_ERROR

        finally:
            # Cleanup temp directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass

    @bp.route('/convert-audio-mkv', methods=['POST'])
    def convert_audio_mkv():
        """
        Start audio conversion job (AC3/DTS → AAC)

        Request: multipart/form-data
            - video: video file (MKV, MP4, etc.)

        Response: JSON with job_id for status polling
        """
        if 'video' not in request.files:
            logger.warning("convert-audio-mkv: Missing video file in request")
            return jsonify({'success': False, 'error': 'Missing video file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']

        logger.info(f"Starting audio conversion job: {video_file.filename}")

        # Create unique job ID
        job_id = str(uuid.uuid4())

        # Create persistent temp directory for this job
        job_folder = config.TEMP_DIR / f'audio_conversion_{job_id}'
        job_folder.mkdir(parents=True, exist_ok=True)

        input_path = job_folder / video_file.filename
        output_filename = video_file.filename.replace('.mkv', '.web.mkv').replace('.mp4', '.web.mp4')
        output_path = job_folder / output_filename

        # Save uploaded file
        video_file.save(str(input_path))

        # Get file size
        from ..services.audio_conversion_service import AudioConversionService
        file_size_gb = AudioConversionService.get_video_file_size(input_path)
        estimated_time = AudioConversionService.estimate_conversion_time(file_size_gb)

        # Initialize job status in Firestore
        job_data = {
            'status': 'starting',
            'filename': video_file.filename,
            'output_filename': output_filename,
            'file_size_gb': file_size_gb,
            'estimated_time': estimated_time,
            'progress': {
                'status': 'starting',
                'percentage': 0,
                'message': 'Initializing audio conversion...'
            }
        }
        services.job_storage_service.create_job(job_id, job_data)

        # Start conversion in background thread
        thread = threading.Thread(
            target=_convert_background,
            args=(job_id, input_path, output_path)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'file_size_gb': file_size_gb,
            'estimated_time': estimated_time,
            'message': 'Audio conversion job started'
        })

    @bp.route('/convert-audio-status/<job_id>', methods=['GET'])
    def get_conversion_status(job_id: str):
        """
        Get audio conversion job status

        Returns: JSON with current progress
        """
        job = services.job_storage_service.get_job(job_id)

        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        response = {
            'success': True,
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

    @bp.route('/convert-audio-download/<job_id>', methods=['GET'])
    def download_converted_audio(job_id: str):
        """
        Download completed audio-converted video

        Returns: Video file with AAC audio
        """
        job = services.job_storage_service.get_job(job_id)

        if not job:
            return jsonify({'error': 'Job not found'}), 404

        if job['status'] != 'completed':
            return jsonify({'error': 'Conversion not yet complete'}), HTTP_BAD_REQUEST

        output_file = job.get('output_file')
        if not output_file or not Path(output_file).exists():
            return jsonify({'error': 'Output file not found'}), 404

        logger.info(f"Job {job_id}: Downloading converted file: {job.get('output_filename')}")

        # Clean up job after download (optional - can keep for retry)
        # services.job_storage_service.delete_job(job_id)

        return send_file(
            output_file,
            mimetype='video/x-matroska',
            as_attachment=True,
            download_name=job.get('output_filename', 'converted.mkv')
        )

    @bp.route('/convert-audio-cancel/<job_id>', methods=['POST'])
    def cancel_conversion(job_id: str):
        """
        Cancel ongoing audio conversion job

        NOTE: This marks the job as cancelled in Firestore, but doesn't
        actually kill the ffmpeg process (that would require process management).
        The background thread will complete, but the job will be marked as cancelled.
        """
        job = services.job_storage_service.get_job(job_id)

        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        if job['status'] in ['completed', 'error']:
            return jsonify({
                'success': False,
                'error': f'Cannot cancel job in {job["status"]} state'
            }), HTTP_BAD_REQUEST

        # Mark as cancelled
        services.job_storage_service.update_job(job_id, {
            'status': 'cancelled',
            'progress': {
                'status': 'cancelled',
                'percentage': 0,
                'message': 'Conversion cancelled by user'
            }
        })

        logger.info(f"Job {job_id}: Cancelled by user")

        return jsonify({
            'success': True,
            'message': 'Conversion job cancelled'
        })

    return bp
