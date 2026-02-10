"""
WSGI entry point for Gunicorn deployment.
This file provides a simple entry point without path manipulation.
"""
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scriptum_api.app import create_app
from scriptum_api.config import Config

# Create app instance
config = Config()
app = create_app(config)

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
