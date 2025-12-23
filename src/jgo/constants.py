"""
Default constants for jgo.

Centralizes hardcoded paths and URLs to avoid duplication across the codebase.
"""

import os
from pathlib import Path

# Maven repository URLs
MAVEN_CENTRAL_URL = "https://repo.maven.apache.org/maven2"

# Settings file display names (these are truly constant)
SETTINGS_FILE_DISPLAY_NAME = "jgo settings file"
SETTINGS_FILE_LEGACY_NAME = "~/.jgorc"
SETTINGS_FILE_XDG_NAME = "~/.config/jgo.conf"


# Dynamic path functions (respect environment variables and HOME)
def default_maven_repo() -> Path:
    """
    Get default Maven repository path.

    Respects M2_REPO environment variable, otherwise uses ~/.m2/repository.
    """
    m2_repo = os.getenv("M2_REPO")
    if m2_repo:
        return Path(m2_repo)
    return Path.home() / ".m2" / "repository"


def default_jgo_cache() -> Path:
    """
    Get default jgo cache directory.

    Respects JGO_CACHE_DIR environment variable, otherwise uses ~/.cache/jgo.
    """
    cache_dir = os.getenv("JGO_CACHE_DIR")
    if cache_dir:
        return Path(cache_dir)
    return Path.home() / ".cache" / "jgo"


def xdg_settings_path() -> Path:
    """
    Get XDG settings file path.

    Respects XDG_CONFIG_HOME environment variable if set, otherwise uses ~/.config/jgo.conf.
    """
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "jgo.conf"
    return Path.home() / ".config" / "jgo.conf"


def legacy_settings_path() -> Path:
    """
    Get legacy settings file path (~/.jgorc).
    """
    return Path.home() / ".jgorc"


# Legacy constant-style access (for backward compatibility, will be removed in 3.0)
DEFAULT_MAVEN_REPO = default_maven_repo()
DEFAULT_JGO_CACHE = default_jgo_cache()
