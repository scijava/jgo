"""jgo add - Add dependencies to jgo.toml"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click

from ...styles import COORD_HELP_FULL

if TYPE_CHECKING:
    from ..parser import ParsedArgs

_log = logging.getLogger(__name__)


@click.command(help="Add dependencies to [cyan]jgo.toml[/].")
@click.argument(
    "coordinates",
    nargs=-1,
    required=True,
    cls=click.RichArgument,
    help=f"One or more Maven coordinates in format {COORD_HELP_FULL}",
)
@click.option(
    "--no-sync",
    is_flag=True,
    help="Don't automatically [yellow]sync[/] after adding dependencies",
)
@click.pass_context
def add(ctx, coordinates, no_sync):
    """
    Add one or more dependencies to jgo.toml.

    Automatically runs 'jgo sync' unless --no-sync is specified.

    EXAMPLES:
      jgo add org.python:jython-standalone:2.7.3
      jgo add org.scijava:scijava-common org.scijava:parsington
      jgo add --no-sync net.imagej:imagej:2.15.0
    """
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, command="add")
    args.coordinates = list(coordinates)
    args.no_sync = no_sync

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the add command.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ...env.spec import EnvironmentSpec

    # Get the spec file path
    spec_file = args.get_spec_file()

    try:
        spec = EnvironmentSpec.load_or_error(spec_file)
    except (FileNotFoundError, ValueError) as e:
        _log.debug(f"Failed to load spec file: {e}")
        return 1

    # Get coordinates to add
    coordinates = getattr(args, "coordinates", [])
    if not coordinates:
        _log.error("No coordinates specified")
        _log.error("Usage: jgo add <coordinate> [<coordinate> ...]")
        return 1

    # Add coordinates
    added_count = 0
    for coord in coordinates:
        if coord in spec.coordinates:
            _log.debug(f"Already present: {coord}")
        else:
            spec.coordinates.append(coord)
            added_count += 1
            _log.debug(f"Added: {coord}")

    if added_count == 0:
        _log.warning("No new dependencies added")
        return 0

    from ..output import handle_dry_run

    # Save updated spec
    if handle_dry_run(args, f"Would add {added_count} dependencies to {spec_file}"):
        return 0

    try:
        spec.save(spec_file)
        _log.info(f"Added {added_count} dependencies to {spec_file}")
    except Exception as e:
        _log.error(f"Failed to save {spec_file}: {e}")
        return 1

    # Auto-sync unless --no-sync specified
    if not getattr(args, "no_sync", False):
        _log.debug("Syncing environment...")
        from . import sync as sync_cmd

        return sync_cmd.execute(args, config)

    return 0
