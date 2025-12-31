"""
ANSI color configuration using rich-click.

This module must be imported before any commands that use rich-click decorators.
"""

import os
import sys

import rich_click as click

# Configure rich-click for better help screens.
click.rich_click.USE_RICH_MARKUP = True  # Enable [cyan]colored[/] markup like this.


# Early color mode detection
# Parse --color flag from sys.argv before Click's argument validation
# This ensures error messages respect the color setting
def _detect_color_mode() -> str:
    """Detect color mode from CLI args or environment."""
    # Check environment variable first
    color = os.environ.get("COLOR", "auto")

    # Override with --color flag if present
    for i, arg in enumerate(sys.argv):
        if arg == "--color" and i + 1 < len(sys.argv):
            color = sys.argv[i + 1]
        elif arg.startswith("--color="):
            color = arg.split("=", 1)[1]

    return color


def _normalize_color_mode(color: str) -> str:
    """Normalize color mode aliases to canonical values."""
    if color == "always":
        return "rich"
    elif color == "never":
        return "plain"
    return color


# Configure rich-click's color system based on detected mode
_color_mode = _normalize_color_mode(_detect_color_mode())

if _color_mode == "plain":
    # No ANSI codes at all - disable color system entirely
    click.rich_click.COLOR_SYSTEM = None
elif _color_mode == "styled":
    # Bold/italic but no color (NO_COLOR compliant)
    # Note: Rich-click doesn't support "styles only" mode - it only has COLOR_SYSTEM
    # which controls both color and styles together. For help text, we fall back to
    # auto detection. The main console output will properly handle styled mode via
    # Rich's no_color=True setting in console.py.
    pass
elif _color_mode == "rich":
    # Force full color + style even if not a TTY
    click.rich_click.FORCE_TERMINAL = True
# else: "auto" - use Rich's default TTY detection
