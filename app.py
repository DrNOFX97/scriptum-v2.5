#!/usr/bin/env python3
"""
Scriptum API v2.5 - Entry Point

Clean, modular Flask API using service-oriented architecture with
dependency injection and professional logging.

Usage:
    python app.py

Environment Variables:
    See .env file or api/config.py for configuration options.
"""

import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from scriptum_api.app import create_app, print_banner
from scriptum_api.config import Config
from scriptum_api.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Main entry point for the application."""
    try:
        # Create configuration
        config = Config()

        # Create Flask app
        app = create_app(config)

        # Print startup banner
        print_banner(config, app.services)

        # Run server
        logger.info(f"Starting server on {config.HOST}:{config.PORT}")
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
