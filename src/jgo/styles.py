"""Presentation styles for jgo output formatting.

This module provides centralized style definitions and formatting functions
for consistent Rich markup across all jgo commands and output.
"""

from __future__ import annotations

import logging

_log = logging.getLogger(__name__)


# Style mappings for coordinate components and punctuation
STYLES = {
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
        '[bold cyan]org.foo[/][dim]:[/][bold]bar[/]'

        >>> styled("g:a:v!", g="org.foo", a="bar", v="1.0")
        '[bold cyan]org.foo[/][dim]:[/][bold]bar[/][dim]:[/][green]1.0[/][dim]![/]'
    """
    result = ""
    for char in template:
        style = styles.get(char)
        value = values.get(char, char)  # Use value if provided, else literal char
        result += f"[{style}]{value}[/]" if style else value

    return result


def format_tokens(
    tokens: list[tuple[str | None, str]], separator: str = ":", styles: dict = STYLES
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
        '[bold cyan]org.foo[/][dim]:[/][bold]bar[/]'

        >>> format_tokens([("org.foo", "g"), ("bar", "a"), ("1.0", "v")])
        '[bold cyan]org.foo[/][dim]:[/][bold]bar[/][dim]:[/][green]1.0[/]'
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
