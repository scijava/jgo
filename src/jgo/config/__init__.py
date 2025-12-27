"""
Configuration module for jgo.

Provides global settings file parsing and defaults management.
"""

from .settings import GlobalSettings

# Backward compatibility alias
JgoConfig = GlobalSettings

__all__ = [
    "GlobalSettings",
    "JgoConfig",  # Deprecated, use GlobalSettings
]
