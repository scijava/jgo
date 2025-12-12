"""jgo remove - Remove dependencies from jgo.toml"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


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
        parts = coord.split(":")
        if len(parts) < 2:
            print(f"Invalid coordinate format: {coord}", file=sys.stderr)
            continue

        group_id = parts[0]
        artifact_id = parts[1]
        prefix = f"{group_id}:{artifact_id}"

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
