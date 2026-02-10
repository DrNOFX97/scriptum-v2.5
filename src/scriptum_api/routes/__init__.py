"""
Route blueprints for Scriptum API.
"""

from .health import create_health_blueprint
from .video import create_video_blueprint
from .subtitles import create_subtitles_blueprint
from .sync import create_sync_blueprint
from .translation import create_translation_blueprint
from .config import create_config_blueprint

__all__ = [
    'create_health_blueprint',
    'create_video_blueprint',
    'create_subtitles_blueprint',
    'create_sync_blueprint',
    'create_translation_blueprint',
    'create_config_blueprint',
]
