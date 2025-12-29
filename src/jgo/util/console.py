"""
Console management for jgo.

Provides centralized Rich Console instances for all output (logging and data).
Consoles are configured once at startup based on CLI flags.
"""

from rich.console import Console

# Module-level console instances
# These are configured at startup via setup_consoles()
_console: Console = Console()
_err_console: Console = Console(stderr=True)


def setup_consoles(color: str = "auto", quiet: bool = False) -> None:
    """
    Configure console instances based on CLI flags.

    Should be called once at startup before any output occurs.

    Args:
        color: Color mode - "auto" (default), "always", or "never"
        quiet: If True, suppress all console output (data and messages)
    """
    global _console, _err_console

    console_kwargs = {"quiet": quiet}

    if color == "never":
        console_kwargs["no_color"] = True
    elif color == "always":
        console_kwargs["force_terminal"] = True
    # else: "auto" - use Rich's default TTY detection

    _console = Console(**console_kwargs)
    _err_console = Console(stderr=True, **console_kwargs)


def get_console() -> Console:
    """
    Get the stdout console instance.

    Returns:
        Console configured for stdout output
    """
    return _console


def get_err_console() -> Console:
    """
    Get the stderr console instance.

    Returns:
        Console configured for stderr output
    """
    return _err_console
