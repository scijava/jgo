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
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
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
    from ...env import EnvironmentSpec

    # Get the spec file path
    spec_file = args.get_spec_file()

    if not spec_file.exists():
        print(f"Error: {spec_file} does not exist", file=sys.stderr)
        print("Run 'jgo init' to create a new environment file first.", file=sys.stderr)
        return 1

    # Get coordinates to add
    coordinates = getattr(args, "coordinates", [])
    if not coordinates:
        print("Error: No coordinates specified", file=sys.stderr)
        print("Usage: jgo add <coordinate> [<coordinate> ...]", file=sys.stderr)
        return 1

    # Load existing spec
    try:
        spec = EnvironmentSpec.load(spec_file)
    except Exception as e:
        print(f"Error: Failed to load {spec_file}: {e}", file=sys.stderr)
        return 1

    # Add coordinates
    added_count = 0
    for coord in coordinates:
        if coord in spec.coordinates:
            if args.verbose > 0:
                print(f"Already present: {coord}")
        else:
            spec.coordinates.append(coord)
            added_count += 1
            if args.verbose > 0:
                print(f"Added: {coord}")

    if added_count == 0:
        print("No new dependencies added", file=sys.stderr)
        return 0

    # Save updated spec
    if args.dry_run:
        print(f"Would add {added_count} dependencies to {spec_file}")
        return 0

    try:
        spec.save(spec_file)
        print(f"Added {added_count} dependencies to {spec_file}")
    except Exception as e:
        print(f"Error: Failed to save {spec_file}: {e}", file=sys.stderr)
        return 1

    # Auto-sync unless --no-sync specified
    if not getattr(args, "no_sync", False):
        if args.verbose > 0:
            print("\nSyncing environment...")
        from . import sync as sync_cmd

        return sync_cmd.execute(args, config)

    return 0
