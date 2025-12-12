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

    # For other info types, delegate to commands but ensure proper flags are set
    # so they print info instead of running
    commands = JgoCommands(args, config)

    # If no specific info flag set, show a helpful message
    if not (
        args.print_classpath
        or args.print_java_info
        or args.print_dependency_tree
        or args.print_dependency_list
    ):
        print("Use info with one of these flags:", file=sys.stderr)
        print("  --print-classpath        Show classpath", file=sys.stderr)
        print(
            "  --print-java-info        Show Java version requirements", file=sys.stderr
        )
        print("  --print-dependency-tree  Show dependency tree", file=sys.stderr)
        print("  --print-dependency-list  Show flat dependency list", file=sys.stderr)
        print(
            "  --list-entrypoints       Show entrypoints from jgo.toml", file=sys.stderr
        )
        print("\nExamples:", file=sys.stderr)
        print(
            "  jgo info --print-classpath org.python:jython-standalone", file=sys.stderr
        )
        print(
            "  jgo info --print-java-info org.scijava:scijava-common", file=sys.stderr
        )
        return 1

    # Handle spec file mode vs endpoint mode
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
