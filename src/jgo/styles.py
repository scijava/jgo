"""Presentation styles for jgo output formatting.

This module provides centralized style definitions and formatting functions
for consistent Rich markup across all jgo commands and output.

Styles can be customized via the [styles] section in jgo.conf (typically at
~/.config/jgo.conf). Built-in defaults are used if no config file is present
or if specific style keys are not defined.

## Available Styles

### Coordinate Components
- g, a, v, p, c, s - Maven coordinate components (groupId, artifactId, etc.)
- :, ! - Structural elements (separator, raw flag)
- optional, placement - Special markers

### Semantic UI Styles
- error - Error messages
- critical - Critical missing items
- warning - Moderate warnings
- filename - File paths and config names
- header - Section headers
- syntax - Command syntax and special chars
- action - Action verbs and operations
- secondary - Tips, defaults, optional info
- domain - Maven domain concepts

## Helper Functions

Use these functions to apply consistent formatting:
- error(text) - Error messages with prefix
- critical(text) - Critical messages
- warning(text) - Warning messages
- filepath(text) - File paths
- header(text) - Section headers
- syntax(text) - Command syntax
- action(text) - Action verbs
- secondary(text) - Secondary info
- domain(text) - Maven concepts
- tip(message) - Tips with prefix

## Pre-formatted Constants

For Click help text and output:
- JGO_TOML, JGO_LOCK_TOML, JGO_CONF_GLOBAL - Config file names
- PLUS_OPERATOR, AT_MAINCLASS, DOUBLE_DASH - Syntax elements
- MAVEN_COORDINATES, MAVEN_REPOSITORIES - Maven terminology
- TIP_DRY_RUN - Common tip text
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
    # Semantic UI styles
    "error": "red",  # Error messages
    "critical": "red",  # Critical missing items
    "warning": "yellow",  # Moderate warnings
    "filename": "cyan",  # File paths and config names
    "header": "bold cyan",  # Section headers
    "syntax": "yellow",  # Command syntax and special chars
    "action": "green",  # Action verbs and operations
    "secondary": "dim",  # Tips, defaults, optional info
    "domain": "magenta",  # Maven domain concepts
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


# Semantic formatting helper functions
def error(text: str) -> str:
    """Format error message with styled Error: prefix."""
    return f"[{STYLES['error']}]Error:[/] {text}"


def critical(text: str) -> str:
    """Format critical message (e.g., 'No JARs found')."""
    return f"[{STYLES['critical']}]{text}[/]"


def warning(text: str) -> str:
    """Format warning message."""
    return f"[{STYLES['warning']}]{text}[/]"


def filepath(text: str) -> str:
    """Format file path or config name."""
    return f"[{STYLES['filename']}]{text}[/]"


def header(text: str) -> str:
    """Format section header."""
    return f"[{STYLES['header']}]{text}[/]"


def syntax(text: str) -> str:
    """Format command syntax or special operator."""
    return f"[{STYLES['syntax']}]{text}[/]"


def action(text: str) -> str:
    """Format action verb."""
    return f"[{STYLES['action']}]{text}[/]"


def secondary(text: str) -> str:
    """Format secondary/optional information."""
    return f"[{STYLES['secondary']}]{text}[/]"


def domain(text: str) -> str:
    """Format Maven domain concept."""
    return f"[{STYLES['domain']}]{text}[/]"


def tip(message: str) -> str:
    """Format tip with styled TIP: prefix."""
    return f"[{STYLES['secondary']}]TIP: {message}[/]"


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

# Common file references - evaluated after STYLES is loaded
JGO_TOML = filepath("jgo.toml")
JGO_LOCK_TOML = filepath("jgo.lock.toml")
JGO_CONF_GLOBAL = filepath("~/.config/jgo.conf")

# Common syntax elements
PLUS_OPERATOR = syntax("+")
AT_MAINCLASS = syntax("@MainClass")
DOUBLE_DASH = syntax("--")

# Maven terminology
MAVEN_COORDINATES = domain("Maven coordinates")
MAVEN_REPOSITORIES = domain("Maven repositories")

# Common help text fragments
TIP_DRY_RUN = tip(
    f"Use {syntax('jgo --dry-run run')} to see the command without executing it."
)
