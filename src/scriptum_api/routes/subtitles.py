"""
Subtitle search and download endpoints.

Handles subtitle searching via OpenSubtitles and LegendasDivx,
downloading, and serving subtitle files.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
import time
import os

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..utils.subtitle_validator import validate_subtitles
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR, LANGUAGE_FALLBACK

logger = setup_logger(__name__)

# Upload folder for downloaded files
UPLOAD_FOLDER = Path(__file__).parent.parent.parent.parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)


def create_subtitles_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create subtitles blueprint with injected dependencies.

    Args:
        services: Service container with all initialized services
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('subtitles', __name__)

    @bp.route('/search-subtitles', methods=['POST'])
    def search_subtitles():
        """
        Search subtitles on OpenSubtitles AND LegendasDivx with fallback

        Request: JSON
            - query: search query (movie name)
            - language: language code (pt, en, etc) - optional, default: pt
            - limit: max results - optional, default: 10

        Response: JSON
            - success: bool
            - subtitles: list of subtitle results from both sources
            - language: language code of the results (may differ from request if fallback occurred)
        """
        data = request.get_json()

        if not data or 'query' not in data:
            logger.warning("search_subtitles: Missing query parameter")
            return jsonify({'error': 'Missing query parameter'}), HTTP_BAD_REQUEST

        query = data['query']
        requested_language = data.get('language', 'pt')
        limit = data.get('limit', 10)

        logger.info(
            f"Searching subtitles - Query: '{query}', "
            f"Language: {requested_language}, Limit: {limit}"
        )

        languages_to_try = LANGUAGE_FALLBACK.get(requested_language, [requested_language, 'en'])
        actual_language = None

        for lang in languages_to_try:
            all_subtitles = []

            # 1. OpenSubtitles
            logger.debug(f"Searching OpenSubtitles ({lang.upper()})...")
            try:
                opensub_results = services.subtitle_service.search_by_query(query, lang, limit)
                if opensub_results:
                    logger.info(f"OpenSubtitles: {len(opensub_results)} results found")
                    for sub in opensub_results:
                        sub['source'] = 'opensubtitles'
                    all_subtitles.extend(opensub_results)
                else:
                    logger.debug(f"OpenSubtitles: No results in {lang.upper()}")
            except Exception as e:
                logger.error(f"OpenSubtitles search error: {e}", exc_info=True)

            # 2. LegendasDivx (ONLY for Portuguese)
            # LegendasDivx is a Portuguese site and only has PT subtitles
            if lang in ['pt', 'pt-PT', 'pt-pt', 'pt-BR', 'pt-br']:
                if services.legendasdivx_service.is_available():
                    logger.debug(f"Searching LegendasDivx ({lang})...")
                    try:
                        divx_results = services.legendasdivx_service.search(query, lang, limit)
                        if divx_results:
                            logger.info(f"LegendasDivx: {len(divx_results)} results found")
                            all_subtitles.extend(divx_results)
                        else:
                            logger.debug(f"LegendasDivx: No results in {lang}")
                    except Exception as e:
                        logger.error(f"LegendasDivx search error: {e}", exc_info=True)
                else:
                    logger.warning("LegendasDivx API not available")

            if all_subtitles:
                actual_language = lang
                # Sort: LegendasDivx first, then by downloads (most popular first)
                # Priority: 0 for legendasdivx, 1 for opensubtitles
                all_subtitles.sort(
                    key=lambda x: (
                        0 if x.get('source') == 'legendasdivx' else 1,  # LegendasDivx first
                        -x.get('downloads', 0)  # Then by downloads (descending)
                    )
                )
                # Limit total results
                all_subtitles = all_subtitles[:limit]

                if lang != requested_language:
                    logger.info(
                        f"Found {len(all_subtitles)} subtitles in {lang.upper()} "
                        f"(fallback from {requested_language.upper()})"
                    )
                else:
                    logger.info(f"Found {len(all_subtitles)} subtitles in {lang.upper()}")

                return jsonify({
                    'success': True,
                    'count': len(all_subtitles),
                    'subtitles': all_subtitles,
                    'language': actual_language
                })
            else:
                logger.debug(f"No results in {lang.upper()}")

        # No results in any language
        logger.warning(f"No subtitles found for query: '{query}'")
        return jsonify({
            'success': False,
            'message': 'No subtitles found'
        })

    @bp.route('/download-subtitle', methods=['POST'])
    def download_subtitle():
        """
        Download subtitle from OpenSubtitles OR LegendasDivx

        Request: JSON
            - file_id: Subtitle ID
            - source: 'opensubtitles' or 'legendasdivx' (optional, auto-detect)

        Response: JSON with file path
        """
        data = request.get_json()
        logger.debug(f"download_subtitle: received data: {data}")

        if not data or 'file_id' not in data:
            logger.warning("download_subtitle: Missing file_id parameter")
            return jsonify({'error': 'Missing file_id parameter'}), HTTP_BAD_REQUEST

        file_id = data['file_id']
        source = data.get('source', 'opensubtitles')  # Default to OpenSubtitles for backward compatibility

        logger.info(f"Downloading subtitle - File ID: {file_id}, Source: {source}")

        try:
            # Download using appropriate service
            if source == 'legendasdivx':
                logger.debug(f"Using LegendasDivx service for download: {file_id}")
                content = services.legendasdivx_service.download_subtitle(str(file_id))
            else:
                logger.debug(f"Using OpenSubtitles service for download: {file_id}")
                content = services.subtitle_service.download_subtitle(file_id)

            logger.debug(f"Downloaded content length: {len(content) if content else 0} bytes")

            if not content:
                logger.error(f"Download failed: No content returned for {file_id}")
                return jsonify({'success': False, 'error': 'Download failed'}), HTTP_INTERNAL_ERROR

            # Save to temp file
            filename = f'subtitle_{file_id}_{int(time.time())}.srt'
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            with open(filepath, 'wb') as f:
                f.write(content)

            logger.info(f"Subtitle saved successfully: {filename}")

            return jsonify({
                'success': True,
                'file_path': filename
            })

        except Exception as e:
            logger.error(f"Subtitle download error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), HTTP_INTERNAL_ERROR

    @bp.route('/download/<filename>', methods=['GET'])
    def download_file(filename):
        """
        Serve downloaded subtitle files

        Response: File download
        """
        try:
            filepath = UPLOAD_FOLDER / filename
            if not filepath.exists():
                logger.warning(f"File not found: {filename}")
                return jsonify({'error': 'File not found'}), 404

            logger.debug(f"Serving file: {filename}")

            return send_file(
                filepath,
                mimetype='text/plain',
                as_attachment=False,
                download_name=filename
            )

        except Exception as e:
            logger.error(f"Error serving file '{filename}': {e}", exc_info=True)
            return jsonify({'error': str(e)}), HTTP_INTERNAL_ERROR

    @bp.route('/sync-log/<filename>', methods=['GET'])
    def get_sync_log(filename):
        """
        Get sync log content for real-time progress

        Response: JSON with log lines
        """
        try:
            filepath = UPLOAD_FOLDER / filename
            if not filepath.exists():
                logger.debug(f"Sync log not found (yet): {filename}")
                return jsonify({'logs': [], 'complete': False})

            with open(filepath, 'r', encoding='utf-8') as f:
                logs = f.readlines()

            # Check if complete (last line contains "Complete")
            complete = len(logs) > 0 and 'Complete' in logs[-1]

            logger.debug(f"Sync log retrieved: {filename} (complete: {complete})")

            return jsonify({
                'logs': [line.strip() for line in logs],
                'complete': complete
            })

        except Exception as e:
            logger.error(f"Error reading sync log '{filename}': {e}", exc_info=True)
            return jsonify({'logs': [f'Error: {e}'], 'complete': False})

    @bp.route('/validate-subtitles', methods=['POST'])
    def validate_subtitle_quality():
        """
        Validate subtitle quality based on PT-PT professional standards

        Request: FormData with 'subtitle' file OR JSON with 'content'/'filename'

        Response: JSON
            - success: bool
            - validation: validation results with problems and stats
        """
        try:
            srt_content = None

            # Try FormData first (file upload)
            if 'subtitle' in request.files:
                subtitle_file = request.files['subtitle']
                srt_content = subtitle_file.read().decode('utf-8')

            # Try JSON
            elif request.is_json:
                data = request.get_json()

                if 'content' in data:
                    srt_content = data['content']
                elif 'filename' in data:
                    filepath = UPLOAD_FOLDER / data['filename']
                    if not filepath.exists():
                        return jsonify({'error': 'File not found'}), 404

                    with open(filepath, 'r', encoding='utf-8') as f:
                        srt_content = f.read()

            if not srt_content:
                return jsonify({'error': 'No subtitle content provided'}), HTTP_BAD_REQUEST

            logger.info("Validating subtitle quality (PT-PT standards)")

            # Run validation
            validation_results = validate_subtitles(srt_content)

            logger.info(
                f"Validation complete: {validation_results['total_entries']} entries, "
                f"{len(validation_results['problems'])} problems found"
            )

            return jsonify({
                'success': True,
                'validation': validation_results
            })

        except Exception as e:
            logger.error(f"Subtitle validation error: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), HTTP_INTERNAL_ERROR

    return bp
