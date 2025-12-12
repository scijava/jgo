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
    import sys
    from ..commands import JgoCommands
    
    if not args.endpoint:
        print("Error: versions command requires a coordinate", file=sys.stderr)
        print("Usage: jgo versions <groupId:artifactId>", file=sys.stderr)
        return 1

    # Parse endpoint to get groupId and artifactId
    parts = args.endpoint.split(":")
    if len(parts) < 2:
        print(
            "Error: Invalid format. Need at least groupId:artifactId",
            file=sys.stderr,
        )
        return 1

    groupId = parts[0]
    artifactId = parts[1]

    # Create commands instance to access maven context creation
    commands = JgoCommands(args, config)
    context = commands._create_maven_context()

    # Get project and fetch versions
    project = context.project(groupId, artifactId)

    try:
        # Update metadata from remote
        project.update()

        # Get available versions
        metadata = project.metadata
        if not metadata or not metadata.versions:
            print(f"No versions found for {groupId}:{artifactId}")
            return 0

        print(f"Available versions for {groupId}:{artifactId}:")
        for version in metadata.versions:
            marker = ""
            if metadata.release and version == metadata.release:
                marker = " (release)"
            elif metadata.latest and version == metadata.latest:
                marker = " (latest)"
            print(f"  {version}{marker}")

    except Exception as e:
        print(f"Error fetching versions: {e}", file=sys.stderr)
        return 1

    return 0
