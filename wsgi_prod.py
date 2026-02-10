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
    CORS(app)

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
                    'movie': '/recognize-movie'
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

    print(f"🚀 App created with {len(app.services)} services loaded")
    return app

# Create the app
app = create_production_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
