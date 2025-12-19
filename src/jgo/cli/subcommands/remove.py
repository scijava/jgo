"""jgo remove - Remove dependencies from jgo.toml"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


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
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = JgoConfig.load_from_opts(opts)
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
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ...env import EnvironmentSpec

    # Get the spec file path
    spec_file = args.get_spec_file()

    if not spec_file.exists():
        print(f"Error: {spec_file} does not exist", file=sys.stderr)
        return 1

    # Get coordinates to remove
    coordinates = getattr(args, "coordinates", [])
    if not coordinates:
        print("Error: No coordinates specified", file=sys.stderr)
        print("Usage: jgo remove <coordinate> [<coordinate> ...]", file=sys.stderr)
        return 1

    # Load existing spec
    try:
        spec = EnvironmentSpec.load(spec_file)
    except Exception as e:
        print(f"Error: Failed to load {spec_file}: {e}", file=sys.stderr)
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
            print(f"Invalid coordinate format: {coord}", file=sys.stderr)
            continue

        # Find matching coordinates
        matched = False
        for existing_coord in spec.coordinates[:]:
            if existing_coord.startswith(prefix):
                spec.coordinates.remove(existing_coord)
                removed_count += 1
                matched = True
                if args.verbose > 0:
                    print(f"Removed: {existing_coord}")

        if not matched:
            if args.verbose > 0:
                print(f"Not found: {coord}")

    if removed_count == 0:
        print("No dependencies removed", file=sys.stderr)
        return 0

    # Save updated spec
    if args.dry_run:
        print(f"Would remove {removed_count} dependencies from {spec_file}")
        return 0

    try:
        spec.save(spec_file)
        print(f"Removed {removed_count} dependencies from {spec_file}")
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
