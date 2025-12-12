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

    # Parse endpoint to extract coordinates
    # For now, create a simple spec
    spec = EnvironmentSpec(
        name=env_name,
        description=f"Generated from {endpoint}",
        coordinates=[endpoint],
        entrypoints={},
        default_entrypoint=None,
        cache_dir=".jgo",
    )

    output_file = args.file or Path("jgo.toml")
    spec.save(output_file)

    if args.verbose > 0:
        print(f"Generated {output_file}")

    return 0
