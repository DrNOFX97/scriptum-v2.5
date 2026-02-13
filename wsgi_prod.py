"""
Production WSGI entry point with gradual service loading.
Provides core functionality even if some services fail.
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

def create_production_app():
    """
    Create production-ready app with gradual service loading.
    Each service is loaded independently to maximize availability.
    """
    app = Flask(__name__)

    # Configure CORS - Allow all origins for production
    # This is necessary because requests come from Firebase Hosting, Netlify, and localhost
    CORS(app,
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         expose_headers=["Content-Range", "X-Content-Range"],
         supports_credentials=False,
         max_age=3600)

    # Basic configuration
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB

    # Setup upload folder
    upload_folder = Path(__file__).parent / 'uploads'
    upload_folder.mkdir(exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Store loaded services
    app.services = {}

    # Handle OPTIONS preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({'status': 'ok'})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
            response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response

    # Force CORS headers on all responses (using set instead of add to avoid duplicates)
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

    # =========================================================================
    # Core Endpoints (Always Available)
    # =========================================================================

    @app.route('/health')
    def health():
        return jsonify({
            'success': True,
            'data': {
                'status': 'ok',
                'version': '2.5.0',
                'service': 'Scriptum API',
                'services_loaded': list(app.services.keys())
            }
        })

    @app.route('/')
    def home():
        return jsonify({
            'success': True,
            'data': {
                'name': 'Scriptum API',
                'version': '2.5.0',
                'services': list(app.services.keys()),
                'endpoints': {
                    'health': '/health',
                    'diagnostics': '/diagnostics',
                    'config': '/config',
                    'search': '/search-subtitles',
                    'movie': '/recognize-movie',
                    'video': '/analyze-video',
                    'sync': '/sync',
                    'translate': '/translate'
                }
            }
        })

    @app.route('/diagnostics')
    def diagnostics():
        return jsonify({
            'success': True,
            'data': {
                'python_version': sys.version,
                'environment': {
                    'PORT': os.getenv('PORT', 'not set'),
                    'DEBUG': os.getenv('DEBUG', 'not set'),
                    'TMDB_API_KEY': 'set' if os.getenv('TMDB_API_KEY') else 'not set',
                    'OPENSUBTITLES_API_KEY': 'set' if os.getenv('OPENSUBTITLES_API_KEY') else 'not set',
                    'GEMINI_API_KEY': 'set' if os.getenv('GEMINI_API_KEY') else 'not set'
                },
                'services_loaded': list(app.services.keys()),
                'upload_folder': str(upload_folder)
            }
        })

    @app.route('/config')
    def get_config():
        """Get API configuration"""
        return jsonify({
            'success': True,
            'data': {
                'api_keys': {
                    'opensubtitles': bool(os.getenv('OPENSUBTITLES_API_KEY')),
                    'tmdb': bool(os.getenv('TMDB_API_KEY')),
                    'gemini': bool(os.getenv('GEMINI_API_KEY'))
                }
            }
        })

    # =========================================================================
    # Load Services Gradually
    # =========================================================================

    # Try to load Config
    try:
        from scriptum_api.config import Config
        config = Config()
        app.services['config'] = config
        print("✅ Config loaded")
    except Exception as e:
        print(f"⚠️  Config failed: {e}")

    # Try to load SubtitleService
    try:
        from scriptum_api.services.subtitle_service import SubtitleService
        api_key = os.getenv('OPENSUBTITLES_API_KEY', '')
        app.services['subtitle'] = SubtitleService(api_key)
        print("✅ SubtitleService loaded")

        @app.route('/search-subtitles', methods=['POST'])
        def search_subtitles():
            data = request.get_json()
            query = data.get('query', '')
            language = data.get('language', 'pt')

            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Query is required'
                }), 400

            try:
                results = app.services['subtitle'].search_by_query(query, language)
                return jsonify({
                    'success': True,
                    'data': {'subtitles': results}
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    except Exception as e:
        print(f"⚠️  SubtitleService failed: {e}")

    # Try to load MovieService
    try:
        from scriptum_api.services.movie_service import MovieService
        api_key = os.getenv('TMDB_API_KEY', '')
        app.services['movie'] = MovieService(api_key)
        print("✅ MovieService loaded")

        @app.route('/recognize-movie', methods=['POST'])
        def recognize_movie():
            # Support both file upload and JSON with filename
            if request.is_json:
                data = request.get_json()
                filename = data.get('filename', '')
            elif 'video' in request.files:
                video = request.files['video']
                filename = video.filename
            else:
                return jsonify({
                    'success': False,
                    'error': 'Video file or filename is required'
                }), 400

            if not filename:
                return jsonify({
                    'success': False,
                    'error': 'Filename is required'
                }), 400

            try:
                # Use MovieService to search for movie
                movie_service = app.services.get('movie')
                if not movie_service:
                    return jsonify({
                        'success': False,
                        'error': 'Movie service not available'
                    }), 503

                # Recognize movie from filename
                result = movie_service.recognize_from_filename(filename)

                if result:
                    return jsonify({
                        'success': True,
                        'movie': result
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Movie not found'
                    }), 404

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    except Exception as e:
        print(f"⚠️  MovieService failed: {e}")

    # Try to load VideoService
    try:
        from scriptum_api.services.video_service import VideoService
        app.services['video'] = VideoService()
        print("✅ VideoService loaded")
    except Exception as e:
        print(f"⚠️  VideoService failed: {e}")

    # =========================================================================
    # Video Analysis Endpoint
    # =========================================================================
    @app.route('/analyze-video', methods=['POST'])
    def analyze_video():
        """Analyze uploaded video file"""
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Video file is required'
            }), 400

        video_file = request.files['video']
        if not video_file.filename:
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        try:
            # Save uploaded file
            import uuid
            from datetime import datetime

            file_ext = video_file.filename.rsplit('.', 1)[-1].lower()
            safe_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            filepath = upload_folder / safe_filename

            video_file.save(str(filepath))

            # Try to get video info using VideoService if available
            video_service = app.services.get('video')
            if video_service:
                try:
                    video_info = video_service.get_video_info(str(filepath))
                    return jsonify({
                        'success': True,
                        'filename': video_file.filename,
                        'saved_as': safe_filename,
                        'video_info': video_info,
                        'can_remux_to_mp4': False,
                        'can_convert_to_mp4': False
                    })
                except Exception as e:
                    print(f"Video analysis failed: {e}")

            # Fallback: return basic info without video_info
            return jsonify({
                'success': True,
                'filename': video_file.filename,
                'saved_as': safe_filename,
                'video_info': None,
                'can_remux_to_mp4': False,
                'can_convert_to_mp4': False,
                'message': 'Video uploaded successfully (detailed analysis unavailable)'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # Subtitle Sync Endpoint
    # =========================================================================
    @app.route('/sync', methods=['POST'])
    def sync_subtitles():
        """Sync subtitle with video"""
        if 'video' not in request.files or 'subtitle' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Both video and subtitle files are required'
            }), 400

        video_file = request.files['video']
        subtitle_file = request.files['subtitle']

        try:
            import uuid
            from datetime import datetime

            # Save files
            video_ext = video_file.filename.rsplit('.', 1)[-1].lower()
            sub_ext = subtitle_file.filename.rsplit('.', 1)[-1].lower()

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_filename = f"video_{uuid.uuid4().hex[:8]}_{timestamp}.{video_ext}"
            sub_filename = f"sub_{uuid.uuid4().hex[:8]}_{timestamp}.{sub_ext}"

            video_path = upload_folder / video_filename
            sub_path = upload_folder / sub_filename

            video_file.save(str(video_path))
            subtitle_file.save(str(sub_path))

            # Return success with file paths for now
            # TODO: Implement actual sync logic with SyncService
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Files uploaded successfully. Sync feature coming soon.',
                    'video': video_filename,
                    'subtitle': sub_filename
                }
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # Translation Endpoint
    # =========================================================================
    @app.route('/translate', methods=['POST'])
    def translate_subtitle():
        """Translate subtitle file"""
        if 'subtitle' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Subtitle file is required'
            }), 400

        subtitle_file = request.files['subtitle']
        source_lang = request.form.get('source_lang', 'en')
        target_lang = request.form.get('target_lang', 'pt')

        try:
            import uuid
            from datetime import datetime

            # Save file
            sub_ext = subtitle_file.filename.rsplit('.', 1)[-1].lower()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            sub_filename = f"translate_{uuid.uuid4().hex[:8]}_{timestamp}.{sub_ext}"
            sub_path = upload_folder / sub_filename

            subtitle_file.save(str(sub_path))

            # Return success
            # TODO: Implement actual translation with TranslationService
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Subtitle uploaded successfully. Translation feature coming soon.',
                    'filename': sub_filename,
                    'source_lang': source_lang,
                    'target_lang': target_lang
                }
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # Cloud Storage Upload Endpoints (for large files)
    # =========================================================================

    @app.route('/upload/request', methods=['POST'])
    def request_upload():
        """Generate signed URL for direct upload to Cloud Storage"""
        data = request.get_json()
        filename = data.get('filename', 'video.mp4')
        content_type = data.get('content_type', 'video/mp4')

        try:
            from src.scriptum_api.utils.storage import generate_upload_signed_url

            result = generate_upload_signed_url(filename, content_type)

            return jsonify({
                'success': True,
                'upload_url': result['signed_url'],
                'blob_name': result['blob_name'],
                'bucket': result['bucket']
            })

        except Exception as e:
            print(f"❌ Error generating upload URL: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/upload/complete', methods=['POST'])
    def complete_upload():
        """Process video after it's been uploaded to Cloud Storage"""
        data = request.get_json()
        blob_name = data.get('blob_name')
        original_filename = data.get('filename')

        if not blob_name:
            return jsonify({
                'success': False,
                'error': 'blob_name is required'
            }), 400

        try:
            from src.scriptum_api.utils.storage import get_blob_download_url

            # Try to get video info using VideoService if available
            video_service = app.services.get('video')
            video_info = None

            if video_service:
                try:
                    # Download blob to temp file for analysis
                    import tempfile
                    import os
                    from src.scriptum_api.utils.storage import download_blob_to_file

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                        temp_path = tmp.name

                    download_blob_to_file(blob_name, temp_path)
                    video_info = video_service.get_video_info(temp_path)

                    # Clean up temp file
                    os.unlink(temp_path)

                except Exception as e:
                    print(f"⚠️  Video analysis failed: {e}")

            # Get download URL
            download_url = get_blob_download_url(blob_name)

            response = {
                'success': True,
                'filename': original_filename,
                'blob_name': blob_name,
                'download_url': download_url,
                'video_info': video_info,
                'can_remux_to_mp4': False,
                'can_convert_to_mp4': False
            }

            # Try movie recognition if filename provided
            if original_filename:
                movie_service = app.services.get('movie')
                if movie_service:
                    try:
                        movie_result = movie_service.recognize_from_filename(original_filename)
                        if movie_result:
                            response['movie'] = movie_result
                    except Exception as e:
                        print(f"⚠️  Movie recognition failed: {e}")

            return jsonify(response)

        except Exception as e:
            print(f"❌ Error processing upload: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    print(f"🚀 App created with {len(app.services)} services loaded")
    return app

# Create the app
app = create_production_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
