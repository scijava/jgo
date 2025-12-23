"""
Config manager for jgo settings file paths and terminology.

Centralizes settings file path resolution and display name logic.
"""

from __future__ import annotations

from pathlib import Path

# Display names for user-facing messages
SETTINGS_FILE_DISPLAY_NAME = "jgo settings file"
LEGACY_SETTINGS_NAME = "~/.jgorc"


def get_settings_path(prefer_legacy: bool = False) -> Path:
    """
    Get the settings file path using XDG Base Directory standard.

    Args:
        prefer_legacy: If True, prefer ~/.jgorc even if XDG config exists

    Returns:
        Path to settings file:
        - If prefer_legacy is True: ~/.jgorc
        - Otherwise: ~/.config/jgo/config if it exists, else ~/.jgorc
    """
    xdg_config = Path.home() / ".config" / "jgo" / "config"
    legacy_config = Path.home() / ".jgorc"

    if prefer_legacy:
        return legacy_config

    return xdg_config if xdg_config.exists() else legacy_config


def get_settings_display_name(path: Path) -> str:
    """
    Get a user-friendly display name for a settings file path.

    Args:
        path: Path to settings file

    Returns:
        Display name for user-facing messages:
        - "~/.jgorc" if path is the legacy location
        - "~/.config/jgo/config" if path is the XDG location
        - Generic "jgo settings file" for other paths
    """
    legacy_config = Path.home() / ".jgorc"
    xdg_config = Path.home() / ".config" / "jgo" / "config"

    if path.resolve() == legacy_config.resolve():
        return LEGACY_SETTINGS_NAME
    elif path.resolve() == xdg_config.resolve():
        return "~/.config/jgo/config"
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
        >>> format_settings_message(Path.home() / ".config/jgo/config", "not found")
        "~/.config/jgo/config not found"
    """
    display_name = get_settings_display_name(path)
    return f"{display_name} {action}"
