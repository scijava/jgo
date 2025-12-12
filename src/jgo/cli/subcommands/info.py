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
    import sys
    from pathlib import Path
    from ...env import EnvironmentSpec
    from ..commands import JgoCommands

    # Check which info was requested
    if args.list_entrypoints:
        # List entrypoints from jgo.toml
        spec_file = args.file or Path("jgo.toml")

        if not spec_file.exists():
            print(f"Error: {spec_file} not found", file=sys.stderr)
            return 1

        spec = EnvironmentSpec.load(spec_file)

        if not spec.entrypoints:
            print("No entrypoints defined")
            return 0

        print("Available entrypoints:")
        for name, main_class in spec.entrypoints.items():
            marker = " (default)" if name == spec.default_entrypoint else ""
            print(f"  {name}: {main_class}{marker}")

        return 0
    
    # For other info types (classpath, java-info), delegate to commands
    commands = JgoCommands(args, config)
    
    # Handle spec file mode vs endpoint mode for other info types
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
