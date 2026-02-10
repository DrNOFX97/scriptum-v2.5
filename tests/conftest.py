"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scriptum_api.app import create_app
from scriptum_api.config import Config
from scriptum_api.dependencies import ServiceContainer


@pytest.fixture
def test_config():
    """Create test configuration."""
    config = Config()
    config.DEBUG = True
    config.TESTING = True
    return config


@pytest.fixture
def app(test_config):
    """Create Flask test app."""
    app = create_app(test_config)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_video_service():
    """Mock VideoService."""
    service = Mock()
    service.get_video_info.return_value = {
        'filename': 'test.mp4',
        'codec': 'h264',
        'format': 'mp4',
        'resolution': '1080p',
        'width': 1920,
        'height': 1080,
        'fps': 24.0,
        'duration': 120.5,
        'duration_formatted': '02:00',
        'size_mb': 150.5
    }
    service.can_remux_to_mp4.return_value = True
    return service


@pytest.fixture
def mock_movie_service():
    """Mock MovieService."""
    service = Mock()
    service.search_movie.return_value = {
        'success': True,
        'movie': {
            'id': 12345,
            'title': 'Test Movie',
            'year': '2024',
            'rating': 8.5,
            'overview': 'Test overview',
            'poster': 'https://example.com/poster.jpg'
        }
    }
    return service


@pytest.fixture
def mock_subtitle_service():
    """Mock SubtitleService."""
    service = Mock()
    service.search_subtitles.return_value = [
        {
            'id': '1',
            'name': 'Test Subtitle',
            'language': 'pt',
            'downloads': 1000,
            'rating': 9.0
        }
    ]
    service.download_subtitle.return_value = b'Subtitle content'
    return service


@pytest.fixture
def mock_translation_service():
    """Mock TranslationService."""
    service = Mock()
    service.translate_file.return_value = True
    return service


@pytest.fixture
def mock_sync_service():
    """Mock SyncService."""
    service = Mock()
    service.sync_subtitles.return_value = {
        'success': True,
        'offset': 2.5,
        'quality': 0.85
    }
    return service


@pytest.fixture
def mock_services(
    mock_video_service,
    mock_movie_service,
    mock_subtitle_service,
    mock_translation_service,
    mock_sync_service
):
    """Create mock service container."""
    services = Mock(spec=ServiceContainer)
    services.video_service = mock_video_service
    services.movie_service = mock_movie_service
    services.subtitle_service = mock_subtitle_service
    services.translation_service = mock_translation_service
    services.sync_service = mock_sync_service
    services.legendasdivx_service = Mock()
    return services


@pytest.fixture
def temp_file(tmp_path):
    """Create temporary file for testing."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")
    return file_path


@pytest.fixture
def temp_video(tmp_path):
    """Create temporary video file path."""
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b'fake video content')
    return video_path


@pytest.fixture
def temp_subtitle(tmp_path):
    """Create temporary subtitle file."""
    subtitle_path = tmp_path / "test_subtitle.srt"
    subtitle_content = """1
00:00:01,000 --> 00:00:03,000
Test subtitle line 1

2
00:00:04,000 --> 00:00:06,000
Test subtitle line 2
"""
    subtitle_path.write_text(subtitle_content)
    return subtitle_path
