"""jgo add - Add dependencies to jgo.toml"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(help="Add dependencies to jgo.toml")
@click.argument("coordinates", nargs=-1, required=True)
@click.option(
    "--no-sync",
    is_flag=True,
    help="Don't automatically sync after adding dependencies",
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
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = JgoConfig.load_from_opts(opts)
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
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """

    # Get the spec file path
    from ..helpers import load_spec_file

    spec, exit_code = load_spec_file(args)
    if exit_code != 0:
        return exit_code

    spec_file = args.get_spec_file()

    # Get coordinates to add
    coordinates = getattr(args, "coordinates", [])
    if not coordinates:
        print("Error: No coordinates specified", file=sys.stderr)
        print("Usage: jgo add <coordinate> [<coordinate> ...]", file=sys.stderr)
        return 1

    from ..helpers import verbose_print

    # Add coordinates
    added_count = 0
    for coord in coordinates:
        if coord in spec.coordinates:
            verbose_print(args, f"Already present: {coord}")
        else:
            spec.coordinates.append(coord)
            added_count += 1
            verbose_print(args, f"Added: {coord}")

    if added_count == 0:
        print("No new dependencies added", file=sys.stderr)
        return 0

    from ..helpers import handle_dry_run

    # Save updated spec
    if handle_dry_run(args, f"Would add {added_count} dependencies to {spec_file}"):
        return 0

    try:
        spec.save(spec_file)
        print(f"Added {added_count} dependencies to {spec_file}")
    except Exception as e:
        print(f"Error: Failed to save {spec_file}: {e}", file=sys.stderr)
        return 1

    # Auto-sync unless --no-sync specified
    if not getattr(args, "no_sync", False):
        verbose_print(args, "\nSyncing environment...")
        from . import sync as sync_cmd

        return sync_cmd.execute(args, config)

    return 0
