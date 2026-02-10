"""
Input validation decorators and utilities.
Consolidates duplicate validation patterns across endpoints.
"""

from functools import wraps
from flask import request
from typing import List, Callable
from .responses import ApiResponse
from .logger import setup_logger

logger = setup_logger(__name__)


def require_files(*required_files: str) -> Callable:
    """
    Decorator to validate required files in request.

    Args:
        *required_files: Names of required file fields

    Returns:
        Decorated function

    Example:
        >>> @require_files('video', 'subtitle')
        >>> def sync_subtitles():
        >>>     video = request.files['video']
        >>>     subtitle = request.files['subtitle']
        >>>     ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            missing_files = []

            for file_key in required_files:
                if file_key not in request.files:
                    missing_files.append(file_key)
                elif not request.files[file_key].filename:
                    missing_files.append(file_key)

            if missing_files:
                logger.warning(f"Missing required files: {missing_files}")
                return ApiResponse.bad_request(
                    f"Missing required files: {', '.join(missing_files)}"
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_json(*required_fields: str) -> Callable:
    """
    Decorator to validate required JSON fields.

    Args:
        *required_fields: Names of required JSON fields

    Returns:
        Decorated function

    Example:
        >>> @require_json('query', 'language')
        >>> def search():
        >>>     data = request.get_json()
        >>>     query = data['query']
        >>>     ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()

            if not data:
                logger.warning("Missing JSON body")
                return ApiResponse.bad_request("Missing JSON body")

            missing_fields = []

            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)

            if missing_fields:
                logger.warning(f"Missing required fields: {missing_fields}")
                return ApiResponse.validation_error(
                    {field: "This field is required" for field in missing_fields}
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_file_extension(file_key: str, allowed_extensions: List[str]) -> Callable:
    """
    Decorator to validate file extensions.

    Args:
        file_key: Name of the file field to validate
        allowed_extensions: List of allowed extensions (without dots)

    Returns:
        Decorated function

    Example:
        >>> @validate_file_extension('subtitle', ['srt', 'vtt'])
        >>> def upload_subtitle():
        >>>     ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if file_key in request.files:
                file = request.files[file_key]
                if file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

                    if ext not in allowed_extensions:
                        logger.warning(f"Invalid file extension: {ext}")
                        return ApiResponse.bad_request(
                            f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
                        )

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_file_size(file_key: str, max_size_mb: int) -> Callable:
    """
    Decorator to validate file size.

    Args:
        file_key: Name of the file field to validate
        max_size_mb: Maximum file size in megabytes

    Returns:
        Decorated function

    Example:
        >>> @validate_file_size('video', 500)
        >>> def upload_video():
        >>>     ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if file_key in request.files:
                file = request.files[file_key]

                # Read file size
                file.seek(0, 2)  # Seek to end
                size = file.tell()
                file.seek(0)  # Reset to beginning

                max_bytes = max_size_mb * 1024 * 1024

                if size > max_bytes:
                    size_mb = size / (1024 * 1024)
                    logger.warning(f"File too large: {size_mb:.1f}MB > {max_size_mb}MB")
                    return ApiResponse.bad_request(
                        f"File too large ({size_mb:.1f}MB). Maximum: {max_size_mb}MB"
                    )

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename (only basename, no directory components)

    Example:
        >>> sanitize_filename("../../etc/passwd")
        'passwd'
        >>> sanitize_filename("normal_file.txt")
        'normal_file.txt'
    """
    from pathlib import Path
    import re

    # Remove directory components
    filename = Path(filename).name

    # Remove potentially dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)

    return filename


def validate_language_code(code: str) -> bool:
    """
    Validate language code format.

    Args:
        code: Language code (e.g., 'en', 'pt', 'pt-BR')

    Returns:
        True if valid format

    Example:
        >>> validate_language_code('en')
        True
        >>> validate_language_code('pt-BR')
        True
        >>> validate_language_code('invalid123')
        False
    """
    import re
    # ISO 639-1 (2 letters) or with region (2-2 letters)
    pattern = r'^[a-z]{2}(-[A-Z]{2})?$'
    return bool(re.match(pattern, code))
