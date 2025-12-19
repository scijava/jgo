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

# Config file paths
XDG_CONFIG_PATH = Path.home() / ".config" / "jgo" / "config"
LEGACY_CONFIG_PATH = Path.home() / ".jgorc"
