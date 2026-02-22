"""
Rich-specific presentation components for jgo CLI.

This package contains all Rich library integration code, keeping
presentation concerns in the CLI layer.
"""

from ._formatters import format_dependency_list, format_dependency_tree
from ._logging import setup_rich_logging
from ._progress import download_progress_callback
from ._widgets import NoWrapTable, NoWrapTree, create_table, create_tree

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
