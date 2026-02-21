#!/usr/bin/env python3
"""
Scriptum v2.0 - Configuration
Centralized configuration for all modules
"""

import os
from pathlib import Path

# ============================================================================
# Application Info
# ============================================================================
APP_NAME = "Scriptum Sync API"
APP_VERSION = "2.0"
APP_DESCRIPTION = "Subtitle synchronization and management service"

# ============================================================================
# Server Configuration
# ============================================================================
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001
DEBUG_MODE = True
THREADED = True

# ============================================================================
# API Keys & External Services
# ============================================================================
OPENSUBTITLES_API_KEY = os.getenv('OPENSUBTITLES_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '8d6d91941230817f7807d643736e8a49')  # Demo key

# ============================================================================
# File Processing
# ============================================================================
MAX_FILE_SIZE_MB = 500  # Maximum video file size in MB
SUPPORTED_VIDEO_FORMATS = [
    '.mp4', '.mkv', '.avi', '.webm', '.mov',
    '.flv', '.wmv', '.m4v', '.mpg', '.mpeg'
]
SUPPORTED_SUBTITLE_FORMATS = ['.srt']

# ============================================================================
# Synchronization Settings
# ============================================================================
SYNC_NUM_SAMPLES = 5  # Number of points to analyze across the video
SYNC_MAX_ITERATIONS = 5  # Maximum refinement iterations
SYNC_QUALITY_THRESHOLD = 0.3  # Seconds - offset threshold for "perfect" sync
SYNC_STDDEV_THRESHOLD = 0.5  # Standard deviation threshold

# ============================================================================
# Whisper/MLX Settings
# ============================================================================
WHISPER_MODEL = 'mlx-community/whisper-tiny'
AUDIO_SAMPLE_START = 60  # Start sampling at 60 seconds
AUDIO_SAMPLE_DURATION = 30  # Sample duration in seconds
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# ============================================================================
# Paths
# ============================================================================
BASE_DIR = Path(__file__).parent
TEMP_DIR = Path('/tmp')
LOG_FILE = TEMP_DIR / 'scriptum_sync.log'

# ============================================================================
# CORS Settings
# ============================================================================
CORS_ORIGINS = '*'  # Allow all origins for local development

# ============================================================================
# Error Messages
# ============================================================================
ERROR_MESSAGES = {
    'no_api_key': 'OpenSubtitles API key not found',
    'invalid_file': 'Invalid file format',
    'sync_failed': 'Synchronization failed',
    'download_failed': 'Subtitle download failed',
    'upload_failed': 'File upload failed',
}

# ============================================================================
# Success Messages
# ============================================================================
SUCCESS_MESSAGES = {
    'sync_complete': 'Synchronization completed successfully',
    'download_complete': 'Subtitle downloaded successfully',
    'upload_complete': 'File uploaded successfully',
}

# ============================================================================
# API Endpoints Info
# ============================================================================
ENDPOINTS = {
    'health': {
        'path': '/health',
        'methods': ['GET'],
        'description': 'Health check endpoint'
    },
    'sync': {
        'path': '/sync',
        'methods': ['POST'],
        'description': 'Synchronize subtitles with video'
    },
    'search_subtitles': {
        'path': '/search-subtitles',
        'methods': ['POST'],
        'description': 'Search for subtitles online'
    },
    'download_subtitle': {
        'path': '/download-subtitle',
        'methods': ['POST'],
        'description': 'Download subtitle file'
    },
    'recognize': {
        'path': '/recognize',
        'methods': ['POST'],
        'description': 'Recognize movie from filename'
    },
}

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'
