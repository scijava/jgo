"""jgo versions - List available versions of an artifact"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...parse.coordinate import Coordinate
from ..args import build_parsed_args
from ..console import console_print
from ..context import create_maven_context
from ..rich.formatters import format_coordinate

if TYPE_CHECKING:
    from ..args import ParsedArgs

_log = logging.getLogger(__name__)


@click.command(help="List available versions of an artifact.")
@click.argument("coordinate", required=True)
@click.pass_context
def versions(ctx, coordinate):
    """List available versions of a Maven artifact."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=coordinate, command="versions")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the versions command.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """

    if not args.endpoint:
        _log.error("versions command requires a coordinate")
        _log.error("Usage: jgo versions <groupId:artifactId>")
        return 1

    # Parse endpoint to get groupId and artifactId
    try:
        coord = Coordinate.parse(args.endpoint)
    except ValueError:
        _log.error("Invalid format. Need at least groupId:artifactId")
        return 1

    # Create maven context
    context = create_maven_context(args, config)

    # Get project and fetch versions
    project = context.project(coord.groupId, coord.artifactId)

    try:
        # Update metadata from remote
        project.update()

        # Get available versions
        metadata = project.metadata
        if not metadata or not metadata.versions:
            console_print(f"No versions found for {format_coordinate(coord)}")
            return 0

        # Use project's smart release/latest resolution
        release_version = project.release
        latest_version = project.latest

        console_print(f"Available versions for {format_coordinate(coord)}:")
        for version in metadata.versions:
            marker = ""
            if release_version and version == release_version:
                marker = " (release)"
            elif latest_version and version == latest_version:
                marker = " (latest)"
            console_print(f"  {version}[dim]{marker}[/]")

    except Exception as e:
        _log.error(f"Error fetching versions: {e}")
        return 1

    return 0
