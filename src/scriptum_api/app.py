"""
Flask application factory for Scriptum API.
Creates and configures the Flask app with all services and routes.
"""

from flask import Flask, send_file
from flask_cors import CORS
from pathlib import Path
from typing import Optional

from .config import Config
from .dependencies import create_services, ServiceContainer
from .utils.logger import setup_logger

logger = setup_logger(__name__)


def create_app(config: Optional[Config] = None, upload_folder: Optional[Path] = None) -> Flask:
    """
    Application factory pattern for Flask app.

    Args:
        config: Optional configuration object (uses default if None)
        upload_folder: Optional upload folder path

    Returns:
        Configured Flask application

    Example:
        >>> app = create_app()
        >>> app.run(host='0.0.0.0', port=5001)
    """
    logger.info("Creating Flask application")

    # Initialize config
    if config is None:
        config = Config()

    # Create Flask app
    app = Flask(__name__, static_folder='.', static_url_path='')
    app.config.from_object(config)
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_VIDEO_SIZE

    # Enable CORS
    CORS(app)
    logger.debug("CORS enabled")

    # Setup upload folder
    if upload_folder is None:
        upload_folder = Path(__file__).parent.parent.parent / 'uploads'
    upload_folder.mkdir(exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    logger.info(f"Upload folder: {upload_folder}")

    # Initialize services
    try:
        services = create_services(config)
        app.services = services  # Store in app context for easy access
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise

    # Register blueprints
    _register_blueprints(app, services, config)

    # Start file cleanup service
    from .utils.cleanup import FileCleanupManager
    from .constants import UPLOAD_RETENTION_HOURS, CLEANUP_INTERVAL_HOURS

    cleanup_manager = FileCleanupManager(
        upload_folder,
        max_age_hours=UPLOAD_RETENTION_HOURS
    )
    cleanup_manager.start_background_cleanup(interval_hours=CLEANUP_INTERVAL_HOURS)
    app.cleanup_manager = cleanup_manager  # Store for manual control if needed
    logger.info("File cleanup service started")

    # Root route
    @app.route('/')
    def index():
        """Serve the main interface"""
        try:
            return send_file('sync.html')
        except FileNotFoundError:
            return {
                'status': 'ok',
                'message': 'Scriptum API v2.5',
                'docs': '/diagnostics'
            }

    logger.info("Flask application created successfully")
    return app


def _register_blueprints(app: Flask, services: ServiceContainer, config: Config) -> None:
    """
    Register all route blueprints with dependency injection.

    Args:
        app: Flask application
        services: Service container
        config: Application configuration
    """
    from .routes import (
        create_health_blueprint,
        create_video_blueprint,
        create_subtitles_blueprint,
        create_sync_blueprint,
        create_translation_blueprint,
        create_config_blueprint,
    )

    # Register blueprints
    blueprints = [
        ('health', create_health_blueprint(services, config)),
        ('video', create_video_blueprint(services, config)),
        ('subtitles', create_subtitles_blueprint(services, config)),
        ('sync', create_sync_blueprint(services, config)),
        ('translation', create_translation_blueprint(services, config)),
        ('config', create_config_blueprint(services, config)),
    ]

    for name, blueprint in blueprints:
        app.register_blueprint(blueprint)
        logger.debug(f"Registered blueprint: {name}")

    logger.info(f"Registered {len(blueprints)} blueprints")


def print_banner(config: Config, services: ServiceContainer) -> None:
    """
    Print startup banner with configuration.

    Args:
        config: Application configuration
        services: Service container (for feature availability)
    """
    print("=" * 70)
    print("🎬 Scriptum API v2.5")
    print("=" * 70)
    print()
    print("Architecture: Service-Oriented (Modular + Dependency Injection)")
    print()
    print("Endpoints:")
    print("  GET  /health                  - Health check")
    print("  GET  /diagnostics             - Configuration diagnostics")
    print("  POST /analyze-video           - Analyze video file")
    print("  POST /recognize-movie         - Recognize movie from filename")
    print("  POST /remux-mkv-to-mp4        - Remux MKV to MP4 (instant)")
    print("  POST /convert-to-mp4          - Convert video to MP4")
    print("  POST /extract-mkv-subtitles   - Extract MKV subtitles")
    print("  POST /search-subtitles        - Search OpenSubtitles")
    print("  POST /download-subtitle       - Download subtitle")
    print("  GET  /download/<filename>     - Download file")
    print("  POST /sync                    - Sync subtitles (MLX Whisper)")
    print("  POST /translate               - Translate subtitles (Gemini)")
    print("  GET  /config                  - Get configuration")
    print("  POST /config                  - Update configuration")
    print()
    print(f"Server: http://localhost:{config.PORT}")
    print()

    # Show feature availability
    print("Features:")
    print(f"  🎬 Movie Recognition: {'✅' if config.TMDB_API_KEY else '❌'}")
    print(f"  📝 Subtitle Search: {'✅' if config.OPENSUBTITLES_API_KEY else '❌'}")
    print(f"  🌐 Translation: {'✅' if config.GEMINI_API_KEY else '❌'}")
    print(f"  🇵🇹 LegendasDivx: {'✅' if services.legendasdivx_service.is_available() else '❌'}")
    print()

    # Show configuration warnings
    warnings = config.validate()
    if warnings:
        for warning in warnings:
            print(warning)
        print()

    print("=" * 70)
    print()
