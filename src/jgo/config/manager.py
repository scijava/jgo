"""
Config manager for jgo settings file paths and terminology.

Centralizes settings file path resolution and display name logic.
"""

from __future__ import annotations

from pathlib import Path

from ..constants import (
    SETTINGS_FILE_DISPLAY_NAME,
    SETTINGS_FILE_LEGACY_NAME,
    SETTINGS_FILE_XDG_NAME,
    legacy_settings_path,
    xdg_settings_path,
)


def get_settings_path() -> Path:
    """
    Get the settings file path using XDG Base Directory standard.

    Returns:
        Path to settings file:
        - ~/.config/jgo.conf if it exists, else ~/.jgorc
    """
    xdg_path = xdg_settings_path()
    return xdg_path if xdg_path.exists() else legacy_settings_path()


def get_settings_display_name(path: Path) -> str:
    """
    Get a user-friendly display name for a settings file path.

    Args:
        path: Path to settings file

    Returns:
        Display name for user-facing messages:
        - "~/.jgorc" if path is the legacy location
        - "~/.config/jgo.conf" if path is the XDG location
        - Generic "jgo settings file" for other paths
    """
    if path.resolve() == legacy_settings_path().resolve():
        return SETTINGS_FILE_LEGACY_NAME
    elif path.resolve() == xdg_settings_path().resolve():
        return SETTINGS_FILE_XDG_NAME
    else:
        return SETTINGS_FILE_DISPLAY_NAME


def format_settings_message(path: Path, action: str) -> str:
    """
    Format a user-facing message about a settings file operation.

    Args:
        path: Path to settings file
        action: Description of the action (e.g., "created", "updated", "not found")

    Returns:
        Formatted message string

    Examples:
        >>> format_settings_message(Path.home() / ".jgorc", "created")
        "~/.jgorc created"
        >>> format_settings_message(Path.home() / ".config/jgo.conf", "not found")
        "~/.config/jgo.conf not found"
    """
    display_name = get_settings_display_name(path)
    return f"{display_name} {action}"
