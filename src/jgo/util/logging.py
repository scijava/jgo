"""
Logging utilities for jgo.

Provides structured logging with verbosity levels.
"""

import logging
import sys


def setup_logging(verbose: int = 0, quiet: bool = False) -> logging.Logger:
    """
    Setup logging for jgo.

    Args:
        verbose: Verbosity level (0 = WARNING, 1 = INFO, 2+ = DEBUG)
        quiet: If True, suppress all output

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

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    if verbose >= 2:
        # Debug mode: include module name and line number
        formatter = logging.Formatter("%(levelname)s [%(name)s:%(lineno)d] %(message)s")
    elif verbose >= 1:
        # Info mode: include level
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    else:
        # Warning/error mode: just the message
        formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(name: str = "jgo") -> logging.Logger:
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
