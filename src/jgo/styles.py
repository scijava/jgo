"""Presentation styles for jgo output formatting.

This module provides centralized style definitions and formatting functions
for consistent Rich markup across all jgo commands and output.

Styles can be customized via the [styles] section in jgo.conf (typically at
~/.config/jgo.conf). Built-in defaults are used if no config file is present
or if specific style keys are not defined.
"""

from __future__ import annotations

import logging
import sys

_log = logging.getLogger(__name__)


# Built-in default styles for coordinate components and punctuation
DEFAULT_STYLES: dict[str, str | None] = {
    # Maven coordinate components
    # Visual hierarchy: a > v > c > g > s > p
    "g": "cyan",  # groupId - organizational context
    "a": "bold",  # artifactId - maximum visibility
    "v": "bright_green",  # version - highly visible, positive semantic
    "p": None,  # packaging - de-emphasize (usually just "jar")
    "c": "yellow",  # classifier - attention-grabbing for variants
    "s": "blue",  # scope - contextual metadata
    # Structural elements
    ":": "dim",  # colon separator
    "!": "dim",  # raw/unmanaged flag
    # Special markers
    "optional": "dim",  # (optional) marker
    "placement": "dim",  # (c)/(m) placement markers
}


def _load_style_settings() -> dict[str, str]:
    """
    Load style settings from jgo config file.

    Attempts to read the [styles] section from jgo.conf. Returns an empty
    dictionary if the config file doesn't exist or cannot be read.

    Returns:
        Dictionary of styles (key -> Rich color/style name)
    """
    styles: dict[str, str] = {}

    try:
        from .config.manager import get_settings_path

        config_file = get_settings_path()
        if config_file.exists():
            from configparser import ConfigParser

            parser = ConfigParser()
            parser.read(config_file)
            if parser.has_section("styles"):
                config_styles = dict(parser.items("styles"))
                styles.update(config_styles)
    except Exception as e:
        # If anything fails, proceed gracefully
        # (most common: config file doesn't exist)
        _log.debug(f"Failed to load style settings: {e}")

    return styles


STYLES: dict[str, str | None] = {}


def load_styles(ignore_config: bool = False) -> None:
    """
    Load styles from config, optionally ignoring the config file.

    This can be called at runtime to refresh styles if needed.
    Most commonly, this is used internally to load initial style settings.

    Args:
        ignore_config: If True, use DEFAULT_STYLES. If False, load from config.
    """
    global STYLES
    STYLES = dict(DEFAULT_STYLES)
    if not ignore_config:
        STYLES.update(_load_style_settings())


# Load styles at import time (can be refreshed by calling load_styles())
load_styles(ignore_config="--ignore-config" in sys.argv)


def styled(template: str, styles: dict = STYLES, **values) -> str:
    """
    Format a template string with Rich markup for colored output.

    Applies styles from STYLES dict to single-character placeholders
    in the template. Values not in STYLES are rendered without markup.

    Args:
        template: Template with placeholders (e.g., "g:a:v")
        styles: Style mapping dict (defaults to STYLES)
        **values: Values to substitute (e.g., g="org.foo", a="bar")

    Returns:
        Formatted string with Rich markup

    Examples:
        >>> styled("g:a", g="org.foo", a="bar")
        '[cyan]org.foo[/][dim]:[/][bold]bar[/]'

        >>> styled("g:a:v!", g="org.foo", a="bar", v="1.0")
        '[cyan]org.foo[/][dim]:[/][bold]bar[/][dim]:[/][bright_green]1.0[/][dim]![/]'
    """
    result = ""
    for char in template:
        style = styles.get(char)
        value = values.get(char, char)  # Use value if provided, else literal char
        result += f"[{style}]{value}[/]" if style else value

    return result


def format_tokens(
    tokens: list[tuple[str | None, str]],
    separator: str = ":",
    styles: dict = STYLES,
) -> str:
    """
    Format a list of (value, style_key) tuples, skipping falsy values.

    Args:
        tokens: List of (value, style_key) tuples. Falsy values are skipped.
        separator: String to join tokens with (default ":")
        styles: Style mapping dict (defaults to STYLES)

    Returns:
        Formatted string with Rich markup, omitting falsy values

    Examples:
        >>> format_tokens([("org.foo", "g"), ("bar", "a"), (None, "v")])
        '[cyan]org.foo[/][dim]:[/][bold]bar[/]'

        >>> format_tokens([("org.foo", "g"), ("bar", "a"), ("1.0", "v")])
        '[cyan]org.foo[/][dim]:[/][bold]bar[/][dim]:[/][bright_green]1.0[/]'
    """
    sep_style = styles.get(separator)
    styled_sep = f"[{sep_style}]{separator}[/]" if sep_style else separator

    parts = []
    for value, style_key in tokens:
        if value:  # Skip None, empty string, etc.
            style = styles.get(style_key)
            parts.append(f"[{style}]{value}[/]" if style else value)

    return styled_sep.join(parts)


# Help text templates - pre-formatted for rich-click decorators
COORD_HELP_SHORT = styled("g:a:v", g="g", a="a", v="v")
COORD_HELP_FULL = (
    styled("g:a", g="groupId", a="artifactId")
    + f"[{STYLES[':']}]:[[/]"
    + styled("v", v="version")
    + f"[{STYLES[':']}]:[[/]"
    + styled("c", c="classifier")
    + f"[{STYLES[':']}]][/]"
)
