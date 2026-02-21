#!/usr/bin/env python3
"""
Scriptum Sync API Server v2.1 (Refactored)
Clean, modular Flask API using service-oriented architecture

Usage:
    python app_refactored.py

Note: This is the refactored version. The original sync_api.py
is kept for backward compatibility during migration.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
from pathlib import Path
import io
import time
import os

# Import configuration
from api.config import config

# Import services
from api.services.video_service import VideoService
from api.services.movie_service import MovieService
from api.services.subtitle_service import SubtitleService
from api.services.translation_service import TranslationService
from api.services.sync_service import SyncService

# Initialize Flask app
# Serve static files from current directory
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configure max file upload size (10GB from config)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_VIDEO_SIZE

# Configure uploads folder
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)

@app.route('/')
def index():
    """Serve the main interface"""
    return send_file('sync.html')

# Initialize services
video_service = VideoService()
movie_service = MovieService(config.TMDB_API_KEY)
subtitle_service = SubtitleService(config.OPENSUBTITLES_API_KEY)
translation_service = TranslationService(config.GEMINI_API_KEY, config.TRANSLATION_BATCH_SIZE)
sync_service = SyncService()

# Initialize LegendasDivx service
from api.services.legendasdivx_service import LegendasDivxService
legendasdivx_service = LegendasDivxService()
print(f"🇵🇹 LegendasDivx: {'✅ Disponível' if legendasdivx_service.is_available() else '❌ Indisponível'}")


def print_banner():
    """Print startup banner with configuration"""
    print("=" * 70)
    print("🎬 Scriptum Sync API Server v2.1 (Refactored)")
    print("=" * 70)
    print()
    print("Architecture: Service-Oriented (Modular)")
    print()
    print("Endpoints:")
    print("  GET  /health                  - Health check")
    print("  POST /analyze-video           - Analyze video file")
    print("  POST /recognize-movie         - Recognize movie from filename")
    print("  POST /remux-mkv-to-mp4        - Remux MKV to MP4 (instant)")
    print("  POST /convert-to-mp4          - Convert video to MP4")
    print("  POST /extract-mkv-subtitles   - Extract MKV subtitles")
    print("  POST /search-subtitles        - Search OpenSubtitles")
    print("  POST /download-subtitle       - Download subtitle")
    print("  POST /sync                    - Sync subtitles (MLX Whisper)")
    print("  POST /translate               - Translate subtitles (Gemini)")
    print()
    print(f"Server: http://localhost:{config.PORT}")
    print()

    # Show configuration warnings
    warnings = config.validate()
    if warnings:
        for warning in warnings:
            print(warning)
        print()

    print("=" * 70)
    print()


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '2.1-refactored',
        'service': 'Scriptum Sync API',
        'architecture': 'service-oriented'
    })


@app.route('/diagnostics', methods=['GET'])
def diagnostics():
    """Expose configuration warnings for UI diagnostics"""
    warnings = config.validate()
    return jsonify({
        'warnings': warnings,
        'keys': {
            'tmdb': bool(config.TMDB_API_KEY),
            'opensubtitles': bool(config.OPENSUBTITLES_API_KEY),
            'gemini': bool(config.GEMINI_API_KEY),
        }
    })


@app.route('/analyze-video', methods=['POST'])
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
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        video_path = tmp / video_file.filename
        video_file.save(str(video_path))

        print(f"\n{'='*70}")
        print(f"📊 Analyzing video: {video_file.filename}")
        print(f"{'='*70}")

        # Get video info using service
        video_info = video_service.get_video_info(video_path)

        # Check conversion capabilities
        can_convert = video_service.can_convert_to_mp4(video_path)
        can_remux = video_service.can_remux_to_mp4(video_path)

        print(f"\n✅ Analysis complete")
        print(f"   Format: {video_info.get('format')}")
        print(f"   Resolution: {video_info.get('resolution')}")
        print(f"   Duration: {video_info.get('duration_formatted')}")
        print(f"   Can remux: {can_remux}")

        return jsonify({
            'success': True,
            'filename': video_file.filename,
            'video_info': video_info,
            'can_convert_to_mp4': can_convert,
            'can_remux_to_mp4': can_remux
        })


@app.route('/recognize-movie', methods=['POST'])
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
        return jsonify({'error': 'Missing filename'}), 400

    filename = data['filename']
    imdb_id = data.get('imdb_id')

    print(f"\n{'='*70}")
    print(f"🎬 Recognizing movie: {filename}")
    if imdb_id:
        print(f"   IMDB ID: {imdb_id}")
    print(f"{'='*70}")

    # Recognize movie using service
    movie = movie_service.recognize_from_filename(filename, imdb_id)

    if not movie:
        return jsonify({
            'success': False,
            'error': 'Movie not found'
        }), 404

    return jsonify({
        'success': True,
        'movie': movie
    })


@app.route('/remux-mkv-to-mp4', methods=['POST'])
def remux_mkv_to_mp4():
    """
    Remux MKV to MP4 (instant, no re-encoding)

    Request: multipart/form-data
        - video: MKV file

    Response: Binary (MP4 file)
    """
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']

    if not video_file.filename.lower().endswith('.mkv'):
        return jsonify({'error': 'Only MKV files supported'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / video_file.filename
        output_path = tmp / video_file.filename.replace('.mkv', '.mp4')

        video_file.save(str(input_path))

        print(f"\n{'='*70}")
        print(f"⚡ Remuxing: {video_file.filename}")
        print(f"{'='*70}")

        # Check if remux is possible
        if not video_service.can_remux_to_mp4(input_path):
            return jsonify({
                'error': 'Video codec not compatible for fast remux. Use /convert-to-mp4 instead.'
            }), 400

        # Remux using service
        success = video_service.remux_to_mp4(input_path, output_path)

        if not success:
            return jsonify({'error': 'Remux failed'}), 500

        return send_file(
            str(output_path),
            mimetype='video/mp4',
            as_attachment=True,
            download_name=output_path.name
        )


@app.route('/convert-to-mp4', methods=['POST'])
def convert_to_mp4():
    """
    Convert video to MP4 with re-encoding

    Request: multipart/form-data
        - video: video file
        - quality: str (fast, balanced, high) - optional, default: balanced

    Response: Binary (MP4 file)
    """
    if 'video' not in request.files:
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']
    quality = request.form.get('quality', 'balanced')

    if quality not in ['fast', 'balanced', 'high']:
        return jsonify({'error': 'Invalid quality. Use: fast, balanced, or high'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        input_path = tmp / video_file.filename
        output_path = tmp / f"{Path(video_file.filename).stem}.mp4"

        video_file.save(str(input_path))

        print(f"\n{'='*70}")
        print(f"🎬 Converting: {video_file.filename}")
        print(f"   Quality: {quality}")
        print(f"{'='*70}")

        # Convert using service
        success = video_service.convert_to_mp4(input_path, output_path, quality)

        if not success:
            return jsonify({'error': 'Conversion failed'}), 500

        return send_file(
            str(output_path),
            mimetype='video/mp4',
            as_attachment=True,
            download_name=output_path.name
        )


@app.route('/extract-mkv-subtitles', methods=['POST'])
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
        return jsonify({'error': 'Missing video file'}), 400

    video_file = request.files['video']

    if not video_file.filename.lower().endswith('.mkv'):
        return jsonify({'error': 'Only MKV files supported'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        video_path = tmp / video_file.filename
        video_file.save(str(video_path))

        print(f"\n{'='*70}")
        print(f"📤 Extracting subtitles: {video_file.filename}")
        print(f"{'='*70}")

        # Extract using service
        subtitles = video_service.extract_mkv_subtitles(video_path, tmp)

        if not subtitles:
            return jsonify({
                'success': False,
                'message': 'No subtitles found in MKV'
            })

        print(f"\n✅ Extracted {len(subtitles)} subtitle track(s)")

        # Read subtitle files and encode as base64 for JSON response
        import base64

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
                        
            # Remove file_path from response (was temporary)
            del sub['file_path']

        return jsonify({
            'success': True,
            'count': len(subtitles),
            'subtitles': subtitles
        })


@app.route('/search-subtitles', methods=['POST'])
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
        return jsonify({'error': 'Missing query parameter'}), 400

    query = data['query']
    requested_language = data.get('language', 'pt')
    limit = data.get('limit', 10)

    print(f"\n{'='*70}")
    print(f"🔍 Searching subtitles (OpenSubtitles + LegendasDivx)")
    print(f"   Query: {query}")
    print(f"   Requested Language: {requested_language}")
    print(f"{'='*70}")

    # Fallback order for different languages
    LANGUAGE_FALLBACK = {
        'pt': ['pt', 'es', 'it', 'fr', 'en'],
        'pt-PT': ['pt', 'es', 'it', 'fr', 'en'],
        'pt-BR': ['pt-BR', 'pt', 'es', 'it', 'fr', 'en'],
        'es': ['es', 'pt', 'it', 'fr', 'en'],
        'it': ['it', 'es', 'pt', 'fr', 'en'],
        'fr': ['fr', 'es', 'it', 'pt', 'en'],
        'en': ['en', 'es', 'pt', 'fr', 'it'],
        'de': ['de', 'en', 'fr', 'es'],
    }

    languages_to_try = LANGUAGE_FALLBACK.get(requested_language, [requested_language, 'en'])
    actual_language = None

    for lang in languages_to_try:
        all_subtitles = []

        # 1. OpenSubtitles
        print(f"🌍 Searching OpenSubtitles ({lang.upper()})...")
        opensub_results = subtitle_service.search_by_query(query, lang, limit)
        if opensub_results:
            print(f"   ✅ OpenSubtitles: {len(opensub_results)} results")
            for sub in opensub_results:
                sub['source'] = 'opensubtitles'
            all_subtitles.extend(opensub_results)

        # 2. LegendasDivx (ONLY for Portuguese)
        # LegendasDivx é um site português e só tem legendas PT
        if lang in ['pt', 'pt-PT', 'pt-pt', 'pt-BR', 'pt-br']:
            if legendasdivx_service.is_available():
                print(f"🇵🇹 Searching LegendasDivx ({lang})...")
                divx_results = legendasdivx_service.search(query, lang, limit)
                if divx_results:
                    print(f"   ✅ LegendasDivx: {len(divx_results)} results")
                    all_subtitles.extend(divx_results)
            else:
                print("   ⚠️  LegendasDivx API não disponível")

        if all_subtitles:
            actual_language = lang
            # Sort: LegendasDivx first, then by downloads (most popular first)
            # Priority: 1 for legendasdivx, 0 for opensubtitles
            all_subtitles.sort(
                key=lambda x: (
                    0 if x.get('source') == 'legendasdivx' else 1,  # LegendasDivx first
                    -x.get('downloads', 0)  # Then by downloads (descending)
                )
            )
            # Limit total results
            all_subtitles = all_subtitles[:limit]

            if lang != requested_language:
                print(f"✅ Found {len(all_subtitles)} subtitles in {lang.upper()} (fallback from {requested_language.upper()})")
            else:
                print(f"✅ Found {len(all_subtitles)} subtitles in {lang.upper()}")

            return jsonify({
                'success': True,
                'count': len(all_subtitles),
                'subtitles': all_subtitles,
                'language': actual_language
            })
        else:
            print(f"   ⚠️  No results in {lang.upper()}")

    # No results in any language
    print("❌ No subtitles found in any language")
    return jsonify({
        'success': False,
        'message': 'No subtitles found'
    })


@app.route('/download-subtitle', methods=['POST'])
def download_subtitle():
    """
    Download subtitle from OpenSubtitles OR LegendasDivx

    Request: JSON
        - file_id: Subtitle ID
        - source: 'opensubtitles' or 'legendasdivx' (optional, auto-detect)

    Response: JSON with file path
    """
    print("DEBUG: download_subtitle endpoint called", flush=True)
    data = request.get_json()
    print(f"DEBUG: received data: {data}", flush=True)

    if not data or 'file_id' not in data:
        print("DEBUG: Missing file_id", flush=True)
        return jsonify({'error': 'Missing file_id parameter'}), 400

    file_id = data['file_id']
    source = data.get('source', 'opensubtitles')  # Default to OpenSubtitles for backward compatibility

    print(f"DEBUG: file_id type: {type(file_id)}, value: {file_id}", flush=True)
    print(f"DEBUG: source: {source}", flush=True)

    print(f"\n{'='*70}")
    print(f"📥 Downloading subtitle")
    print(f"   File ID: {file_id}")
    print(f"   Source: {source}")
    print(f"{'='*70}", flush=True)

    try:
        # Download using appropriate service
        if source == 'legendasdivx':
            print(f"DEBUG: Calling legendasdivx_service.download_subtitle({file_id})", flush=True)
            content = legendasdivx_service.download_subtitle(str(file_id))
        else:
            print(f"DEBUG: Calling subtitle_service.download_subtitle({file_id})", flush=True)
            content = subtitle_service.download_subtitle(file_id)
        print(f"DEBUG: download_subtitle returned: {type(content)}, length: {len(content) if content else 0}", flush=True)

        if not content:
            print("DEBUG: Content is None or empty, returning error", flush=True)
            return jsonify({'success': False, 'error': 'Download failed'}), 500

        # Save to temp file
        filename = f'subtitle_{file_id}_{int(time.time())}.srt'
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, 'wb') as f:
            f.write(content)

        print(f"✅ Subtitle saved: {filename}")

        return jsonify({
            'success': True,
            'file_path': filename
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Serve downloaded subtitle files

    Response: File download
    """
    try:
        filepath = UPLOAD_FOLDER / filename
        if not filepath.exists():
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            filepath,
            mimetype='text/plain',
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        print(f"❌ Error serving file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/sync-log/<filename>', methods=['GET'])
def get_sync_log(filename):
    """
    Get sync log content for real-time progress

    Response: JSON with log lines
    """
    try:
        filepath = UPLOAD_FOLDER / filename
        if not filepath.exists():
            return jsonify({'logs': [], 'complete': False})

        with open(filepath, 'r', encoding='utf-8') as f:
            logs = f.readlines()

        # Check if complete (last line contains "Complete")
        complete = len(logs) > 0 and 'Complete' in logs[-1]

        return jsonify({
            'logs': [line.strip() for line in logs],
            'complete': complete
        })
    except Exception as e:
        return jsonify({'logs': [f'Error: {e}'], 'complete': False})


@app.route('/sync', methods=['POST'])
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
        return jsonify({'error': 'Missing video or subtitle file'}), 400

    video_file = request.files['video']
    subtitle_file = request.files['subtitle']

    if not subtitle_file.filename.endswith('.srt'):
        return jsonify({'error': 'Subtitle must be .srt format'}), 400

    # Save files to persistent location for download later
    video_path = UPLOAD_FOLDER / f"sync_video_{int(time.time())}_{video_file.filename}"
    subtitle_path = UPLOAD_FOLDER / f"sync_sub_{int(time.time())}_{subtitle_file.filename}"
    output_filename = f'synced_{int(time.time())}_{subtitle_file.filename}'
    output_path = UPLOAD_FOLDER / output_filename

    # Create log file for progress
    log_filename = f'sync_log_{int(time.time())}.txt'
    log_path = UPLOAD_FOLDER / log_filename

    video_file.save(str(video_path))
    subtitle_file.save(str(subtitle_path))

    print(f"\n{'='*70}")
    print(f"🔄 Starting sync process")
    print(f"   Video: {video_file.filename}")
    print(f"   Subtitle: {subtitle_file.filename}")
    print(f"   Log: {log_filename}")
    print(f"{'='*70}")

    # Create temp directory for processing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Sync using service with logging
        result = sync_service.sync_subtitles_with_log(
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
    except:
        pass

    if not result['success']:
        return jsonify(result), 500

    return jsonify({
        'success': True,
        'synced_file': output_filename,
        'log_file': log_filename,
        'offset_detected': result.get('offset_detected'),
        'stats': result.get('stats')
    })


@app.route('/translate', methods=['POST'])
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
        return jsonify({'error': 'Missing subtitle file'}), 400

    subtitle_file = request.files['subtitle']
    source_lang = request.form.get('source_lang', 'en')
    target_lang = request.form.get('target_lang', 'pt')
    movie_context = request.form.get('movie_context')

    if not subtitle_file.filename.endswith('.srt'):
        return jsonify({'error': 'Subtitle must be .srt format'}), 400

    if source_lang == target_lang:
        return jsonify({'error': 'Source and target languages must be different'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Save files
        input_path = tmp / subtitle_file.filename
        output_path = tmp / subtitle_file.filename.replace('.srt', f'_{target_lang}.srt')

        subtitle_file.save(str(input_path))

        # Translate using service
        success = translation_service.translate_file(
            input_path,
            output_path,
            source_lang,
            target_lang,
            movie_context
        )

        if not success:
            return jsonify({'error': 'Translation failed'}), 500

        return send_file(
            str(output_path),
            mimetype='text/plain',
            as_attachment=True,
            download_name=output_path.name
        )


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================

@app.route('/config', methods=['GET'])
def get_config():
    """
    Get current configuration from .env file

    Response: JSON
        - success: bool
        - config: dict with configuration values
    """
    try:
        from dotenv import dotenv_values

        # Path to .env file
        env_path = Path(__file__).parent / '.env'

        if not env_path.exists():
            return jsonify({
                'success': False,
                'error': '.env file not found'
            }), 404

        # Read .env file
        env_config = dotenv_values(env_path)

        # Also read LegendasDivx config from its own .env
        legendasdivx_env_path = Path(__file__).parent / 'legendasdivx-api' / '.env'
        legendasdivx_config = {}
        if legendasdivx_env_path.exists():
            legendasdivx_config = dotenv_values(legendasdivx_env_path)

        # Return only the configurable values (hide sensitive info by default)
        config_data = {
            'OPENSUBTITLES_API_KEY': env_config.get('OPENSUBTITLES_API_KEY', ''),
            'OPENSUBTITLES_USER_AGENT': env_config.get('OPENSUBTITLES_USER_AGENT', ''),
            'GEMINI_API_KEY': env_config.get('GEMINI_API_KEY', ''),
            'TMDB_API_KEY': env_config.get('TMDB_API_KEY', ''),
            'LEGENDASDIVX_USER': legendasdivx_config.get('LEGENDASDIVX_USER', ''),
            'LEGENDASDIVX_PASS': legendasdivx_config.get('LEGENDASDIVX_PASS', ''),
        }

        return jsonify({
            'success': True,
            'config': config_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/config', methods=['POST'])
def update_config():
    """
    Update configuration in .env file

    Request: JSON
        - config: dict with configuration values to update

    Response: JSON
        - success: bool
        - message: str
    """
    try:
        data = request.get_json()

        if not data or 'config' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing config data'
            }), 400

        new_config = data['config']

        # Separate LegendasDivx config from main config
        legendasdivx_keys = {'LEGENDASDIVX_USER', 'LEGENDASDIVX_PASS'}
        main_config = {k: v for k, v in new_config.items() if k not in legendasdivx_keys}
        legendasdivx_config = {k: v for k, v in new_config.items() if k in legendasdivx_keys}

        # Update main .env file
        env_path = Path(__file__).parent / '.env'

        # Read current .env content
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        # Update or add configuration values
        updated_keys = set()
        new_lines = []

        for line in lines:
            line = line.rstrip()
            if not line or line.startswith('#'):
                new_lines.append(line)
                continue

            # Parse line
            if '=' in line:
                key = line.split('=')[0].strip()
                if key in main_config:
                    new_lines.append(f"{key}={main_config[key]}")
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # Add new keys that weren't in the file
        for key, value in main_config.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}")

        # Write back to .env file
        with open(env_path, 'w') as f:
            f.write('\n'.join(new_lines) + '\n')

        print(f"✅ Main configuration updated in .env file")

        # Update LegendasDivx .env file
        if legendasdivx_config:
            legendasdivx_env_path = Path(__file__).parent / 'legendasdivx-api' / '.env'

            if legendasdivx_env_path.exists():
                with open(legendasdivx_env_path, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []

            updated_keys = set()
            new_lines = []

            for line in lines:
                line = line.rstrip()
                if not line or line.startswith('#'):
                    new_lines.append(line)
                    continue

                if '=' in line:
                    key = line.split('=')[0].strip()
                    if key in legendasdivx_config:
                        new_lines.append(f"{key}={legendasdivx_config[key]}")
                        updated_keys.add(key)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            # Add new keys
            for key, value in legendasdivx_config.items():
                if key not in updated_keys:
                    new_lines.append(f"{key}={value}")

            # Write back
            with open(legendasdivx_env_path, 'w') as f:
                f.write('\n'.join(new_lines) + '\n')

            print(f"✅ LegendasDivx configuration updated in legendasdivx-api/.env")

        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully. Please restart the server to apply changes.'
        })

    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print_banner()

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
