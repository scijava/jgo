"""
Configuration module for jgo.

Provides global settings file parsing and defaults management.
"""

from ._manager import get_settings_path
from ._settings import GlobalSettings, parse_config_key

__all__ = [
    # manager
    "get_settings_path",
    # settings
    "GlobalSettings",
    "parse_config_key",
]
