"""jgo run - Execute Java applications from Maven coordinates or jgo.toml"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the run command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Import here to avoid circular dependency
    from ..commands import JgoCommands

    # Delegate to existing JgoCommands implementation
    commands = JgoCommands(args, config)

    # Handle spec file mode vs endpoint mode
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
