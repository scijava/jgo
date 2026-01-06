"""
Rich logging setup for jgo CLI.

This module provides Rich-specific logging configuration,
keeping Rich integration in the CLI layer.
"""

import logging

from rich.logging import RichHandler

from ..console import get_err_console


def setup_rich_logging(logger: logging.Logger, verbose: int = 0) -> None:
    """
    Configure Rich logging handler for the given logger.

    Args:
        logger: Logger instance to configure
        verbose: Verbosity level (0 = WARNING, 1 = INFO, 2+ = DEBUG)

    Note:
        Console configuration (color, quiet) is handled by console.setup_consoles().
        This function only configures the Rich handler and formatting.
    """
    # Use the shared stderr console configured by console.setup_consoles()
    console = get_err_console()

    # Determine log level
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:  # verbose >= 2
        level = logging.DEBUG

    # Create Rich handler for colored, formatted log output
    handler = RichHandler(
        console=console,
        show_time=False,
        show_path=(verbose >= 2),  # Show module:line in debug mode
        markup=False,  # Disable markup to prevent emoji conversion (e.g., :fiji: → 🇫🇯)
        rich_tracebacks=True,  # Better exception formatting
    )
    handler.setLevel(level)

    # Create formatter - RichHandler adds level colors automatically
    if verbose >= 2:
        # Debug mode: RichHandler's show_path will display [name:lineno]
        formatter = logging.Formatter("%(message)s")
    elif verbose >= 1:
        # Info mode: show level name
        formatter = logging.Formatter("%(message)s")
    else:
        # Warning/error mode: just the message
        formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)
