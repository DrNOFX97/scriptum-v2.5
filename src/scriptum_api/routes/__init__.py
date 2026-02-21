"""
Route blueprints for Scriptum API.
"""

from .health import create_health_blueprint
from .video import create_video_blueprint
from .subtitles import create_subtitles_blueprint
from .sync import create_sync_blueprint
from .translation import create_translation_blueprint
from .config import create_config_blueprint
from .audio_conversion import create_audio_conversion_blueprint
from .audio_extraction import create_audio_extraction_blueprint
from .chunked_upload import create_chunked_upload_blueprint

__all__ = [
    'create_health_blueprint',
    'create_video_blueprint',
    'create_subtitles_blueprint',
    'create_sync_blueprint',
    'create_translation_blueprint',
    'create_config_blueprint',
    'create_audio_conversion_blueprint',
    'create_audio_extraction_blueprint',
    'create_chunked_upload_blueprint',
]
