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
    config = JgoConfig.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="init")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the init command.

    Supports shortcut composition with '+':
    - jgo init repl → creates 1 coordinate, 1 entrypoint (if @MainClass present)
    - jgo init repl+groovy → creates 2 coordinates, 2 entrypoints (one per shortcut with @MainClass)

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    import sys
    from pathlib import Path

    from ...config.jgorc import JgoConfig
    from ...env import EnvironmentSpec

    endpoint = args.endpoint
    if not endpoint:
        print("Error: init requires an endpoint", file=sys.stderr)
        return 1

    # Use current directory name as environment name (like pixi and uv do)
    current_dir = Path.cwd()
    env_name = current_dir.name

    # Expand shortcuts (supports + composition)
    shortcuts = config.get("shortcuts", {})
    jgoconfig = JgoConfig(shortcuts=shortcuts)
    expanded_endpoint = jgoconfig.expand_shortcuts(endpoint)

    if args.verbose > 0 and expanded_endpoint != endpoint:
        print(f"Expanded shortcuts: {endpoint} → {expanded_endpoint}", file=sys.stderr)

    # Parse endpoint to extract coordinates and entrypoints
    # Support composition with '+': track original shortcut names for entrypoint naming
    coordinates, entrypoints, default_entrypoint = _parse_endpoint_with_shortcuts(
        endpoint, expanded_endpoint, shortcuts
    )

    spec = EnvironmentSpec(
        name=env_name,
        description=f"Generated from {endpoint}",
        coordinates=coordinates,
        entrypoints=entrypoints,
        default_entrypoint=default_entrypoint,
        cache_dir=".jgo",
    )

    output_file = args.file or Path("jgo.toml")

    # Handle dry-run mode
    if args.dry_run:
        import tomli_w

        from ..helpers import handle_dry_run

        # Generate the TOML content that would be written
        toml_content = tomli_w.dumps(spec._to_dict())
        message = f"Would create {output_file}:\n{toml_content}"
        handle_dry_run(args, message)
        return 0

    spec.save(output_file)

    if args.verbose > 0:
        print(f"Generated {output_file}")
        if entrypoints:
            print(
                f"Created {len(entrypoints)} entrypoint(s): {', '.join(entrypoints.keys())}"
            )

    return 0


def _parse_endpoint_with_shortcuts(
    original_endpoint: str, expanded_endpoint: str, shortcuts: dict[str, str]
) -> tuple[list[str], dict[str, str], str | None]:
    """
    Parse endpoint (possibly with shortcuts and + composition) to extract coordinates and entrypoints.

    When no main class is specified via @ notation, the default entrypoint will use an
    endpoint reference (e.g., "org.python:jython-slim") to indicate main class inference
    from coordinates, rather than scanning for a main class explicitly during the init.

    Args:
        original_endpoint: Original endpoint string (may contain shortcut names)
        expanded_endpoint: Expanded endpoint string (shortcuts replaced with coordinates)
        shortcuts: Shortcut mapping from config

    Returns:
        Tuple of (coordinates, entrypoints, default_entrypoint)
        - coordinates: List of Maven coordinates
        - entrypoints: Dict mapping entrypoint names to coordinate references or main classes
        - default_entrypoint: Name of default entrypoint
    """
    # Split on + for composition
    original_parts = original_endpoint.split("+")
    expanded_parts = expanded_endpoint.split("+")

    if len(original_parts) != len(expanded_parts):
        # This shouldn't happen if expansion works correctly, but handle gracefully
        expanded_parts = expanded_endpoint.split("+")
        original_parts = expanded_parts  # Fall back to using expanded parts

    coordinates = []
    entrypoints = {}
    default_entrypoint = None

    for orig_part, exp_part in zip(original_parts, expanded_parts):
        # Parse the expanded part to get coordinate and main class
        coord, main_class = _parse_endpoint_for_init(exp_part)
        coordinates.append(coord)

        # If there's a main class, create an entrypoint
        if main_class:
            # Try to use the original part as the entrypoint name (if it's a shortcut)
            # Strip any suffix from the original part to get the shortcut name
            entrypoint_name = orig_part.split(":")[0]  # Take first token before ':'

            # If the original part is a known shortcut, use it as the entrypoint name
            if orig_part in shortcuts:
                entrypoint_name = orig_part
            else:
                # Not a shortcut, use a generic name
                if not entrypoints:
                    entrypoint_name = "main"
                else:
                    # Generate unique name: main2, main3, etc.
                    entrypoint_name = f"main{len(entrypoints) + 1}"

            entrypoints[entrypoint_name] = main_class

            # First entrypoint becomes default
            if default_entrypoint is None:
                default_entrypoint = entrypoint_name
        elif len(coordinates) == 1:
            # No explicit main class specified - use coordinate reference for inference
            # This allows "jgo init org.python:jython-slim" to infer main class at build time
            entrypoint_name = "main"
            # Use the full expanded coordinate as the entrypoint value
            entrypoints[entrypoint_name] = exp_part
            default_entrypoint = entrypoint_name

    return coordinates, entrypoints, default_entrypoint


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
