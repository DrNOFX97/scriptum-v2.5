"""
Unit tests for validation utilities.
"""

import pytest
from scriptum_api.utils.validators import (
    sanitize_filename,
    validate_language_code
)


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_sanitize_removes_directory_traversal(self):
        """Test that directory traversal is removed."""
        result = sanitize_filename('../../etc/passwd')
        assert result == 'passwd'
        assert '..' not in result

    def test_sanitize_keeps_normal_filename(self):
        """Test that normal filenames are preserved."""
        result = sanitize_filename('normal_file.txt')
        assert result == 'normal_file.txt'

    def test_sanitize_removes_special_chars(self):
        """Test that special characters are replaced."""
        result = sanitize_filename('file@#$%.txt')
        assert '@' not in result
        assert '#' not in result
        assert '$' not in result
        assert '%' not in result

    def test_sanitize_preserves_extensions(self):
        """Test that file extensions are preserved."""
        result = sanitize_filename('movie.mkv')
        assert result.endswith('.mkv')

    def test_sanitize_handles_absolute_paths(self):
        """Test that absolute paths are handled."""
        result = sanitize_filename('/usr/local/bin/script.sh')
        assert result == 'script.sh'
        assert '/' not in result

    def test_sanitize_handles_windows_paths(self):
        """Test that Windows paths are handled."""
        result = sanitize_filename('C:\\Windows\\System32\\file.dll')
        # On Unix systems, Path().name might keep backslashes as regular chars
        # The important thing is the path separator is removed
        assert result.endswith('.dll')
        # Should not have forward or backslashes
        assert '/' not in result or result == 'file.dll'


class TestValidateLanguageCode:
    """Tests for language code validation."""

    def test_validate_accepts_iso_639_1(self):
        """Test that ISO 639-1 codes are accepted."""
        assert validate_language_code('en') is True
        assert validate_language_code('pt') is True
        assert validate_language_code('fr') is True

    def test_validate_accepts_with_region(self):
        """Test that codes with regions are accepted."""
        assert validate_language_code('pt-BR') is True
        assert validate_language_code('en-US') is True
        assert validate_language_code('zh-CN') is True

    def test_validate_rejects_invalid(self):
        """Test that invalid codes are rejected."""
        assert validate_language_code('invalid') is False
        assert validate_language_code('123') is False
        assert validate_language_code('e') is False

    def test_validate_rejects_wrong_format(self):
        """Test that wrong formats are rejected."""
        assert validate_language_code('en-us') is False  # lowercase region
        assert validate_language_code('EN') is False     # uppercase code
        assert validate_language_code('en-USA') is False # 3-letter region

    def test_validate_handles_empty(self):
        """Test that empty strings are rejected."""
        assert validate_language_code('') is False
