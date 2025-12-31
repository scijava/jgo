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

# Current color mode (for other modules to query)
_color_mode: str = "auto"


def normalize_color_mode(color: str) -> str:
    """
    Normalize color mode aliases to canonical values.

    Args:
        color: Color mode string (may be alias)

    Returns:
        Canonical color mode: "auto", "rich", "styled", or "plain"
    """
    # Resolve aliases
    if color == "always":
        return "rich"
    elif color == "never":
        return "plain"
    return color


def setup_consoles(color: str = "auto", quiet: bool = False) -> None:
    """
    Configure console instances based on CLI flags.

    Should be called once at startup before any output occurs.

    Args:
        color: Color mode:
            - "auto" (default): Rich's default TTY detection
            - "rich" (alias: "always"): Force full color + style
            - "styled": Bold/italic only, no color (NO_COLOR compliant)
            - "plain" (alias: "never"): No ANSI codes at all
        quiet: If True, suppress all console output (data and messages)
    """
    global _console, _err_console, _color_mode

    # Normalize aliases
    color = normalize_color_mode(color)
    _color_mode = color

    console_kwargs: dict = {"quiet": quiet}

    if color == "plain":
        # No ANSI codes at all
        console_kwargs["color_system"] = None
    elif color == "styled":
        # Bold/italic but no color (NO_COLOR compliant)
        console_kwargs["no_color"] = True
    elif color == "rich":
        # Force full color + style even if not a TTY
        console_kwargs["force_terminal"] = True
    # else: "auto" - use Rich's default TTY detection

    _console = Console(**console_kwargs)
    _err_console = Console(stderr=True, **console_kwargs)


def get_color_mode() -> str:
    """
    Get the current color mode.

    Returns:
        Current color mode: "auto", "rich", "styled", or "plain"
    """
    return _color_mode


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
