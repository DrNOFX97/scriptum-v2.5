"""
WSGI entry point for Gunicorn deployment.
Production-ready Flask app with error handling.
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import Flask first to ensure it's available
from flask import Flask, jsonify
from flask_cors import CORS

def create_minimal_app():
    """
    Create a minimal Flask app that will work even if some services fail.
    This ensures the app can start and be debugged.
    """
    app = Flask(__name__)
    CORS(app)

    # Basic configuration from environment
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'

    # Health check endpoint (required by Render)
    @app.route('/health')
    def health():
        return jsonify({
            'success': True,
            'data': {
                'status': 'ok',
                'version': '2.5.0',
                'service': 'Scriptum API'
            }
        })

    # Root endpoint
    @app.route('/')
    def home():
        return jsonify({
            'success': True,
            'data': {
                'name': 'Scriptum API',
                'version': '2.5.0',
                'endpoints': ['/health', '/diagnostics']
            }
        })

    # Diagnostics endpoint
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
                }
            }
        })

    return app

try:
    # Try to import and use the full app
    from scriptum_api.app import create_app as create_full_app
    from scriptum_api.config import Config

    config = Config()
    app = create_full_app(config)
    print("✅ Full Scriptum API loaded successfully")

except Exception as e:
    # Fall back to minimal app if full app fails
    print(f"⚠️  Failed to load full app: {e}")
    print("⚠️  Falling back to minimal app")
    app = create_minimal_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
