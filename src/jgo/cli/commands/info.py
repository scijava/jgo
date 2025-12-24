"""jgo info - Show information about environment or artifact"""

from __future__ import annotations

import logging
from pathlib import Path

import click

_logger = logging.getLogger("jgo")


@click.command(help="Show classpath")
@click.argument("endpoint", required=False)
@click.pass_context
def classpath(ctx, endpoint):
    """Show the classpath for the given endpoint."""
    from ...config import GlobalSettings
    from ...env import EnvironmentSpec
    from ..context import create_environment_builder, create_maven_context
    from ..output import print_classpath
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Build environment
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _logger.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        environment = builder.from_spec(spec, update=args.update)
    else:
        if not endpoint:
            _logger.error("No endpoint specified")
            ctx.exit(1)
        environment = builder.from_endpoint(endpoint, update=args.update)

    print_classpath(environment)
    ctx.exit(0)


@click.command(help="Show dependency tree")
@click.argument("endpoint", required=False)
@click.pass_context
def deptree(ctx, endpoint):
    """Show the dependency tree for the given endpoint."""
    from ...config import GlobalSettings
    from ...env import EnvironmentSpec
    from ...env.builder import filter_managed_components
    from ...parse.coordinate import Coordinate
    from ..context import create_environment_builder, create_maven_context
    from ..output import print_dependencies
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Parse coordinates into components
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _logger.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        components = []
        for coord_str in spec.coordinates:
            coord = Coordinate.parse(coord_str)
            version = coord.version or "RELEASE"
            component = context.project(coord.groupId, coord.artifactId).at_version(
                version
            )
            components.append(component)
        boms = None  # No BOM management for spec mode
    else:
        if not endpoint:
            _logger.error("No endpoint specified")
            ctx.exit(1)
        components, coordinates, _ = builder._parse_endpoint(endpoint)
        boms = filter_managed_components(components, coordinates)

    print_dependencies(components, context, boms=boms, list_mode=False)
    ctx.exit(0)


@click.command(help="Show flat list of dependencies")
@click.argument("endpoint", required=False)
@click.option(
    "--direct", is_flag=True, help="Show only direct dependencies (non-transitive)"
)
@click.pass_context
def deplist(ctx, endpoint, direct):
    """Show a flat list of all dependencies for the given endpoint."""
    from ...config import GlobalSettings
    from ...env import EnvironmentSpec
    from ...env.builder import filter_managed_components
    from ...parse.coordinate import Coordinate
    from ..context import create_environment_builder, create_maven_context
    from ..output import print_dependencies
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Parse coordinates into components
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _logger.error(f"{spec_file} not found")
            ctx.exit(1)
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
        if not endpoint:
            _logger.error("No endpoint specified")
            ctx.exit(1)
        components, coordinates, _ = builder._parse_endpoint(endpoint)
        boms = filter_managed_components(components, coordinates)

    print_dependencies(
        components, context, boms=boms, list_mode=True, direct_only=direct
    )
    ctx.exit(0)


@click.command(help="Show Java version requirements")
@click.argument("endpoint", required=False)
@click.pass_context
def javainfo(ctx, endpoint):
    """Show Java version requirements for the given endpoint."""
    from ...config import GlobalSettings
    from ...env import EnvironmentSpec
    from ..context import create_environment_builder, create_maven_context
    from ..output import print_java_info
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Build environment
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _logger.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        environment = builder.from_spec(spec, update=args.update)
    else:
        if not endpoint:
            _logger.error("No endpoint specified")
            ctx.exit(1)
        environment = builder.from_endpoint(endpoint, update=args.update)

    print_java_info(environment)
    ctx.exit(0)


