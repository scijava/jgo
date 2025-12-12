"""jgo list - List resolved dependencies"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Add the 'list' subcommand parser."""
    parser = subparsers.add_parser(
        "list",
        help="List resolved dependencies",
        description="""List resolved dependencies as a flat list.

Shows all dependencies that would be included in the classpath,
without the tree structure.

All global options apply. Use 'jgo --help' to see global options.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # TODO: Add list-specific options in Phase 3
    # parser.add_argument('--tree', action='store_true', help='Show as tree (alias for jgo tree)')
    # parser.add_argument('--format', choices=['simple', 'json', 'table'], help='Output format')

    return parser


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the list command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Import here to avoid circular dependency
    from ..commands import JgoCommands

    # Set the flag to print dependency list
    args.print_dependency_list = True

    # Delegate to existing JgoCommands implementation
    commands = JgoCommands(args, config)

    # Handle spec file mode vs endpoint mode
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
