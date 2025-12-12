"""jgo versions - List available versions of an artifact"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Add the 'versions' subcommand parser."""
    parser = subparsers.add_parser(
        "versions",
        help="List available versions of an artifact",
        description="""List available versions of a Maven artifact.

Queries Maven repositories for all published versions of the specified artifact.

Example:
  jgo versions org.scijava:scijava-common

All global options apply. Use 'jgo --help' to see global options.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # TODO: Add versions-specific options in Phase 3
    # parser.add_argument('--limit', type=int, help='Limit number of results')
    # parser.add_argument('--filter', help='Filter versions by pattern')

    return parser


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the versions command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Import here to avoid circular dependency
    from ..commands import JgoCommands

    # Set the flag to list versions
    args.list_versions = True
    
    # Delegate to existing JgoCommands implementation
    commands = JgoCommands(args, config)
    return commands._cmd_list_versions()
