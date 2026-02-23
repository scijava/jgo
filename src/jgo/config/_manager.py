"""
Config manager for jgo settings file paths and terminology.

Centralizes settings file path resolution and display name logic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..constants import (
    SETTINGS_FILE_DISPLAY_NAME,
    SETTINGS_FILE_LEGACY_NAME,
    SETTINGS_FILE_XDG_NAME,
    legacy_settings_path,
    xdg_settings_path,
)

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pathlib import Path


def get_settings_path() -> Path:
    """
    Get the settings file path using XDG Base Directory standard.

    Returns:
        Path to settings file with the following precedence:
        - ~/.config/jgo.conf if it exists (preferred location)
        - ~/.jgorc if it exists (legacy backward compatibility)
        - ~/.config/jgo.conf otherwise (default for new installations)
    """
    xdg_path = xdg_settings_path()
    legacy_path = legacy_settings_path()

    _log.debug(f"XDG settings path: {xdg_path} (exists={xdg_path.exists()})")
    _log.debug(f"Legacy settings path: {legacy_path} (exists={legacy_path.exists()})")

    # Prefer XDG if it exists
    if xdg_path.exists():
        _log.debug(f"Using XDG settings file: {xdg_path}")
        return xdg_path

    # Fall back to legacy if it exists (backward compatibility)
    if legacy_path.exists():
        _log.debug(f"Using legacy settings file: {legacy_path}")
        return legacy_path

    # Default to XDG for new installations
    _log.debug(f"Using default XDG settings path: {xdg_path}")
    return xdg_path


def get_settings_display_name(path: Path) -> str:
    """
    Get a user-friendly display name for a settings file path.

    Args:
        path: Path to settings file

    Returns:
        Display name for user-facing messages:
        - "~/.config/jgo.conf" if path is the XDG location
        - "~/.jgorc" if path is the legacy location
        - Generic "jgo settings file" for other paths
    """
    if path.resolve() == xdg_settings_path().resolve():
        return SETTINGS_FILE_XDG_NAME
    if path.resolve() == legacy_settings_path().resolve():
        return SETTINGS_FILE_LEGACY_NAME
    return SETTINGS_FILE_DISPLAY_NAME


def format_settings_message(path: Path, action: str) -> str:
    """
    Format a user-facing message about a settings file operation.

    Args:
        path: Path to settings file
        action: Description of the action (e.g., "created", "updated", "not found")

    Returns:
        Formatted message string

    Example:
        >>> format_settings_message(Path.home() / ".config/jgo.conf", "not found")
        "~/.config/jgo.conf not found"
    """
    display_name = get_settings_display_name(path)
    return f"{display_name} {action}"
