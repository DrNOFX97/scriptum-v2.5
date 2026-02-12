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

    # Configure CORS for Firebase Hosting and Netlify
    CORS(app, resources={
        r"/*": {
            "origins": [
                "https://scriptum-v2-50.web.app",
                "https://scriptum-v2-50.firebaseapp.com",
                "https://scriptum-v2-5.netlify.app",
                "http://localhost:5173",
                "http://localhost:5001"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": False,
            "max_age": 3600
        }
    })

    # Basic configuration
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB

    # Setup upload folder
    upload_folder = Path(__file__).parent / 'uploads'
    upload_folder.mkdir(exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    # Store loaded services
    app.services = {}

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

    print(f"🚀 App created with {len(app.services)} services loaded")
    return app

# Create the app
app = create_production_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
