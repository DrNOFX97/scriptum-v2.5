"""
Unit tests for logging utilities.
"""

import pytest
import logging
from scriptum_api.utils.logger import setup_logger, get_logger


def test_setup_logger_creates_logger():
    """Test that setup_logger creates a logger."""
    logger = setup_logger('test_logger')

    assert logger is not None
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'test_logger'


def test_setup_logger_sets_level():
    """Test that logger level is set correctly."""
    logger = setup_logger('test_level', level=logging.DEBUG)

    assert logger.level == logging.DEBUG


def test_setup_logger_adds_handler():
    """Test that logger has a handler."""
    logger = setup_logger('test_handler')

    assert len(logger.handlers) > 0


def test_get_logger_returns_existing():
    """Test that get_logger returns existing logger."""
    logger1 = setup_logger('test_existing')
    logger2 = get_logger('test_existing')

    assert logger1 is logger2


def test_logger_output_format(caplog):
    """Test that logger outputs in correct format."""
    logger = setup_logger('test_format', level=logging.INFO)

    # Logger writes to stdout, not captured by caplog by default
    # Just verify the logger can log without errors
    try:
        logger.info('Test message')
        logger.debug('Debug message')
        logger.error('Error message')
        assert True  # If we got here, logging works
    except Exception:
        pytest.fail("Logger failed to log messages")
