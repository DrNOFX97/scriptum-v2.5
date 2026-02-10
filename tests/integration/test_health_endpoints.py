"""
Integration tests for health check endpoints.
"""

import pytest


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')

    assert response.status_code == 200

    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'version' in data
    assert 'service' in data


def test_diagnostics(client):
    """Test diagnostics endpoint."""
    response = client.get('/diagnostics')

    assert response.status_code == 200

    data = response.get_json()
    assert 'warnings' in data
    assert 'keys' in data

    # Check keys structure
    keys = data['keys']
    assert 'tmdb' in keys
    assert 'opensubtitles' in keys
    assert 'gemini' in keys

    # Values should be booleans
    assert isinstance(keys['tmdb'], bool)
    assert isinstance(keys['opensubtitles'], bool)
    assert isinstance(keys['gemini'], bool)
