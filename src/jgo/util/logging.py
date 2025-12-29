"""
Logging utilities for jgo.

Provides structured logging with verbosity levels.
"""

import logging

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    verbose: int = 0, quiet: bool = False, color: str = "auto"
) -> logging.Logger:
    """
    Setup logging for jgo.

    Args:
        verbose: Verbosity level (0 = WARNING, 1 = INFO, 2+ = DEBUG)
        quiet: If True, suppress all output
        color: Color mode: "auto", "always", or "never"

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("jgo")

    # Clear any existing handlers
    logger.handlers = []

    # Determine log level
    if quiet:
        level = logging.CRITICAL + 1  # Suppress all output
    elif verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:  # verbose >= 2
        level = logging.DEBUG

    logger.setLevel(level)

    # Configure console with color settings
    if color == "never":
        console = Console(stderr=True, no_color=True)
    elif color == "always":
        console = Console(stderr=True, force_terminal=True)
    else:  # "auto"
        console = Console(stderr=True)

    # Create Rich handler for colored, formatted log output
    handler = RichHandler(
        console=console,
        show_time=False,
        show_path=(verbose >= 2),  # Show module:line in debug mode
        markup=True,  # Allow rich markup in log messages
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

    return logger


def get_log(name: str = "jgo") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to "jgo")

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_log_level() -> int:
    """
    Get the current log level for the jgo logger.

    Returns:
        Current log level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
    """
    return logging.getLogger("jgo").level


def is_debug_enabled() -> bool:
    """
    Check if DEBUG logging is enabled.

    Returns:
        True if the current log level is DEBUG or lower
    """
    return get_log_level() <= logging.DEBUG


def is_info_enabled() -> bool:
    """
    Check if INFO logging is enabled.

    Returns:
        True if the current log level is INFO or lower (INFO or DEBUG)
    """
    return get_log_level() <= logging.INFO
