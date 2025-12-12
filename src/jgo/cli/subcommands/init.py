"""jgo init - Create a new jgo.toml environment file"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(help="Create a new jgo.toml environment file")
@click.argument("endpoint", required=False)
@click.pass_context
def init(ctx, endpoint):
    """Create a new jgo.toml file."""
    from ...config.jgorc import JgoConfig
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = JgoConfig() if opts.get("ignore_jgorc") else JgoConfig.load()
    args = _build_parsed_args(opts, endpoint=endpoint, command="init")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the init command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    import sys
    from pathlib import Path

    from ...env import EnvironmentSpec

    endpoint = args.endpoint
    if not endpoint:
        print("Error: init requires an endpoint", file=sys.stderr)
        return 1

    # Use current directory name as environment name (like pixi and uv do)
    current_dir = Path.cwd()
    env_name = current_dir.name

    # Parse endpoint to extract coordinates and main class
    coordinate, main_class = _parse_endpoint_for_init(endpoint)

    # Create spec with separated coordinate and entrypoint
    entrypoints = {}
    default_entrypoint = None
    if main_class:
        # Use a meaningful entrypoint name
        entrypoint_name = "main"
        entrypoints[entrypoint_name] = main_class
        default_entrypoint = entrypoint_name

    spec = EnvironmentSpec(
        name=env_name,
        description=f"Generated from {endpoint}",
        coordinates=[coordinate],
        entrypoints=entrypoints,
        default_entrypoint=default_entrypoint,
        cache_dir=".jgo",
    )

    output_file = args.file or Path("jgo.toml")
    spec.save(output_file)

    if args.verbose > 0:
        print(f"Generated {output_file}")

    return 0


def _parse_endpoint_for_init(endpoint: str) -> tuple[str, str | None]:
    """
    Parse an endpoint string to extract the Maven coordinate and main class.

    Args:
        endpoint: Endpoint string (e.g., "org.scijava:scijava-common@ScriptREPL")

    Returns:
        Tuple of (coordinate, main_class)
        - coordinate: Maven coordinate without main class (e.g., "org.scijava:scijava-common")
        - main_class: Main class if specified, otherwise None
    """
    # Check for @ separator (new format)
    if "@" in endpoint:
        # Split on the last @ to separate coordinate from main class
        at_index = endpoint.rfind("@")
        before_at = endpoint[:at_index]
        after_at = endpoint[at_index + 1 :]

        # Check for old format (coord:@MainClass)
        if before_at.endswith(":"):
            # Old format - main class has @ prefix
            coordinate = before_at.rstrip(":")
            main_class = "@" + after_at if after_at else None
        else:
            # New format - main class after @
            coordinate = before_at
            main_class = after_at if after_at else None

        return coordinate, main_class

    # No @ separator - endpoint is just the coordinate
    return endpoint, None
