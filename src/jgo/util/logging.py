"""
Logging utilities for jgo.

Provides structured logging with verbosity levels.
"""

import logging

from rich.logging import RichHandler

from .console import get_err_console


def setup_logging(verbose: int = 0) -> logging.Logger:
    """
    Setup logging for jgo.

    Args:
        verbose: Verbosity level (0 = WARNING, 1 = INFO, 2+ = DEBUG)

    Returns:
        Configured logger instance

    Note:
        Console configuration (color, quiet) is handled by console.setup_consoles().
        This function only configures log levels and formatting.
    """
    # Note: Must use "jgo" explicitly to configure the root jgo logger,
    # not this module's logger.
    logger = logging.getLogger("jgo")

    # Clear any existing handlers
    logger.handlers = []

    # Determine log level
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    else:  # verbose >= 2
        level = logging.DEBUG

    logger.setLevel(level)

    # Use the shared stderr console configured by console.setup_consoles()
    console = get_err_console()

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
    # Note: Must use "jgo" explicitly to query the root logger's level,
    # not this module's logger which would return NOTSET.
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


def log_exception_if_verbose(verbose: int = 0, level: int = 1) -> None:
    """
    Print full traceback if verbose level is high enough.

    Args:
        verbose: Current verbosity level
        level: Minimum verbose level required to print traceback (default: 1)

    Examples:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     _log.error(f"Operation failed: {e}")
        ...     log_exception_if_verbose(args.verbose)
    """
    if verbose > level:
        import traceback

        traceback.print_exc()
