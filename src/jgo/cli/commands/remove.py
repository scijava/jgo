"""jgo remove - Remove dependencies from jgo.toml"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs

_logger = logging.getLogger("jgo")


@click.command(help="Remove dependencies from jgo.toml")
@click.argument("coordinates", nargs=-1, required=True)
@click.option(
    "--no-sync",
    is_flag=True,
    help="Don't automatically sync after removing dependencies",
)
@click.pass_context
def remove(ctx, coordinates, no_sync):
    """
    Remove one or more dependencies from jgo.toml.

    Coordinates can be specified as groupId:artifactId (version ignored).
    Automatically runs 'jgo sync' unless --no-sync is specified.

    EXAMPLES:
      jgo remove org.python:jython-standalone
      jgo remove org.scijava:scijava-common org.scijava:parsington
      jgo remove --no-sync net.imagej:imagej
    """
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, command="remove")
    args.coordinates = list(coordinates)
    args.no_sync = no_sync

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the remove command.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ..helpers import load_spec_file

    # Get the spec file path
    spec, exit_code = load_spec_file(args)
    if exit_code != 0:
        return exit_code

    spec_file = args.get_spec_file()

    # Get coordinates to remove
    coordinates = getattr(args, "coordinates", [])
    if not coordinates:
        _logger.error("No coordinates specified")
        _logger.error("Usage: jgo remove <coordinate> [<coordinate> ...]")
        return 1

    # Remove coordinates (matching by groupId:artifactId, ignoring version)
    removed_count = 0
    for coord in coordinates:
        # Parse coordinate to extract groupId:artifactId
        try:
            from ...parse.coordinate import Coordinate

            coord_obj = Coordinate.parse(coord)
            prefix = f"{coord_obj.groupId}:{coord_obj.artifactId}"
        except ValueError:
            _logger.error(f"Invalid coordinate format: {coord}")
            continue

        # Find matching coordinates
        matched = False
        for existing_coord in spec.coordinates[:]:
            if existing_coord.startswith(prefix):
                spec.coordinates.remove(existing_coord)
                removed_count += 1
                matched = True
                _logger.debug(f"Removed: {existing_coord}")

        if not matched:
            _logger.debug(f"Not found: {coord}")

    if removed_count == 0:
        _logger.warning("No dependencies removed")
        return 0

    from ..helpers import handle_dry_run

    # Save updated spec
    if handle_dry_run(
        args, f"Would remove {removed_count} dependencies from {spec_file}"
    ):
        return 0

    try:
        spec.save(spec_file)
        _logger.info(f"Removed {removed_count} dependencies from {spec_file}")
    except Exception as e:
        _logger.error(f"Failed to save {spec_file}: {e}")
        return 1

    # Auto-sync unless --no-sync specified
    if not getattr(args, "no_sync", False):
        _logger.debug("Syncing environment...")
        from . import sync as sync_cmd

        return sync_cmd.execute(args, config)

    return 0
