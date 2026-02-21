"""
Video processing endpoints.

Handles video analysis, conversion, remuxing, and subtitle extraction.
"""

from flask import Blueprint, request, jsonify, send_file, Response
from pathlib import Path
import tempfile
import base64
import uuid
import threading
import subprocess
from google.cloud import storage as gcs_storage

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR

GCS_BUCKET = "scriptum-uploads"
GCS_REMUX_PREFIX = "remuxed"

logger = setup_logger(__name__)


def create_video_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create video processing blueprint with injected dependencies.

    Args:
        services: Service container with all initialized services
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('video', __name__)

    @bp.route('/analyze-video', methods=['POST'])
    def analyze_video():
        """
        Analyze video file and return comprehensive metadata

        Request: multipart/form-data
            - video: video file

        Response: JSON
            - success: bool
            - filename: str
            - video_info: dict (format, size, resolution, duration, codec, fps)
            - can_convert_to_mp4: bool
            - can_remux_to_mp4: bool
        """
        if 'video' not in request.files:
            logger.warning("analyze_video: Missing video file in request")
            return jsonify({'error': 'Missing video file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']
        logger.info(f"Analyzing video: {video_file.filename}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            video_path = tmp / video_file.filename
            video_file.save(str(video_path))

            logger.debug(f"Video saved to temporary path: {video_path}")

            try:
                # Get video info using service
                video_info = services.video_service.get_video_info(video_path)

                # Check conversion capabilities
                can_convert = services.video_service.can_convert_to_mp4(video_path)
                can_remux = services.video_service.can_remux_to_mp4(video_path)

                logger.info(
                    f"Analysis complete - Format: {video_info.get('format')}, "
                    f"Resolution: {video_info.get('resolution')}, "
                    f"Duration: {video_info.get('duration_formatted')}, "
                    f"Can remux: {can_remux}"
                )

                return jsonify({
                    'success': True,
                    'filename': video_file.filename,
                    'video_info': video_info,
                    'can_convert_to_mp4': can_convert,
                    'can_remux_to_mp4': can_remux
                })

            except Exception as e:
                logger.error(f"Video analysis failed: {e}", exc_info=True)
                return jsonify({'error': f'Analysis failed: {str(e)}'}), HTTP_INTERNAL_ERROR

    def _remux_background(job_id: str, gcs_input_path: str, filename: str):
        """Background remux: download from GCS → ffmpeg stream copy → upload output to GCS"""
        output_path = None
        input_path = None
        try:
            services.job_storage_service.update_job(job_id, {
                'status': 'processing',
                'progress': {'percentage': 10, 'message': 'A descarregar ficheiro...', 'stage': 'downloading'}
            })

            gcs_client = gcs_storage.Client()
            gcs_path = gcs_input_path[5:]  # strip gs://
            bucket_name, object_name = gcs_path.split('/', 1)
            bucket = gcs_client.bucket(bucket_name)
            input_blob = bucket.blob(object_name)

            # Download input to temp
            input_path = Path(config.TEMP_DIR) / f"remux_in_{job_id}_{filename}"
            logger.info(f"Job {job_id}: Downloading {gcs_input_path} to {input_path}")
            input_blob.download_to_filename(str(input_path))
            logger.info(f"Job {job_id}: Download complete ({input_path.stat().st_size / (1024**3):.2f} GB)")

            services.job_storage_service.update_job(job_id, {
                'progress': {'percentage': 40, 'message': 'A remuxar para MP4...', 'stage': 'remuxing'}
            })

            output_filename = filename.rsplit('.', 1)[0] + '.mp4'
            output_path = Path(config.TEMP_DIR) / f"remux_out_{job_id}_{output_filename}"

            # Remux: stream copy MKV → MP4 (no re-encoding)
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', str(input_path),
                '-c', 'copy',
                '-movflags', 'faststart',
                str(output_path)
            ], capture_output=True, text=True, timeout=3600)

            # Clean up input immediately after remux
            if input_path.exists():
                input_path.unlink()
                input_path = None

            if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
                raise Exception(f"ffmpeg failed: {result.stderr[-500:]}")

            output_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Job {job_id}: Remux complete ({output_size_mb:.1f} MB)")

            services.job_storage_service.update_job(job_id, {
                'progress': {'percentage': 80, 'message': 'A guardar resultado...', 'stage': 'uploading'}
            })

            # Upload output to GCS
            output_gcs_name = f"{GCS_REMUX_PREFIX}/{job_id}/{output_filename}"
            output_blob = bucket.blob(output_gcs_name)
            output_blob.upload_from_filename(str(output_path), content_type='video/mp4')
            logger.info(f"Job {job_id}: Uploaded to gs://{bucket_name}/{output_gcs_name}")

            # Clean up local output
            if output_path.exists():
                output_path.unlink()
                output_path = None

            # Delete GCS input
            try:
                input_blob.delete()
            except Exception:
                pass

            services.job_storage_service.update_job(job_id, {
                'status': 'completed',
                'output_filename': output_filename,
                'output_size_mb': round(output_size_mb, 2),
                'gcs_path': f"gs://{bucket_name}/{output_gcs_name}",
                'progress': {'percentage': 100, 'message': 'Remux concluído!', 'stage': 'completed'}
            })
            logger.info(f"Job {job_id}: Completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id}: Remux failed - {e}", exc_info=True)
            services.job_storage_service.update_job(job_id, {
                'status': 'error',
                'error': str(e),
                'progress': {'percentage': 0, 'message': f'Erro: {str(e)}', 'stage': 'error'}
            })
            if input_path and input_path.exists():
                input_path.unlink()
            if output_path and output_path.exists():
                output_path.unlink()

    @bp.route('/remux-mkv-to-mp4', methods=['POST'])
    def remux_mkv_to_mp4():
        """
        Remux MKV to MP4 (stream copy, no re-encoding).

        Accepts JSON: {file_path: "gs://...", filename: "video.mkv"}
        Returns: {success, job_id}
        """
        if not request.is_json:
            return jsonify({'error': 'Send JSON with file_path and filename'}), HTTP_BAD_REQUEST

        data = request.json
        gcs_path = data.get('file_path')
        filename = data.get('filename', 'video.mkv')

        if not gcs_path:
            return jsonify({'error': 'Missing file_path'}), HTTP_BAD_REQUEST

        job_id = f"remux_{uuid.uuid4()}"
        job_data = {
            'status': 'pending',
            'filename': filename,
            'progress': {'percentage': 0, 'message': 'A aguardar...', 'stage': 'pending'}
        }
        services.job_storage_service.create_job(job_id, job_data)

        thread = threading.Thread(target=_remux_background, args=(job_id, gcs_path, filename))
        thread.daemon = True
        thread.start()

        logger.info(f"Job {job_id}: Remux started for {filename}")
        return jsonify({'success': True, 'job_id': job_id})

    @bp.route('/remux-status/<job_id>', methods=['GET'])
    def remux_status(job_id: str):
        """Get remux job status."""
        job = services.job_storage_service.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        response = {
            'success': True,
            'job_id': job_id,
            'status': job['status'],
            'progress': job.get('progress', {}),
            'output_filename': job.get('output_filename'),
            'output_size_mb': job.get('output_size_mb'),
        }
        if job['status'] == 'error':
            response['error'] = job.get('error', 'Unknown error')
        return jsonify(response)

    @bp.route('/remux-download/<job_id>', methods=['GET'])
    def remux_download(job_id: str):
        """Stream remuxed MP4 from GCS to client."""
        job = services.job_storage_service.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        if job['status'] != 'completed':
            return jsonify({'error': 'Remux not complete'}), HTTP_BAD_REQUEST

        gcs_path = job.get('gcs_path')
        if not gcs_path:
            return jsonify({'error': 'Output not found'}), 404

        gcs_path_stripped = gcs_path[5:]
        bucket_name, object_name = gcs_path_stripped.split('/', 1)
        gcs_client = gcs_storage.Client()
        blob = gcs_client.bucket(bucket_name).blob(object_name)
        output_filename = job.get('output_filename', 'video.mp4')

        def stream_blob():
            with blob.open('rb') as f:
                while True:
                    chunk = f.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    yield chunk

        return Response(
            stream_blob(),
            mimetype='video/mp4',
            headers={'Content-Disposition': f'attachment; filename="{output_filename}"'}
        )

    @bp.route('/convert-to-mp4', methods=['POST'])
    def convert_to_mp4():
        """
        Convert video to MP4 with re-encoding

        Request: multipart/form-data
            - video: video file
            - quality: str (fast, balanced, high) - optional, default: balanced

        Response: Binary (MP4 file)
        """
        if 'video' not in request.files:
            logger.warning("convert_to_mp4: Missing video file in request")
            return jsonify({'error': 'Missing video file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']
        quality = request.form.get('quality', 'balanced')

        if quality not in ['fast', 'balanced', 'high']:
            logger.warning(f"convert_to_mp4: Invalid quality parameter: {quality}")
            return jsonify({'error': 'Invalid quality. Use: fast, balanced, or high'}), HTTP_BAD_REQUEST

        logger.info(f"Converting to MP4: {video_file.filename} (quality: {quality})")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / video_file.filename
            output_path = tmp / f"{Path(video_file.filename).stem}.mp4"

            video_file.save(str(input_path))
            logger.debug(f"Video saved to: {input_path}")

            try:
                # Convert using service
                success = services.video_service.convert_to_mp4(input_path, output_path, quality)

                if not success:
                    logger.error(f"Conversion failed: {video_file.filename}")
                    return jsonify({'error': 'Conversion failed'}), HTTP_INTERNAL_ERROR

                logger.info(f"Conversion successful: {output_path.name}")

                return send_file(
                    str(output_path),
                    mimetype='video/mp4',
                    as_attachment=True,
                    download_name=output_path.name
                )

            except Exception as e:
                logger.error(f"Conversion error: {e}", exc_info=True)
                return jsonify({'error': f'Conversion failed: {str(e)}'}), HTTP_INTERNAL_ERROR

    @bp.route('/extract-mkv-subtitles', methods=['POST'])
    def extract_mkv_subtitles():
        """
        Extract all subtitle tracks from MKV file

        Request: multipart/form-data
            - video: MKV file

        Response: JSON
            - success: bool
            - subtitles: list of subtitle info
        """
        if 'video' not in request.files:
            logger.warning("extract_mkv_subtitles: Missing video file in request")
            return jsonify({'error': 'Missing video file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']

        if not video_file.filename.lower().endswith('.mkv'):
            logger.warning(f"extract_mkv_subtitles: Invalid file type: {video_file.filename}")
            return jsonify({'error': 'Only MKV files supported'}), HTTP_BAD_REQUEST

        logger.info(f"Extracting subtitles from MKV: {video_file.filename}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            video_path = tmp / video_file.filename
            video_file.save(str(video_path))

            logger.debug(f"Video saved to: {video_path}")

            try:
                # Extract using service
                subtitles = services.video_service.extract_mkv_subtitles(video_path, tmp)

                if not subtitles:
                    logger.warning(f"No subtitles found in MKV: {video_file.filename}")
                    return jsonify({
                        'success': False,
                        'message': 'No subtitles found in MKV'
                    })

                logger.info(f"Extracted {len(subtitles)} subtitle track(s)")

                # Read subtitle files and encode as base64 for JSON response
                for sub in subtitles:
                    with open(sub['file_path'], 'rb') as f:
                        content_bytes = f.read()
                        sub['content_base64'] = base64.b64encode(content_bytes).decode('utf-8')

                        # Try to decode as text for frontend usage
                        try:
                            sub['content'] = content_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            # Try latin-1 fallback or just leave empty for binary formats
                            try:
                                sub['content'] = content_bytes.decode('latin-1')
                            except:
                                sub['content'] = ""
                                logger.debug(f"Could not decode subtitle as text: {sub.get('title')}")

                    # Remove file_path from response (was temporary)
                    del sub['file_path']

                return jsonify({
                    'success': True,
                    'count': len(subtitles),
                    'subtitles': subtitles
                })

            except Exception as e:
                logger.error(f"Subtitle extraction failed: {e}", exc_info=True)
                return jsonify({'error': f'Extraction failed: {str(e)}'}), HTTP_INTERNAL_ERROR

    @bp.route('/recognize-movie', methods=['POST'])
    def recognize_movie():
        """
        Recognize movie from filename or IMDB ID

        Request: JSON
            - filename: str (video filename)
            - imdb_id: str (optional IMDB ID for direct lookup)

        Response: JSON
            - success: bool
            - movie: dict (title, year, rating, poster, overview)
        """
        data = request.get_json()

        if not data or 'filename' not in data:
            logger.warning("recognize_movie: Missing filename in request")
            return jsonify({'error': 'Missing filename'}), HTTP_BAD_REQUEST

        filename = data['filename']
        imdb_id = data.get('imdb_id')

        logger.info(f"Recognizing movie: {filename}" + (f" (IMDB ID: {imdb_id})" if imdb_id else ""))

        try:
            # Recognize movie using service
            movie = services.movie_service.recognize_from_filename(filename, imdb_id)

            if not movie:
                logger.warning(f"Movie not found: {filename}")
                return jsonify({
                    'success': False,
                    'error': 'Movie not found'
                }), 404

            logger.info(f"Movie recognized: {movie.get('title')} ({movie.get('year')})")

            return jsonify({
                'success': True,
                'movie': movie
            })

        except Exception as e:
            logger.error(f"Movie recognition failed: {e}", exc_info=True)
            return jsonify({'error': f'Recognition failed: {str(e)}'}), HTTP_INTERNAL_ERROR

    return bp
