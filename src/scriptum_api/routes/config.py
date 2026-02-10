"""
Configuration management endpoints.

Handles reading and updating application configuration from .env files.
"""

from flask import Blueprint, request, jsonify
from pathlib import Path

from ..dependencies import ServiceContainer
from ..config import Config
from ..utils.logger import setup_logger
from ..constants import HTTP_BAD_REQUEST, HTTP_INTERNAL_ERROR, HTTP_NOT_FOUND

logger = setup_logger(__name__)


def create_config_blueprint(services: ServiceContainer, config: Config) -> Blueprint:
    """
    Create configuration management blueprint with injected dependencies.

    Args:
        services: Service container with all initialized services
        config: Application configuration

    Returns:
        Configured blueprint
    """
    bp = Blueprint('config', __name__)

    @bp.route('/config', methods=['GET'])
    def get_config():
        """
        Get current configuration from .env file

        Response: JSON
            - success: bool
            - config: dict with configuration values
        """
        try:
            from dotenv import dotenv_values

            # Path to .env file (project root)
            env_path = Path(__file__).parent.parent.parent.parent / '.env'
            logger.debug(f"Reading configuration from: {env_path}")

            if not env_path.exists():
                logger.error(f".env file not found at: {env_path}")
                return jsonify({
                    'success': False,
                    'error': '.env file not found'
                }), HTTP_NOT_FOUND

            # Read .env file
            env_config = dotenv_values(env_path)

            # Also read LegendasDivx config from its own .env
            legendasdivx_env_path = Path(__file__).parent.parent.parent.parent / 'legendasdivx-api' / '.env'
            legendasdivx_config = {}
            if legendasdivx_env_path.exists():
                legendasdivx_config = dotenv_values(legendasdivx_env_path)
                logger.debug(f"Read LegendasDivx config from: {legendasdivx_env_path}")

            # Return only the configurable values (hide sensitive info by default)
            config_data = {
                'OPENSUBTITLES_API_KEY': env_config.get('OPENSUBTITLES_API_KEY', ''),
                'OPENSUBTITLES_USER_AGENT': env_config.get('OPENSUBTITLES_USER_AGENT', ''),
                'GEMINI_API_KEY': env_config.get('GEMINI_API_KEY', ''),
                'TMDB_API_KEY': env_config.get('TMDB_API_KEY', ''),
                'LEGENDASDIVX_USER': legendasdivx_config.get('LEGENDASDIVX_USER', ''),
                'LEGENDASDIVX_PASS': legendasdivx_config.get('LEGENDASDIVX_PASS', ''),
            }

            logger.info("Configuration retrieved successfully")

            return jsonify({
                'success': True,
                'config': config_data
            })

        except Exception as e:
            logger.error(f"Error retrieving configuration: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), HTTP_INTERNAL_ERROR

    @bp.route('/config', methods=['POST'])
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
                logger.warning("update_config: Missing config data")
                return jsonify({
                    'success': False,
                    'error': 'Missing config data'
                }), HTTP_BAD_REQUEST

            new_config = data['config']
            logger.info(f"Updating configuration with {len(new_config)} values")

            # Separate LegendasDivx config from main config
            legendasdivx_keys = {'LEGENDASDIVX_USER', 'LEGENDASDIVX_PASS'}
            main_config = {k: v for k, v in new_config.items() if k not in legendasdivx_keys}
            legendasdivx_config = {k: v for k, v in new_config.items() if k in legendasdivx_keys}

            # Update main .env file
            env_path = Path(__file__).parent.parent.parent.parent / '.env'
            logger.debug(f"Updating main .env file: {env_path}")

            # Read current .env content
            if env_path.exists():
                with open(env_path, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
                logger.warning(f".env file does not exist, will create it: {env_path}")

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
                        logger.debug(f"Updated key: {key}")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            # Add new keys that weren't in the file
            for key, value in main_config.items():
                if key not in updated_keys:
                    new_lines.append(f"{key}={value}")
                    logger.debug(f"Added new key: {key}")

            # Write back to .env file
            with open(env_path, 'w') as f:
                f.write('\n'.join(new_lines) + '\n')

            logger.info("Main configuration updated in .env file")

            # Update LegendasDivx .env file
            if legendasdivx_config:
                legendasdivx_env_path = Path(__file__).parent.parent.parent.parent / 'legendasdivx-api' / '.env'
                logger.debug(f"Updating LegendasDivx .env file: {legendasdivx_env_path}")

                if legendasdivx_env_path.exists():
                    with open(legendasdivx_env_path, 'r') as f:
                        lines = f.readlines()
                else:
                    lines = []
                    logger.warning(
                        f"LegendasDivx .env file does not exist, will create it: {legendasdivx_env_path}"
                    )

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
                            logger.debug(f"Updated LegendasDivx key: {key}")
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)

                # Add new keys
                for key, value in legendasdivx_config.items():
                    if key not in updated_keys:
                        new_lines.append(f"{key}={value}")
                        logger.debug(f"Added new LegendasDivx key: {key}")

                # Write back
                with open(legendasdivx_env_path, 'w') as f:
                    f.write('\n'.join(new_lines) + '\n')

                logger.info("LegendasDivx configuration updated in legendasdivx-api/.env")

            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully. Please restart the server to apply changes.'
            })

        except Exception as e:
            logger.error(f"Error updating configuration: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), HTTP_INTERNAL_ERROR

    return bp
