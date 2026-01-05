"""
Console management for jgo.

Provides centralized Rich Console instances for all output (logging and data).
Consoles are configured once at startup based on CLI flags.
"""

from __future__ import annotations

from rich.console import Console

# Module-level console instances
# These are configured at startup via setup_consoles()
_console: Console = Console()
_err_console: Console = Console(stderr=True)

# Current color mode (for other modules to query)
_color_mode: str = "auto"

# Current wrap mode
_wrap_mode: str = "smart"

# Current quiet mode
_quiet: bool = False


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


def setup_consoles(
    color: str = "auto", quiet: bool = False, wrap: str = "smart"
) -> None:
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
        wrap: Wrap mode:
            - "smart" (default): Rich's intelligent wrapping with padding
            - "raw": Natural terminal wrapping, no constraints
            - "crop": Truncate at terminal width
    """
    global _console, _err_console, _color_mode, _wrap_mode, _quiet

    # Normalize aliases
    color = normalize_color_mode(color)
    _color_mode = color
    _wrap_mode = wrap
    _quiet = quiet

    console_kwargs: dict = {"quiet": quiet}

    # Configure color mode
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

    # Configure wrap mode
    if wrap == "raw":
        # Natural terminal wrapping, no constraints
        console_kwargs["soft_wrap"] = True
    # else: "smart" or "crop" use Rich's default behavior

    _console = Console(**console_kwargs)
    _err_console = Console(stderr=True, **console_kwargs)


def get_color_mode() -> str:
    """
    Get the current color mode.

    Returns:
        Current color mode: "auto", "rich", "styled", or "plain"
    """
    return _color_mode


def get_wrap_mode() -> str:
    """
    Get the current wrap mode.

    Returns:
        Current wrap mode: "smart", "raw", or "crop"
    """
    return _wrap_mode


def is_quiet() -> bool:
    """
    Check if quiet mode is enabled.

    Returns:
        True if quiet mode is enabled (suppress all output including progress bars)
    """
    return _quiet


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


def console_print(
    *objects,
    sep: str = " ",
    end: str = "\n",
    stderr: bool = False,
    highlight: bool | None = None,
    **kwargs,
) -> None:
    """
    Print to console, respecting the global wrap setting.

    This is a convenience wrapper around Console.print(). Currently not used
    since wrap mode is configured globally on the console instances, but kept
    for potential future use.

    Args:
        *objects: Objects to print
        sep: Separator between objects
        end: String to print at end
        stderr: If True, print to stderr console
        highlight: Enable syntax highlighting (default: None = auto)
        **kwargs: Additional arguments passed to Console.print()
    """
    console = _err_console if stderr else _console
    console.print(*objects, sep=sep, end=end, highlight=highlight, **kwargs)