@click.command(help="Show entrypoints from jgo.toml")
@click.pass_context
def entrypoints(ctx):
    """Show available entrypoints defined in jgo.toml."""
    from ...env import EnvironmentSpec
    from ..parser import _build_parsed_args

    opts = ctx.obj
    args = _build_parsed_args(opts, endpoint=None, command="info")

    spec_file = args.file or Path("jgo.toml")

    if not spec_file.exists():
        _logger.error(f"{spec_file} not found")
        ctx.exit(1)

    spec = EnvironmentSpec.load(spec_file)

    if not spec.entrypoints:
        print("No entrypoints defined")
        ctx.exit(0)

    print("Available entrypoints:")
    for name, main_class in spec.entrypoints.items():
        marker = " (default)" if name == spec.default_entrypoint else ""
        print(f"  {name}: {main_class}{marker}")

    ctx.exit(0)


@click.command(help="Show JAR manifest")
@click.argument("endpoint", required=True)
@click.option("--raw", is_flag=True, help="Show raw manifest contents")
@click.pass_context
def manifest(ctx, endpoint, raw):
    """Show the JAR manifest for the given endpoint."""
    import zipfile

    from ...config import GlobalSettings
    from ...env.jar_util import parse_manifest, read_raw_manifest
    from ..context import create_maven_context
    from ..helpers import parse_coordinate_safe
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    try:
        # Create Maven context
        maven_context = create_maven_context(args, config.to_dict())

        # Parse endpoint to get G:A:V
        coord, exit_code = parse_coordinate_safe(endpoint)
        if exit_code != 0:
            ctx.exit(exit_code)
        version = coord.version or "RELEASE"

        # Get component
        component = maven_context.project(coord.groupId, coord.artifactId).at_version(
            version
        )

        # Resolve artifact to get JAR path
        artifact = component.artifact()
        jar_path = artifact.resolve()

        if not jar_path:
            _logger.error(f"Could not resolve artifact: {endpoint}")
            ctx.exit(1)

        # Verify it's a valid JAR file
        if not zipfile.is_zipfile(jar_path):
            _logger.error(f"Not a valid JAR file: {jar_path}")
            ctx.exit(1)

        # Read and display manifest
        if raw:
            manifest_content = read_raw_manifest(jar_path)
            if manifest_content is None:
                _logger.error(f"No MANIFEST.MF found in {jar_path}")
                ctx.exit(1)
            print(manifest_content, end="")
        else:
            manifest_dict = parse_manifest(jar_path)
            if manifest_dict is None:
                _logger.error(f"No MANIFEST.MF found in {jar_path}")
                ctx.exit(1)

            # Display parsed manifest
            for key, value in manifest_dict.items():
                print(f"{key}: {value}")

    except SystemExit:
        raise
    except Exception as e:
        _logger.error(f"{e}")
        ctx.exit(1)


@click.command(help="Show POM information")
@click.argument("endpoint", required=True)
@click.pass_context
def pom(ctx, endpoint):
    """Show the POM for the given component."""
    import xml.dom.minidom

    from ...config import GlobalSettings
    from ..context import create_maven_context
    from ..helpers import parse_coordinate_safe
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, endpoint=endpoint, command="info")

    try:
        # Create Maven context
        maven_context = create_maven_context(args, config.to_dict())

        # Parse endpoint to get G:A:V
        coord, exit_code = parse_coordinate_safe(endpoint)
        if exit_code != 0:
            ctx.exit(exit_code)
        version = coord.version or "RELEASE"

        # Get component
        component = maven_context.project(coord.groupId, coord.artifactId).at_version(
            version
        )

        # Get raw POM and pretty-print
        pom_obj = component.pom()

        if not pom_obj or not pom_obj.source:
            _logger.error(f"Could not resolve POM for: {endpoint}")
            ctx.exit(1)

        # Read POM content
        if isinstance(pom_obj.source, Path):
            pom_content = pom_obj.source.read_text()
        else:
            pom_content = str(pom_obj.source)

        # Pretty-print the XML
        try:
            dom = xml.dom.minidom.parseString(pom_content)
            pretty_xml = dom.toprettyxml(indent="  ")
            # Remove extra blank lines that toprettyxml adds
            lines = [line for line in pretty_xml.split("\n") if line.strip()]
            print("\n".join(lines))
        except Exception:
            # If pretty-printing fails, just output raw
            print(pom_content)

    except SystemExit:
        raise
    except Exception as e:
        _logger.error(f"{e}")
        ctx.exit(1)
