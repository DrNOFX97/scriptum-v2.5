"""
Health and diagnostics endpoints.
"""

from flask import Blueprint, jsonify
from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


def create_health_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create health check blueprint with injected dependencies.

    Args:
        services: Service container (not used but available)
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('health', __name__)

    @bp.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        logger.debug("Health check requested")
        return jsonify({
            'status': 'ok',
            'version': '2.5.0',
            'service': 'Scriptum API',
            'architecture': 'service-oriented'
        })

    @bp.route('/diagnostics', methods=['GET'])
    def diagnostics():
        """Expose configuration warnings for UI diagnostics"""
        logger.debug("Diagnostics requested")
        warnings = config.validate()

        return jsonify({
            'warnings': warnings,
            'keys': {
                'tmdb': bool(config.TMDB_API_KEY),
                'opensubtitles': bool(config.OPENSUBTITLES_API_KEY),
                'gemini': bool(config.GEMINI_API_KEY),
            }
        })

    return bp
