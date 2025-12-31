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

# Current no-wrap mode
_no_wrap: bool = False


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
    color: str = "auto", quiet: bool = False, no_wrap: bool = False
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
        no_wrap: If True, disable text wrapping in rich output
    """
    global _console, _err_console, _color_mode, _no_wrap

    # Normalize aliases
    color = normalize_color_mode(color)
    _color_mode = color
    _no_wrap = no_wrap

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


def get_no_wrap() -> bool:
    """
    Get the current no-wrap mode.

    Returns:
        True if text wrapping should be disabled in rich output
    """
    return _no_wrap


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
    Print to console, respecting the global no-wrap setting.

    This is a convenience wrapper around Console.print() that automatically
    applies soft_wrap=True when --no-wrap mode is enabled.

    Args:
        *objects: Objects to print
        sep: Separator between objects
        end: String to print at end
        stderr: If True, print to stderr console
        highlight: Enable syntax highlighting (default: None = auto)
        **kwargs: Additional arguments passed to Console.print()
    """
    console = _err_console if stderr else _console

    if _no_wrap:
        # In no-wrap mode, use soft_wrap to prevent artificial line breaks
        kwargs.setdefault("soft_wrap", True)
        # Disable highlighting in no-wrap mode to avoid color codes in grep output
        if highlight is None:
            highlight = False

    console.print(*objects, sep=sep, end=end, highlight=highlight, **kwargs)
