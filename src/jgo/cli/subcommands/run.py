"""jgo run - Execute Java applications from Maven coordinates or jgo.toml"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Add the 'run' subcommand parser."""
    parser = subparsers.add_parser(
        "run",
        help="Run Java application from endpoint or jgo.toml",
        description="""Run a Java application from Maven coordinates or jgo.toml.

If an endpoint is provided, resolves dependencies and executes the main class.
If no endpoint is provided, runs the default entrypoint from jgo.toml.

All global options apply. Use 'jgo --help' to see global options.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Note: endpoint and remaining are already defined at global level
    # No additional arguments needed for now - all flags are global

    return parser


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
