"""
Centralized constants for the Scriptum API.
Extracts magic numbers and repeated values for better maintainability.
"""

# ============================================================================
# API Timeouts (in seconds)
# ============================================================================
API_TIMEOUT_SHORT = 10   # For quick requests (health checks, simple queries)
API_TIMEOUT_MEDIUM = 30  # For standard API calls (search, metadata)
API_TIMEOUT_LONG = 60    # For heavy operations (downloads, processing)

# ============================================================================
# Processing Limits
# ============================================================================
BATCH_SIZE = 10  # Number of items to process in a single batch
MAX_RETRIES = 3  # Maximum number of retry attempts for failed operations
RETRY_DELAY_MS = 2000  # Delay between retries in milliseconds

# ============================================================================
# Subtitle Validation
# ============================================================================
MAX_LINE_LENGTH = 42  # Maximum characters per subtitle line
MAX_SUBTITLE_SIZE_MB = 10  # Maximum subtitle file size in megabytes
MIN_SUBTITLE_DURATION_MS = 500  # Minimum subtitle display duration

# ============================================================================
# Sync Quality Thresholds
# ============================================================================
SYNC_QUALITY_THRESHOLD_LOW = 0.3   # Minimum acceptable sync quality
SYNC_QUALITY_THRESHOLD_HIGH = 0.5  # Good sync quality threshold
SYNC_QUALITY_EXCELLENT = 0.7       # Excellent sync quality
MAX_SYNC_ITERATIONS = 5            # Maximum sync refinement iterations
SYNC_OFFSET_TOLERANCE_MS = 100     # Tolerance for sync offset in milliseconds

# ============================================================================
# Video Processing
# ============================================================================
SUPPORTED_VIDEO_FORMATS = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv']
SUPPORTED_SUBTITLE_FORMATS = ['srt', 'ass', 'ssa', 'sub', 'vtt']
VIDEO_SAMPLE_DURATION_SEC = 60  # Duration to sample for analysis

# ============================================================================
# Language Fallback Priorities
# ============================================================================
# When a translation is not available, try these languages in order
LANGUAGE_FALLBACK = {
    'pt': ['pt', 'pt-PT', 'pt-BR', 'es', 'it', 'fr', 'en'],
    'pt-PT': ['pt-PT', 'pt', 'pt-BR', 'es', 'it', 'fr', 'en'],
    'pt-BR': ['pt-BR', 'pt', 'pt-PT', 'es', 'it', 'fr', 'en'],
    'es': ['es', 'pt', 'it', 'fr', 'en'],
    'es-ES': ['es-ES', 'es', 'pt', 'it', 'fr', 'en'],
    'es-MX': ['es-MX', 'es', 'pt', 'it', 'fr', 'en'],
    'it': ['it', 'es', 'pt', 'fr', 'en'],
    'fr': ['fr', 'es', 'pt', 'it', 'en'],
    'en': ['en', 'en-US', 'en-GB'],
    'en-US': ['en-US', 'en', 'en-GB'],
    'en-GB': ['en-GB', 'en', 'en-US'],
    'de': ['de', 'en', 'fr'],
    'ru': ['ru', 'en'],
    'ja': ['ja', 'en'],
    'ko': ['ko', 'en'],
    'zh': ['zh', 'zh-CN', 'zh-TW', 'en'],
}

# ============================================================================
# Translation Settings
# ============================================================================
TRANSLATION_CHUNK_SIZE = 50  # Number of subtitle entries per translation batch
TRANSLATION_QUALITY_CHECK = True  # Whether to validate translation output
MIN_TRANSLATION_CONFIDENCE = 0.6  # Minimum confidence score for translations

# ============================================================================
# Cache Settings
# ============================================================================
CACHE_DURATION_SHORT_SEC = 300   # 5 minutes - for volatile data
CACHE_DURATION_MEDIUM_SEC = 3600  # 1 hour - for semi-stable data
CACHE_DURATION_LONG_SEC = 86400   # 24 hours - for stable data

# ============================================================================
# Rate Limiting
# ============================================================================
RATE_LIMIT_PER_MINUTE = 30   # Maximum requests per minute per endpoint
RATE_LIMIT_PER_HOUR = 200    # Maximum requests per hour
RATE_LIMIT_PER_DAY = 2000    # Maximum requests per day

# ============================================================================
# File Management
# ============================================================================
UPLOAD_MAX_SIZE_MB = 500  # Maximum upload file size
UPLOAD_RETENTION_HOURS = 24  # How long to keep uploaded files
CLEANUP_INTERVAL_HOURS = 1  # How often to run file cleanup

# ============================================================================
# API Response Defaults
# ============================================================================
DEFAULT_PAGE_SIZE = 20  # Default number of results per page
MAX_PAGE_SIZE = 100     # Maximum allowed results per page
DEFAULT_LANGUAGE = 'pt'  # Default language for operations

# ============================================================================
# External API Keys (Environment Variable Names)
# ============================================================================
ENV_TMDB_API_KEY = 'TMDB_API_KEY'
ENV_OPENSUBTITLES_API_KEY = 'OPENSUBTITLES_API_KEY'
ENV_GEMINI_API_KEY = 'GEMINI_API_KEY'
ENV_OPENSUBTITLES_USER_AGENT = 'OPENSUBTITLES_USER_AGENT'

# ============================================================================
# HTTP Status Codes (for consistency)
# ============================================================================
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_INTERNAL_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503
