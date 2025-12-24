"""
ANSI color configuration using rich-click.

This module must be imported before any commands that use rich-click decorators.
"""

import rich_click as click

# Configure rich-click for better help screens.
click.rich_click.USE_RICH_MARKUP = True  # Enable [cyan]colored[/] markup like this.
