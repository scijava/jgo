"""
Default constants for jgo.

Centralizes hardcoded paths and URLs to avoid duplication across the codebase.
"""

from pathlib import Path

# Maven repository URLs
MAVEN_CENTRAL_URL = "https://repo.maven.apache.org/maven2"

# Default local paths
DEFAULT_MAVEN_REPO = Path.home() / ".m2" / "repository"
DEFAULT_JGO_CACHE = Path.home() / ".cache" / "jgo"

# Settings file paths
XDG_SETTINGS_PATH = Path.home() / ".config" / "jgo" / "config"
LEGACY_SETTINGS_PATH = Path.home() / ".jgorc"

# Legacy aliases for backward compatibility
XDG_CONFIG_PATH = XDG_SETTINGS_PATH
LEGACY_CONFIG_PATH = LEGACY_SETTINGS_PATH

# Settings file display names
SETTINGS_FILE_DISPLAY_NAME = "jgo settings file"
SETTINGS_FILE_LEGACY_NAME = "~/.jgorc"
