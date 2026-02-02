"""jgo list - List resolved dependencies"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...env import EnvironmentSpec
from ...env.builder import filter_managed_components
from ...parse.coordinate import Coordinate
from ..args import build_parsed_args
from ..context import create_environment_builder, create_maven_context
from ..output import print_dependencies

if TYPE_CHECKING:
    from ..args import ParsedArgs

_log = logging.getLogger(__name__)


@click.command(name="list", help="List resolved dependencies (flat list).")
@click.argument(
    "endpoint",
    required=False,
    cls=click.RichArgument,
    help="Maven coordinates (single or combined with [yellow]+[/]) "
    "optionally followed by [yellow]@MainClass[/]",
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

    # Parse coordinates into components
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            return 1
        spec = EnvironmentSpec.load(spec_file)
        components = []
        for coord_str in spec.coordinates:
            coord = Coordinate.parse(coord_str)
            version = coord.version or "RELEASE"
            component = context.project(coord.groupId, coord.artifactId).at_version(
                version
            )
            components.append(component)
        boms = None
    else:
        if not args.endpoint:
            _log.error("No endpoint specified")
            return 1
        components, coordinates, _ = builder._parse_endpoint(args.endpoint)
        boms = filter_managed_components(components, coordinates)

    print_dependencies(
        components,
        context,
        boms=boms,
        list_mode=True,
        direct_only=args.direct_only,
        optional_depth=args.get_effective_optional_depth(),
    )
    return 0
