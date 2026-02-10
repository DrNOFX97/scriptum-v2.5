"""
Scriptum API - Professional subtitle management backend.

This package provides a Flask-based API for:
- Video analysis and conversion
- Subtitle search, sync, and translation
- Movie recognition and metadata
"""

__version__ = '2.5.0'
__author__ = 'Scriptum Team'

from .config import Config
from .dependencies import ServiceContainer, create_services

__all__ = ['Config', 'ServiceContainer', 'create_services']
