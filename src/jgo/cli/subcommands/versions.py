"""jgo versions - List available versions of an artifact"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(help="List available versions of an artifact")
@click.argument("coordinate", required=True)
@click.pass_context
def versions(ctx, coordinate):
    """List available versions of a Maven artifact."""
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = JgoConfig.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=coordinate, command="versions")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


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
    from ..helpers import parse_coordinate_safe

    if not args.endpoint:
        print("Error: versions command requires a coordinate", file=sys.stderr)
        print("Usage: jgo versions <groupId:artifactId>", file=sys.stderr)
        return 1

    # Parse endpoint to get groupId and artifactId
    coord, exit_code = parse_coordinate_safe(
        args.endpoint, "Invalid format. Need at least groupId:artifactId"
    )
    if exit_code != 0:
        return exit_code

    # Create commands instance to access maven context creation
    commands = JgoCommands(args, config)
    context = commands._create_maven_context()

    # Get project and fetch versions
    project = context.project(coord.groupId, coord.artifactId)

    try:
        # Update metadata from remote
        project.update()

        # Get available versions
        metadata = project.metadata
        if not metadata or not metadata.versions:
            print(f"No versions found for {coord.groupId}:{coord.artifactId}")
            return 0

        print(f"Available versions for {coord.groupId}:{coord.artifactId}:")
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
