"""jgo tree - Show dependency tree"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import rich_click as click

if TYPE_CHECKING:
    from ..parser import ParsedArgs

_log = logging.getLogger("jgo")


@click.command(help="Show dependency tree.")
@click.argument("endpoint", required=False)
@click.pass_context
def tree(ctx, endpoint):
    """Show the dependency tree for an endpoint or jgo.toml."""
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="tree")

    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the tree command.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from ...env import EnvironmentSpec
    from ...env.builder import filter_managed_components
    from ...parse.coordinate import Coordinate
    from ..context import create_environment_builder, create_maven_context
    from ..output import print_dependencies

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

    print_dependencies(components, context, boms=boms, list_mode=False)
    return 0
