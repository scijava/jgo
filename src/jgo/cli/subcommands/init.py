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
    import sys
    from pathlib import Path
    from ...env import EnvironmentSpec
    
    endpoint = args.endpoint
    if not endpoint:
        print("Error: init requires an endpoint", file=sys.stderr)
        return 1

    # Parse endpoint to extract coordinates
    # For now, create a simple spec
    spec = EnvironmentSpec(
        name="jgo-environment",
        description=f"Generated from {endpoint}",
        coordinates=[endpoint],
        entrypoints={},
        default_entrypoint=None,
    )

    output_file = args.file or Path("jgo.toml")
    spec.save(output_file)

    if args.verbose > 0:
        print(f"Generated {output_file}")

    return 0
