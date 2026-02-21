"""
Configuration management for Scriptum API
Centralizes all environment variables and settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # API Keys
    TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
    OPENSUBTITLES_API_KEY = os.getenv('OPENSUBTITLES_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # Video processing
    MAX_VIDEO_SIZE = int(os.getenv('MAX_VIDEO_SIZE', 10 * 1024 * 1024 * 1024))  # 10GB
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv']
    SUPPORTED_SUBTITLE_FORMATS = ['.srt']

    # FFmpeg settings
    FFMPEG_THREADS = int(os.getenv('FFMPEG_THREADS', 0))  # 0 = auto

    # Translation settings
    TRANSLATION_BATCH_SIZE = int(os.getenv('TRANSLATION_BATCH_SIZE', 25))
    SUPPORTED_LANGUAGES = ['en', 'pt']

    # Temporary files
    TEMP_DIR = Path(os.getenv('TEMP_DIR', '/tmp'))

    # OpenSubtitles settings
    OPENSUBTITLES_USER_AGENT = 'Scriptum v2.1'

    # TMDB settings
    TMDB_LANGUAGE = 'pt-BR'

    # LegendasDivx API settings
    LEGENDASDIVX_API_URL = os.getenv('LEGENDASDIVX_API_URL', 'https://legendasdivx-api-315653817267.europe-west1.run.app')

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        warnings = []

        if not cls.TMDB_API_KEY:
            warnings.append('⚠️  TMDB_API_KEY not set - movie recognition disabled')

        if not cls.OPENSUBTITLES_API_KEY:
            warnings.append('⚠️  OPENSUBTITLES_API_KEY not set - subtitle search disabled')

        if not cls.GEMINI_API_KEY:
            warnings.append('⚠️  GEMINI_API_KEY not set - translation disabled')

        return warnings

# Create config instance
config = Config()
