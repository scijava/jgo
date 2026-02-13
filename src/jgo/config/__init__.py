"""
Configuration module for jgo.

Provides global settings file parsing and defaults management.
"""

from .manager import get_settings_path
from .settings import GlobalSettings, parse_config_key

__all__ = [
    # manager
    "get_settings_path",
    # settings
    "GlobalSettings",
    "parse_config_key",
]
