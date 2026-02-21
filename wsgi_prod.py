"""
Production WSGI entry point for Scriptum API.
Simple wrapper around the main application factory.
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scriptum_api.app import create_app, print_banner
from scriptum_api.config import Config

# Create configuration with production settings
config = Config()

# Override CORS for production if needed
# Cloud Run allows requests from any origin (Firebase, Netlify, etc.)
if os.getenv('PRODUCTION_CORS', 'true').lower() == 'true':
    os.environ['CORS_ORIGINS'] = '*'

# Create Flask app using the application factory
app = create_app(config=config)

# Print startup banner
if __name__ != '__main__':
    # Running under gunicorn/production
    print_banner(config, app.services)
    print(f"🚀 Production mode: CORS={'*' if os.getenv('CORS_ORIGINS') == '*' else 'restricted'}")
    print()

# For local development
if __name__ == '__main__':
    print_banner(config, app.services)
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
