"""
Rich-specific presentation components for jgo CLI.

This package contains all Rich library integration code, keeping
presentation concerns in the CLI layer.
"""

from .formatters import format_dependency_list, format_dependency_tree
from .logging import setup_rich_logging
from .progress import download_progress_callback
from .widgets import NoWrapTable, NoWrapTree, create_table, create_tree

__all__ = [
    # Formatters
    "format_dependency_list",
    "format_dependency_tree",
    # Logging
    "setup_rich_logging",
    # Progress
    "download_progress_callback",
    # Widgets
    "NoWrapTable",
    "NoWrapTree",
    "create_table",
    "create_tree",
]
