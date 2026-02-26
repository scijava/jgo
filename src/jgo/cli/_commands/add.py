"""jgo add - Add dependencies to jgo.toml"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...env import EnvironmentSpec
from ...styles import COORD_HELP_FULL, JGO_TOML, syntax
from .._args import build_parsed_args
from .._output import handle_dry_run
from . import parse_requirements_file
from . import sync as sync_cmd

if TYPE_CHECKING:
    from .._args import ParsedArgs

_log = logging.getLogger(__name__)


@click.command(help=f"Add dependencies to {JGO_TOML}.")
@click.argument(
    "coordinates",
    nargs=-1,
    required=False,
    cls=click.RichArgument,
    help=f"One or more Maven coordinates in format {COORD_HELP_FULL}",
)
@click.option(
    "-r",
    "--requirements",
    "requirements_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Read coordinates from a requirements file (one per line, # for comments)",
)
@click.option(
    "--no-sync",
    is_flag=True,
    help=f"Don't automatically {syntax('sync')} after adding dependencies",
)
@click.pass_context
def add(ctx, coordinates, requirements_file, no_sync):
    """
    Add one or more dependencies to jgo.toml.

    Automatically runs 'jgo sync' unless --no-sync is specified.

    EXAMPLES:
      jgo add org.python:jython-standalone:2.7.3
      jgo add org.scijava:scijava-common org.scijava:parsington
      jgo add --no-sync net.imagej:imagej:2.15.0
    """

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, command="add")
    args.coordinates = list(coordinates)
    args.requirements_file = requirements_file
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

    # Get the spec file path
    spec_file = args.get_spec_file()

    try:
        spec = EnvironmentSpec.load_or_error(spec_file)
    except (FileNotFoundError, ValueError) as e:
        _log.debug(f"Failed to load spec file: {e}")
        return 1

    # Get coordinates to add (from args and/or requirements file)
    coordinates = list(getattr(args, "coordinates", []))
    requirements_file = getattr(args, "requirements_file", None)
    if requirements_file:
        coordinates.extend(parse_requirements_file(requirements_file))
    if not coordinates:
        _log.error("No coordinates specified")
        _log.error("Usage: jgo add [-r requirements.txt] [<coordinate> ...]")
        return 1

    # Add coordinates
    added = []
    for coord in coordinates:
        if coord in spec.coordinates:
            _log.debug(f"Already present: {coord}")
        else:
            spec.coordinates.append(coord)
            added.append(coord)
            _log.debug(f"Added: {coord}")
    added_count = len(added)

    if added_count == 0:
        _log.warning("No new dependencies added")
        return 0

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
        exit_code = sync_cmd.execute(args, config)
        if exit_code != 0:
            # Sync failed -- revert the spec file to avoid leaving it in a bad state
            _log.debug("Reverting changes to spec file due to sync failure")
            for coord in added:
                try:
                    spec.coordinates.remove(coord)
                except ValueError:
                    pass
            try:
                spec.save(spec_file)
            except Exception as e:
                _log.warning(f"Failed to revert {spec_file}: {e}")
        return exit_code

    return 0
