"""jgo tree - Show dependency tree"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Add the 'tree' subcommand parser."""
    parser = subparsers.add_parser(
        "tree",
        help="Show dependency tree",
        description="""Show the dependency tree for an endpoint or jgo.toml.

Displays dependencies in a tree structure showing the relationship between
artifacts and their transitive dependencies.

All global options apply. Use 'jgo --help' to see global options.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # TODO: Add tree-specific options in Phase 5
    # parser.add_argument('--depth', type=int, help='Limit tree depth')
    # parser.add_argument('--format', choices=['simple', 'json'], help='Output format')

    return parser


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the tree command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Import here to avoid circular dependency
    from ..commands import JgoCommands

    # Set the flag to print dependency tree
    args.print_dependency_tree = True

    # Delegate to existing JgoCommands implementation
    commands = JgoCommands(args, config)

    # Handle spec file mode vs endpoint mode
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
