"""
Subtitle translation endpoints.

Handles subtitle translation using Google Gemini.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import tempfile

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR

logger = setup_logger(__name__)


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

    @bp.route('/translate', methods=['POST'])
    def translate_subtitle():
        """
        Translate subtitle using Google Gemini

        Request: multipart/form-data
            - subtitle: SRT file
            - source_lang: source language code (en, pt)
            - target_lang: target language code (en, pt)
            - movie_context: optional movie name for context

        Response: Binary (translated SRT file)
        """
        if 'subtitle' not in request.files:
            logger.warning("translate: Missing subtitle file in request")
            return jsonify({'error': 'Missing subtitle file'}), HTTP_BAD_REQUEST

        subtitle_file = request.files['subtitle']
        source_lang = request.form.get('source_lang', 'en')
        target_lang = request.form.get('target_lang', 'pt')
        movie_context = request.form.get('movie_context')

        if not subtitle_file.filename.endswith('.srt'):
            logger.warning(f"translate: Invalid subtitle format: {subtitle_file.filename}")
            return jsonify({'error': 'Subtitle must be .srt format'}), HTTP_BAD_REQUEST

        if source_lang == target_lang:
            logger.warning(
                f"translate: Same source and target language: {source_lang}"
            )
            return jsonify({'error': 'Source and target languages must be different'}), HTTP_BAD_REQUEST

        logger.info(
            f"Translating subtitle: {subtitle_file.filename} "
            f"({source_lang} -> {target_lang})"
            + (f", Movie context: {movie_context}" if movie_context else "")
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # Save files
            input_path = tmp / subtitle_file.filename
            output_path = tmp / subtitle_file.filename.replace('.srt', f'_{target_lang}.srt')

            subtitle_file.save(str(input_path))
            logger.debug(f"Subtitle saved to: {input_path}")

            try:
                # Translate using service
                success = services.translation_service.translate_file(
                    input_path,
                    output_path,
                    source_lang,
                    target_lang,
                    movie_context
                )

                if not success:
                    logger.error(f"Translation failed for: {subtitle_file.filename}")
                    return jsonify({'error': 'Translation failed'}), HTTP_INTERNAL_ERROR

                logger.info(f"Translation successful: {output_path.name}")

                return send_file(
                    str(output_path),
                    mimetype='text/plain',
                    as_attachment=True,
                    download_name=output_path.name
                )

            except Exception as e:
                logger.error(f"Translation error: {e}", exc_info=True)
                return jsonify({'error': f'Translation failed: {str(e)}'}), HTTP_INTERNAL_ERROR

    return bp
