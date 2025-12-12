"""jgo init - Create a new jgo.toml environment file"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Add the 'init' subcommand parser."""
    parser = subparsers.add_parser(
        "init",
        help="Create a new jgo.toml environment file",
        description="""Create a new jgo.toml environment file.

If an endpoint is provided, initializes the project with that dependency.
If no endpoint is provided, creates a minimal template.

All global options apply. Use 'jgo --help' to see global options.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    return parser


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the init command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Import here to avoid circular dependency
    from ..commands import JgoCommands

    # Set the init flag to trigger init behavior
    # The endpoint is used as the init parameter
    args.init = args.endpoint or ""
    
    # Delegate to existing JgoCommands implementation
    commands = JgoCommands(args, config)
    return commands._cmd_init()
