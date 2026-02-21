#!/usr/bin/env python3
"""
Scriptum v2.0 - Utilities
Common utility functions used across modules
"""

import re
from pathlib import Path
from typing import Optional, Tuple


def extract_movie_name(filename: str) -> str:
    """
    Extract clean movie name from filename

    Args:
        filename: Video filename

    Returns:
        Cleaned movie name
    """
    # Remove extension
    clean_name = re.sub(r'\.(mp4|mkv|avi|webm|mov|flv|wmv)$', '', filename, flags=re.IGNORECASE)

    # Replace dots and underscores with spaces
    clean_name = re.sub(r'[\._]', ' ', clean_name)

    # Remove year and everything after
    clean_name = re.sub(r'\d{4}.*$', '', clean_name)

    # Remove quality indicators and codecs
    clean_name = re.sub(
        r'\b(720p|1080p|2160p|4K|BluRay|WEB-DL|HDTV|x264|x265|HEVC|AAC|DTS)\b.*',
        '',
        clean_name,
        flags=re.IGNORECASE
    )

    return clean_name.strip()


def extract_year_from_filename(filename: str) -> Optional[str]:
    """
    Extract year from filename if present

    Args:
        filename: Video filename

    Returns:
        Year as string or None
    """
    match = re.search(r'(19|20)\d{2}', filename)
    return match.group(0) if match else None


def format_file_size(bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def validate_video_file(filename: str, allowed_extensions: list) -> Tuple[bool, str]:
    """
    Validate if file is a supported video format

    Args:
        filename: File name to validate
        allowed_extensions: List of allowed extensions

    Returns:
        Tuple of (is_valid, error_message)
    """
    ext = Path(filename).suffix.lower()

    if not ext:
        return False, "File has no extension"

    if ext not in allowed_extensions:
        return False, f"Unsupported format: {ext}"

    return True, ""


def validate_subtitle_file(filename: str) -> Tuple[bool, str]:
    """
    Validate if file is a supported subtitle format

    Args:
        filename: File name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    ext = Path(filename).suffix.lower()

    if ext != '.srt':
        return False, f"Only .srt format supported, got: {ext}"

    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system operations

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length
    if len(filename) > 255:
        name, ext = Path(filename).stem, Path(filename).suffix
        filename = name[:255-len(ext)] + ext

    return filename


def parse_framerate(fps_string: str) -> float:
    """
    Parse framerate from various formats

    Args:
        fps_string: Framerate string (e.g., "24000/1001", "23.976", "24")

    Returns:
        Framerate as float
    """
    if '/' in fps_string:
        num, den = map(int, fps_string.split('/'))
        return round(num / den, 3)
    return float(fps_string)


def calculate_sync_quality(offset: float, std_dev: float) -> str:
    """
    Calculate sync quality based on offset and standard deviation

    Args:
        offset: Average offset in seconds
        std_dev: Standard deviation of offsets

    Returns:
        Quality string: PERFEITO, BOM, MÉDIO, FRACO
    """
    if abs(offset) < 0.3 and std_dev < 0.5:
        return "PERFEITO"
    elif abs(offset) < 0.8 and std_dev < 1.0:
        return "BOM"
    elif abs(offset) < 2.0 and std_dev < 2.0:
        return "MÉDIO"
    else:
        return "FRACO"


def get_file_hash(filepath: Path, chunk_size: int = 65536) -> str:
    """
    Calculate file hash for comparison

    Args:
        filepath: Path to file
        chunk_size: Size of chunks to read

    Returns:
        Hex digest of file hash
    """
    import hashlib

    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()
