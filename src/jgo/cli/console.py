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
    color: str = "auto", quiet: bool = False, wrap: str = "auto"
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
            - "auto" (default): Smart for TTY, raw for pipes/files
            - "smart": Rich's intelligent wrapping at word boundaries
            - "raw": Natural terminal wrapping, no constraints
    """
    global _console, _err_console, _color_mode, _wrap_mode, _quiet

    # Normalize aliases
    color = normalize_color_mode(color)
    _color_mode = color
    _quiet = quiet

    console_kwargs: dict = {"quiet": quiet}

    # Configure color mode
    if color == "plain":
        # No ANSI codes at all
        console_kwargs["color_system"] = None
    elif color == "styled":
        # Bold/italic but no color (NO_COLOR compliant)
        console_kwargs["no_color"] = True
        console_kwargs["force_terminal"] = True
    elif color == "rich":
        # Force full color + style even if not a TTY
        console_kwargs["force_terminal"] = True
    # else: "auto" - use Rich's default TTY detection

    # Create consoles
    _console = Console(**console_kwargs)
    _err_console = Console(stderr=True, **console_kwargs)

    # Resolve wrap mode using Rich's TTY detection
    # This ensures we're consistent with Rich's opinion on TTY status
    if wrap == "auto":
        _wrap_mode = "smart" if _console.is_terminal else "raw"
    else:
        _wrap_mode = wrap


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
        Current wrap mode: "smart" or "raw" (auto is resolved in setup_consoles)
    """
    return _wrap_mode


def is_quiet() -> bool:
    """
    Check if quiet mode is enabled.

    Returns:
        True if quiet mode is enabled (suppress all output including progress bars)
    """
    return _quiet


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
    style: str | None = None,
    justify: str | None = None,
    overflow: str | None = None,
    markup: bool | None = None,
    emoji: bool = False,
    highlight: bool | None = None,
    soft_wrap: bool | None = None,
    **kwargs,
) -> None:
    """
    Print to console, respecting global color and wrap settings.

    This wrapper provides consistent defaults for jgo output:
    - Automatically sets soft_wrap based on wrap mode (smart/raw)
    - Disables emoji by default (emoji=False)
    - Respects color and wrap modes configured at startup

    Args:
        *objects: Objects to print
        sep: Separator between objects (default: " ")
        end: String to print at end (default: "\\n")
        stderr: If True, print to stderr console (default: False)
        style: Rich style to apply (default: None)
        justify: Text justification - "default", "left", "right", "center", "full" (default: None)
        overflow: Overflow handling - "ignore", "crop", "fold", "ellipsis" (default: None)
        markup: Enable Rich markup like [bold] (default: None = use console default)
        emoji: Enable emoji codes (default: False, jgo doesn't use emoji)
        highlight: Enable syntax highlighting (default: None = use console default)
        soft_wrap: Override wrap mode - True for raw, False for smart (default: None = auto from wrap mode)
        **kwargs: Additional arguments passed to Console.print()
    """
    console = _err_console if stderr else _console

    # Auto-set soft_wrap based on wrap mode if not explicitly provided
    if soft_wrap is None:
        soft_wrap = _wrap_mode == "raw"

    console.print(
        *objects,
        sep=sep,
        end=end,
        style=style,
        justify=justify,
        overflow=overflow,
        markup=markup,
        emoji=emoji,
        highlight=highlight,
        soft_wrap=soft_wrap,
        **kwargs,
    )
