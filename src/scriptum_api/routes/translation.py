"""
Subtitle translation endpoints.

Handles subtitle translation using Google Gemini.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import tempfile
import uuid
import threading
from langdetect import detect, LangDetectException

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR

logger = setup_logger(__name__)


def detect_subtitle_language(subtitle_content: str) -> str:
    """
    Detect language from subtitle content.

    Args:
        subtitle_content: Raw SRT content

    Returns:
        Language code (e.g., 'en', 'pt', 'es', 'fr')
    """
    try:
        # Extract text from SRT (remove timestamps and numbers)
        import re
        # Remove subtitle numbers
        text = re.sub(r'^\d+\s*$', '', subtitle_content, flags=re.MULTILINE)
        # Remove timestamps
        text = re.sub(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', '', text)
        # Remove empty lines
        text = '\n'.join(line for line in text.split('\n') if line.strip())

        # Take first 2000 characters for detection (faster and usually accurate)
        sample = text[:2000]

        if len(sample) < 50:
            logger.warning("Subtitle text too short for language detection")
            return 'en'  # Default to English

        detected = detect(sample)

        # langdetect returns 2-letter codes, we may need to map some
        # Map common variants
        lang_map = {
            'pt': 'pt-PT',  # Default Portuguese to PT-PT
            'en': 'en',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'it': 'it',
            'ja': 'ja',
            'ko': 'ko',
            'zh-cn': 'zh',
            'zh-tw': 'zh',
        }

        result = lang_map.get(detected, detected)
        logger.info(f"Detected language: {result} (from {detected})")
        return result

    except LangDetectException as e:
        logger.error(f"Language detection error: {e}")
        return 'en'  # Default to English on error
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}", exc_info=True)
        return 'en'


def create_translation_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create translation blueprint with injected dependencies.

    Args:
        services: Service container with all initialized services
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('translation', __name__)

    @bp.route('/detect-language', methods=['POST'])
    def detect_language():
        """
        Detect language from subtitle file

        Request: multipart/form-data
            - subtitle: SRT file

        Response: JSON with detected language
        """
        if 'subtitle' not in request.files:
            logger.warning("detect-language: Missing subtitle file in request")
            return jsonify({'success': False, 'error': 'Missing subtitle file'}), HTTP_BAD_REQUEST

        subtitle_file = request.files['subtitle']

        try:
            # Read subtitle content
            content = subtitle_file.read().decode('utf-8', errors='ignore')

            # Detect language
            detected_lang = detect_subtitle_language(content)

            return jsonify({
                'success': True,
                'language': detected_lang,
                'confidence': 'high'  # langdetect doesn't provide confidence, but we can add it
            })

        except Exception as e:
            logger.error(f"Language detection error: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Language detection failed: {str(e)}'
            }), HTTP_INTERNAL_ERROR

    def _translate_background(job_id: str, input_path: Path, output_path: Path,
                            source_lang: str, target_lang: str, movie_context: str):
        """Background task for translation"""
        def progress_update(progress_data):
            """Callback to update progress"""
            services.job_storage_service.update_job(job_id, {'progress': progress_data})
            logger.debug(f"Job {job_id}: {progress_data.get('message', 'Progress update')}")

        try:
            success = services.translation_service.translate_file(
                input_path,
                output_path,
                source_lang,
                target_lang,
                movie_context,
                progress_callback=progress_update
            )

            if success:
                services.job_storage_service.update_job(job_id, {
                    'status': 'completed',
                    'output_file': str(output_path)
                })
                logger.info(f"Job {job_id}: Translation completed")
            else:
                services.job_storage_service.update_job(job_id, {
                    'status': 'error',
                    'error': 'Translation failed'
                })
                logger.error(f"Job {job_id}: Translation failed")

        except Exception as e:
            services.job_storage_service.update_job(job_id, {
                'status': 'error',
                'error': str(e)
            })
            logger.error(f"Job {job_id}: Error - {e}", exc_info=True)

    @bp.route('/translate', methods=['POST'])
    def translate_subtitle():
        """
        Start subtitle translation job

        Request: multipart/form-data
            - subtitle: SRT file
            - source_lang: source language code (en, pt, pt-PT, pt-BR)
            - target_lang: target language code (en, pt, pt-PT, pt-BR)
            - context: optional movie/context name
            - tone: optional tone (casual, formal, technical)

        Response: JSON with job_id for status polling
        """
        if 'subtitle' not in request.files:
            logger.warning("translate: Missing subtitle file in request")
            return jsonify({'success': False, 'error': 'Missing subtitle file'}), HTTP_BAD_REQUEST

        subtitle_file = request.files['subtitle']
        source_lang = request.form.get('source_lang', 'en')
        target_lang = request.form.get('target_lang', 'pt-PT')
        context = request.form.get('context', '')
        tone = request.form.get('tone', 'casual')

        # Build movie context string
        movie_context = f"{context} ({tone})" if context else tone

        logger.info(
            f"Starting translation job: {subtitle_file.filename} "
            f"({source_lang} -> {target_lang})"
            + (f", Context: {movie_context}" if movie_context else "")
        )

        # Create unique job ID
        job_id = str(uuid.uuid4())

        # Create persistent temp directory for this job
        job_folder = config.TEMP_DIR / f'translation_{job_id}'
        job_folder.mkdir(parents=True, exist_ok=True)

        input_path = job_folder / subtitle_file.filename
        output_filename = subtitle_file.filename.replace('.srt', f'_{target_lang}.srt')
        output_path = job_folder / output_filename

        # Save uploaded file
        subtitle_file.save(str(input_path))

        # Initialize job status in Firestore
        job_data = {
            'status': 'starting',
            'filename': subtitle_file.filename,
            'output_filename': output_filename,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'progress': {
                'status': 'starting',
                'percentage': 0,
                'message': 'Initializing translation...'
            }
        }
        services.job_storage_service.create_job(job_id, job_data)

        # Start translation in background thread
        thread = threading.Thread(
            target=_translate_background,
            args=(job_id, input_path, output_path, source_lang, target_lang, movie_context)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Translation job started'
        })

    @bp.route('/translate-status/<job_id>', methods=['GET'])
    def get_translation_status(job_id: str):
        """
        Get translation job status

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
            'progress': job.get('progress', {})
        }

        if job['status'] == 'error':
            response['error'] = job.get('error', 'Unknown error')

        return jsonify(response)

    @bp.route('/translate-download/<job_id>', methods=['GET'])
    def download_translated(job_id: str):
        """
        Download completed translation

        Returns: Translated SRT file
        """
        job = services.job_storage_service.get_job(job_id)

        if not job:
            return jsonify({'error': 'Job not found'}), 404

        if job['status'] != 'completed':
            return jsonify({'error': 'Translation not yet complete'}), HTTP_BAD_REQUEST

        output_file = job.get('output_file')
        if not output_file or not Path(output_file).exists():
            return jsonify({'error': 'Output file not found'}), 404

        return send_file(
            output_file,
            mimetype='text/plain',
            as_attachment=True,
            download_name=job.get('output_filename', 'translated.srt')
        )

    return bp
