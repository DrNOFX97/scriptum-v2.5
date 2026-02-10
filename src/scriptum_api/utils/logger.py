"""
Professional logging setup for Scriptum API.
Replaces print() statements with structured logging.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Configure a structured logger with consistent formatting.

    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string (uses default if None)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.error("Operation failed", exc_info=True)
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # Don't propagate to root logger

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Set formatter
    if format_string is None:
        format_string = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'

    formatter = logging.Formatter(
        format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds contextual information to log messages.

    Example:
        >>> logger = setup_logger(__name__)
        >>> adapter = LoggerAdapter(logger, {'request_id': '12345'})
        >>> adapter.info("Processing request")
        # Output: ... | request_id=12345 | Processing request
    """

    def process(self, msg, kwargs):
        """Add extra context to log messages."""
        if self.extra:
            extra_str = ' | '.join(f'{k}={v}' for k, v in self.extra.items())
            msg = f'{extra_str} | {msg}'
        return msg, kwargs
