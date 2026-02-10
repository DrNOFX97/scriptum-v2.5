"""
Video processing endpoints.

Handles video analysis, conversion, remuxing, and subtitle extraction.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import tempfile
import base64

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR

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

    @bp.route('/remux-mkv-to-mp4', methods=['POST'])
    def remux_mkv_to_mp4():
        """
        Remux MKV to MP4 (instant, no re-encoding)

        Request: multipart/form-data
            - video: MKV file

        Response: Binary (MP4 file)
        """
        if 'video' not in request.files:
            logger.warning("remux_mkv_to_mp4: Missing video file in request")
            return jsonify({'error': 'Missing video file'}), HTTP_BAD_REQUEST

        video_file = request.files['video']

        if not video_file.filename.lower().endswith('.mkv'):
            logger.warning(f"remux_mkv_to_mp4: Invalid file type: {video_file.filename}")
            return jsonify({'error': 'Only MKV files supported'}), HTTP_BAD_REQUEST

        logger.info(f"Remuxing MKV to MP4: {video_file.filename}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_path = tmp / video_file.filename
            output_path = tmp / video_file.filename.replace('.mkv', '.mp4')

            video_file.save(str(input_path))
            logger.debug(f"Video saved to: {input_path}")

            try:
                # Check if remux is possible
                if not services.video_service.can_remux_to_mp4(input_path):
                    logger.error(f"Video codec not compatible for fast remux: {video_file.filename}")
                    return jsonify({
                        'error': 'Video codec not compatible for fast remux. Use /convert-to-mp4 instead.'
                    }), HTTP_BAD_REQUEST

                # Remux using service
                success = services.video_service.remux_to_mp4(input_path, output_path)

                if not success:
                    logger.error(f"Remux operation failed: {video_file.filename}")
                    return jsonify({'error': 'Remux failed'}), HTTP_INTERNAL_ERROR

                logger.info(f"Remux successful: {output_path.name}")

                return send_file(
                    str(output_path),
                    mimetype='video/mp4',
                    as_attachment=True,
                    download_name=output_path.name
                )

            except Exception as e:
                logger.error(f"Remux error: {e}", exc_info=True)
                return jsonify({'error': f'Remux failed: {str(e)}'}), HTTP_INTERNAL_ERROR

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
