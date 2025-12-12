"""jgo info - Show information about environment or artifact"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def add_parser(subparsers) -> argparse.ArgumentParser:
    """Add the 'info' subcommand parser."""
    parser = subparsers.add_parser(
        "info",
        help="Show information about environment or artifact",
        description="""Show information about a jgo environment or Maven artifact.

Use global flags to specify what information to show:
  --print-classpath    Show classpath
  --print-java-info    Show Java version requirements
  --list-entrypoints   Show available entrypoints from jgo.toml

Examples:
  jgo info --print-classpath org.python:jython-standalone
  jgo --print-java-info info org.python:jython-standalone
  jgo --list-entrypoints info

All global options apply. Use 'jgo --help' to see global options.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    return parser


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the info command.

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
    
    # Check which info was requested
    if args.list_entrypoints:
        return commands._cmd_list_entrypoints()
    
    # Handle spec file mode vs endpoint mode for other info types
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
