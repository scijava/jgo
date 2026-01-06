"""
Default constants for jgo.

Centralizes hardcoded paths and URLs to avoid duplication across the codebase.
"""

import os
from pathlib import Path

from .util.platform import get_user_home


def _get_version() -> str:
    """Get jgo version from package metadata."""
    try:
        # Try importlib.metadata (Python 3.8+)
        from importlib.metadata import version

        return version("jgo")
    except Exception:
        # Fallback: read from pyproject.toml
        try:
            from .util.toml import tomllib

            pyproject = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject.exists():
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    return data.get("project", {}).get("version", "unknown")
        except Exception:
            pass
        return "unknown"


# Package version
VERSION = _get_version()

# Maven repository URLs
MAVEN_CENTRAL_URL = "https://repo.maven.apache.org/maven2"

# Settings file display names (these are truly constant)
SETTINGS_FILE_DISPLAY_NAME = "jgo settings file"
SETTINGS_FILE_XDG_NAME = "~/.config/jgo.conf"
SETTINGS_FILE_LEGACY_NAME = "~/.jgorc"


# Dynamic path functions (respect environment variables and HOME)
def default_maven_repo() -> Path:
    """
    Get default Maven repository path.

    Respects M2_REPO environment variable, otherwise uses ~/.m2/repository.
    """
    m2_repo = os.getenv("M2_REPO")
    if m2_repo:
        return Path(m2_repo)
    return get_user_home() / ".m2" / "repository"


def default_jgo_cache() -> Path:
    """
    Get default jgo cache directory.

    Respects JGO_CACHE_DIR environment variable, otherwise uses ~/.cache/jgo.
    """
    cache_dir = os.getenv("JGO_CACHE_DIR")
    if cache_dir:
        return Path(cache_dir)
    return get_user_home() / ".cache" / "jgo"


def xdg_settings_path() -> Path:
    """
    Get XDG settings file path.

    Respects XDG_CONFIG_HOME environment variable if set, otherwise uses ~/.config/jgo.conf.
    """
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "jgo.conf"
    return get_user_home() / ".config" / "jgo.conf"


def legacy_settings_path() -> Path:
    """
    Get legacy settings file path (~/.jgorc).
    """
    return get_user_home() / ".jgorc"


# Legacy constant-style access (for backward compatibility, will be removed in 3.0)
DEFAULT_MAVEN_REPO = default_maven_repo()
DEFAULT_JGO_CACHE = default_jgo_cache()
