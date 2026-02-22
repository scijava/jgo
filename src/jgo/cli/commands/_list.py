"""jgo list - List resolved dependencies"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...env import EnvironmentSpec
from ...parse import Coordinate, Endpoint
from ...styles import AT_MAINCLASS, PLUS_OPERATOR
from .._args import build_parsed_args
from .._context import create_environment_builder, create_maven_context
from .._output import print_dependencies

if TYPE_CHECKING:
    from .._args import ParsedArgs

_log = logging.getLogger(__name__)


@click.command(name="list", help="List resolved dependencies (flat list).")
@click.argument(
    "endpoint",
    required=False,
    cls=click.RichArgument,
    help=f"Maven coordinates (single or combined with {PLUS_OPERATOR}) "
    f"optionally followed by {AT_MAINCLASS}",
)
@click.option(
    "--direct", is_flag=True, help="Show only direct dependencies (non-transitive)"
)
@click.pass_context
def list_cmd(ctx, endpoint, direct):
    """List resolved dependencies as a flat list."""
    opts = ctx.obj
    opts["direct_only"] = direct
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=endpoint, command="list")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the list command.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    context = create_maven_context(args, config)
    builder = create_environment_builder(args, config, context)

    # Parse coordinates into dependencies
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            return 1
        spec = EnvironmentSpec.load(spec_file)
        try:
            coordinates = [
                Coordinate.parse(coord_str) for coord_str in spec.coordinates
            ]
        except ValueError as e:
            _log.error(f"Invalid coordinate format: {e}")
            return 1
        dependencies = builder._coordinates_to_dependencies(coordinates)
    else:
        if not args.endpoint:
            _log.error("No endpoint specified")
            return 1
        try:
            parsed = Endpoint.parse(args.endpoint)
        except ValueError as e:
            _log.error(f"Invalid endpoint format: {e}")
            return 1
        dependencies = builder._coordinates_to_dependencies(parsed.coordinates)

    print_dependencies(
        dependencies,
        context,
        list_mode=True,
        direct_only=args.direct_only,
        optional_depth=args.get_effective_optional_depth(),
    )
    return 0
