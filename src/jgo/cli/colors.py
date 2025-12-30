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


# Configure rich-click's color system based on detected mode
_color_mode = _detect_color_mode()
if _color_mode == "never":
    # Disable color and fancy formatting in rich-click's console
    click.rich_click.COLOR_SYSTEM = None
    # Use ASCII box characters instead of Unicode when color is disabled
    # This ensures the output works on all terminals and avoids fancy formatting
    from rich import box

    click.rich_click.STYLE_ERRORS_PANEL_BOX = box.ASCII
    click.rich_click.STYLE_OPTIONS_PANEL_BOX = box.ASCII
    click.rich_click.STYLE_COMMANDS_PANEL_BOX = box.ASCII
    click.rich_click.STYLE_OPTIONS_TABLE_BOX = box.ASCII
    click.rich_click.STYLE_COMMANDS_TABLE_BOX = box.ASCII
elif _color_mode == "always":
    # Force color in rich-click's console
    click.rich_click.FORCE_TERMINAL = True
