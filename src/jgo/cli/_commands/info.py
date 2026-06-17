"""jgo info - Show information about environment or artifact"""

from __future__ import annotations

import logging
import xml.dom.minidom
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...env import EnvironmentSpec, parse_manifest, read_raw_manifest
from ...parse import Coordinate, Endpoint

if TYPE_CHECKING:
    from ...env import Environment, EnvironmentBuilder
    from ...maven import MavenContext
    from .._args import ParsedArgs

from ...styles import AT_MAINCLASS, COORD_HELP_FULL, JGO_TOML, PLUS_OPERATOR
from .._args import build_parsed_args, classify_javainfo_input, resolve_pom_input
from .._console import console_print
from .._context import create_environment_builder, create_maven_context
from .._output import (
    SourceReport,
    environment_report,
    paths_report,
    print_classpath,
    print_dependencies,
    print_jars,
    print_java_info,
    print_main_classes,
    print_modulepath,
    print_pom_dependencies,
)

_log = logging.getLogger(__name__)


@click.command(help="Show classpath.")
@click.argument(
    "endpoint",
    required=False,
    cls=click.RichArgument,
    help=f"Maven coordinates (single or combined with {PLUS_OPERATOR}) "
    f"optionally followed by {AT_MAINCLASS}",
)
@click.pass_context
def classpath(ctx: click.Context, endpoint: str | None) -> None:
    """Show the classpath for the given endpoint."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Build environment
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        environment = _from_spec_or_die(ctx, builder, spec, args.update)
    else:
        if not endpoint:
            _log.error("No endpoint specified")
            ctx.exit(1)
        environment = builder.from_endpoint(endpoint, update=args.update)

    print_classpath(environment)
    ctx.exit(0)


@click.command(help="Show environment directory path.")
@click.argument(
    "endpoint",
    required=False,
    cls=click.RichArgument,
    help=f"Maven coordinates (single or combined with {PLUS_OPERATOR}) "
    f"optionally followed by {AT_MAINCLASS}",
)
@click.pass_context
def envdir(ctx: click.Context, endpoint: str | None) -> None:
    """Show the cache/environment directory for the given endpoint or jgo project."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Build environment
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        environment = _from_spec_or_die(ctx, builder, spec, args.update)
    else:
        if not endpoint:
            _log.error("No endpoint specified")
            ctx.exit(1)
        environment = builder.from_endpoint(endpoint, update=args.update)

    console_print(environment.path)
    ctx.exit(0)


@click.command(help="Show all JAR paths (classpath + module-path).")
@click.argument(
    "endpoint",
    required=False,
    cls=click.RichArgument,
    help=f"Maven coordinates (single or combined with {PLUS_OPERATOR}) "
    f"optionally followed by {AT_MAINCLASS}",
)
@click.pass_context
def jars(ctx: click.Context, endpoint: str | None) -> None:
    """Show all JAR paths with section headers for classpath and module-path."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Build environment
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        environment = _from_spec_or_die(ctx, builder, spec, args.update)
    else:
        if not endpoint:
            _log.error("No endpoint specified")
            ctx.exit(1)
        environment = builder.from_endpoint(endpoint, update=args.update)

    print_jars(environment)
    ctx.exit(0)


@click.command(help="Show module-path.")
@click.argument("endpoint", required=False)
@click.pass_context
def modulepath(ctx: click.Context, endpoint: str | None) -> None:
    """Show the module-path for the given endpoint."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Build environment
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        environment = _from_spec_or_die(ctx, builder, spec, args.update)
    else:
        if not endpoint:
            _log.error("No endpoint specified")
            ctx.exit(1)
        environment = builder.from_endpoint(endpoint, update=args.update)

    print_modulepath(environment)
    ctx.exit(0)


@click.command(help="Show classes with public main methods.")
@click.argument("endpoint", required=False)
@click.pass_context
def mains(ctx: click.Context, endpoint: str | None) -> None:
    """Find and list all classes with public static void main(String[]) methods."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Build environment
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        environment = _from_spec_or_die(ctx, builder, spec, args.update)
    else:
        if not endpoint:
            _log.error("No endpoint specified")
            ctx.exit(1)
        environment = builder.from_endpoint(endpoint, update=args.update)

    print_main_classes(environment)
    ctx.exit(0)


@click.command(help="Show dependency tree.")
@click.argument("endpoint", required=False)
@click.pass_context
def deptree(ctx: click.Context, endpoint: str | None) -> None:
    """Show the dependency tree for the given endpoint."""
    _print_deps(ctx, endpoint, list_mode=False)


@click.command(help="Show flat list of dependencies.")
@click.argument("endpoint", required=False)
@click.option(
    "--direct", is_flag=True, help="Show only direct dependencies (non-transitive)."
)
@click.pass_context
def deplist(ctx: click.Context, endpoint: str | None, direct: bool) -> None:
    """Show a flat list of all dependencies for the given endpoint."""
    _print_deps(ctx, endpoint, list_mode=True)


@click.command(help="Show Java version requirements.")
@click.argument("inputs", nargs=-1)
@click.option(
    "--direct",
    is_flag=True,
    help="Analyze the named artifacts plus their direct dependencies only.",
)
@click.option(
    "--self",
    "self_only",
    is_flag=True,
    help="Analyze only the named artifacts themselves, with no dependencies.",
)
@click.pass_context
def javainfo(
    ctx: click.Context, inputs: tuple[str, ...], direct: bool, self_only: bool
) -> None:
    """Show Java version requirements for endpoints, POMs, JARs, or class files.

    Accepts any mix of Maven coordinates, local POM files/directories, .jar files,
    .class files, and directories of compiled classes. Each argument is analyzed as
    an independent source.
    """

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)

    if direct and self_only:
        _log.error("--direct and --self are mutually exclusive")
        ctx.exit(1)

    args = build_parsed_args(opts, endpoint=None, command="info")
    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    reports: list[SourceReport] = []

    if inputs:
        for arg in inputs:
            reports.append(
                _javainfo_source(ctx, arg, builder, context, args, direct, self_only)
            )
    else:
        # No inputs: fall back to spec mode (jgo.toml), matching other subcommands.
        if args.is_spec_mode():
            spec_file = args.get_spec_file()
            if not spec_file.exists():
                _log.error(f"{spec_file} not found")
                ctx.exit(1)
            spec = EnvironmentSpec.load(spec_file)
            environment = _from_spec_or_die(ctx, builder, spec, args.update)
            reports.append(environment_report(environment, label=str(spec_file)))
        else:
            _log.error("No endpoint specified")
            ctx.exit(1)

    print_java_info(reports)
    ctx.exit(0)


def _javainfo_source(
    ctx: click.Context,
    arg: str,
    builder: EnvironmentBuilder,
    context: MavenContext,
    args: ParsedArgs,
    direct: bool,
    self_only: bool,
) -> SourceReport:
    """Build a SourceReport for a single javainfo argument."""

    kind, path = classify_javainfo_input(arg)

    if kind == "pom":
        return _javainfo_pom_report(ctx, path, context, args, direct, self_only)

    if kind in ("jar", "class"):
        if not path.exists():
            _log.error(f"{path} not found")
            ctx.exit(1)
        return paths_report(arg, [path])

    if kind == "dir":
        local = sorted(path.rglob("*.jar")) + sorted(path.rglob("*.class"))
        if not local:
            _log.error(f"No .jar or .class files found in {path}")
            ctx.exit(1)
        return paths_report(arg, local)

    # kind == "coordinate"
    return _javainfo_coordinate_report(
        ctx, arg, builder, context, args, direct, self_only
    )


def _resolve_artifact_path(artifact) -> Path | None:
    """Resolve an artifact to a local JAR path, returning None on failure."""
    try:
        resolved = artifact.resolve()
    except Exception as e:
        _log.debug(f"Could not resolve {artifact}: {e}")
        return None
    return resolved


def _javainfo_coordinate_report(
    ctx: click.Context,
    arg: str,
    builder: EnvironmentBuilder,
    context: MavenContext,
    args: ParsedArgs,
    direct: bool,
    self_only: bool,
) -> SourceReport:
    """Build a SourceReport for a Maven coordinate / endpoint argument."""

    # Default (transitive): build the full environment, exactly as before.
    if not direct and not self_only:
        environment = builder.from_endpoint(arg, update=args.update)
        return environment_report(environment, label=arg)

    # --self / --direct: resolve the named artifacts (and direct deps) directly.
    try:
        parsed = Endpoint.parse(arg)
    except ValueError as e:
        _log.error(f"Invalid endpoint format: {e}")
        ctx.exit(1)

    paths: list[Path] = []
    for coord in parsed.coordinates:
        version = coord.version or "RELEASE"
        component = context.project(coord.groupId, coord.artifactId).at_version(version)
        artifact = component.artifact(
            classifier=coord.classifier or "",
            packaging=coord.packaging or "jar",
        )
        resolved = _resolve_artifact_path(artifact)
        if resolved is not None:
            paths.append(resolved)

        if direct:
            _root, deps = context.pom_dependency_list(
                component.pom(),
                transitive=False,
                optional_depth=args.get_effective_optional_depth(),
            )
            for node in deps:
                resolved = _resolve_artifact_path(node.dep.artifact)
                if resolved is not None:
                    paths.append(resolved)

    return paths_report(arg, _dedup_paths(paths))


def _javainfo_pom_report(
    ctx: click.Context,
    pom_path: Path,
    context: MavenContext,
    args: ParsedArgs,
    direct: bool,
    self_only: bool,
) -> SourceReport:
    """Build a SourceReport for a local project POM argument."""

    from ...maven import POM

    if not pom_path.exists():
        _log.error(f"{pom_path} not found")
        ctx.exit(1)

    pom = POM(pom_path)
    label = str(pom_path)

    try:
        if self_only:
            # Just the project's own artifact (no dependencies).
            root, _deps = context.pom_dependency_list(pom, transitive=False)
            resolved = _resolve_artifact_path(root.dep.artifact)
            paths = [resolved] if resolved is not None else []
        else:
            _root, deps = context.pom_dependency_list(
                pom,
                transitive=not direct,
                optional_depth=args.get_effective_optional_depth(),
            )
            paths = []
            for node in deps:
                resolved = _resolve_artifact_path(node.dep.artifact)
                if resolved is not None:
                    paths.append(resolved)
    except (RuntimeError, ValueError) as e:
        _log.error(f"Failed to resolve {pom_path}: {e}")
        ctx.exit(1)

    return paths_report(label, _dedup_paths(paths))


def _dedup_paths(paths: list[Path]) -> list[Path]:
    """De-duplicate paths while preserving first-seen order."""
    seen: set[Path] = set()
    result: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


@click.command(help=f"Show entrypoints from {JGO_TOML}.")
@click.pass_context
def entrypoints(ctx: click.Context) -> None:
    """Show available entrypoints defined in jgo.toml."""

    opts = ctx.obj
    args = build_parsed_args(opts, endpoint=None, command="info")

    spec_file = args.file or Path("jgo.toml")

    if not spec_file.exists():
        _log.error(f"{spec_file} not found")
        ctx.exit(1)

    spec = EnvironmentSpec.load(spec_file)

    if not spec.entrypoints:
        console_print("No entrypoints defined")
        ctx.exit(0)

    console_print("Available entrypoints:")
    for name, main_class in spec.entrypoints.items():
        marker = " (default)" if name == spec.default_entrypoint else ""
        console_print(f"  {name}: {main_class}{marker}")

    ctx.exit(0)


@click.command(help="Show JAR manifest.")
@click.argument(
    "coordinate",
    required=True,
    cls=click.RichArgument,
    help=f"Maven coordinate in format {COORD_HELP_FULL}",
)
@click.option("--raw", is_flag=True, help="Show raw manifest contents")
@click.pass_context
def manifest(ctx: click.Context, coordinate: str, raw: bool) -> None:
    """Show the JAR manifest for the given coordinate."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=coordinate, command="info")

    try:
        # Create Maven context
        maven_context = create_maven_context(args, config.to_dict())

        # Parse coordinate to get G:A:V
        coord = _parse_coord_or_die(ctx, coordinate)
        version = coord.version or "RELEASE"

        # Get component
        component = maven_context.project(coord.groupId, coord.artifactId).at_version(
            version
        )

        # Resolve artifact to get JAR path
        artifact = component.artifact()
        jar_path = artifact.resolve()

        if not jar_path:
            _log.error(f"Could not resolve artifact: {coordinate}")
            ctx.exit(1)

        # Verify it's a valid JAR file
        if not zipfile.is_zipfile(jar_path):
            _log.error(f"Not a valid JAR file: {jar_path}")
            ctx.exit(1)

        # Read and display manifest
        if raw:
            manifest_content = read_raw_manifest(jar_path)
            if manifest_content is None:
                _log.error(f"No MANIFEST.MF found in {jar_path}")
                ctx.exit(1)
            console_print(manifest_content, end="")
        else:
            manifest_dict = parse_manifest(jar_path)
            if manifest_dict is None:
                _log.error(f"No MANIFEST.MF found in {jar_path}")
                ctx.exit(1)

            # Display parsed manifest
            for key, value in manifest_dict.items():
                console_print(f"{key}: {value}")

    except SystemExit:
        raise
    except Exception as e:
        _log.error(f"{e}")
        ctx.exit(1)


@click.command(help="Show POM content.")
@click.argument(
    "coordinate",
    required=True,
    cls=click.RichArgument,
    help=f"Maven coordinate in format {COORD_HELP_FULL}",
)
@click.pass_context
def pom(ctx: click.Context, coordinate: str) -> None:
    """Show the POM for the given component."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=coordinate, command="info")

    try:
        # Create Maven context
        maven_context = create_maven_context(args, config.to_dict())

        # Parse coordinate to get G:A:V
        coord = _parse_coord_or_die(ctx, coordinate)
        version = coord.version or "RELEASE"

        # Get component
        component = maven_context.project(coord.groupId, coord.artifactId).at_version(
            version
        )

        # Get raw POM and pretty-print
        pom_obj = component.pom()

        if not pom_obj or not pom_obj.source:
            _log.error(f"Could not resolve POM for: {coordinate}")
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
            xml_output = "\n".join(lines)
        except Exception:
            # If pretty-printing fails, use raw content
            xml_output = pom_content

        console_print(xml_output)

    except SystemExit:
        raise
    except Exception as e:
        _log.error(f"{e}")
        ctx.exit(1)


def _from_spec_or_die(
    ctx: click.Context, builder: EnvironmentBuilder, spec: EnvironmentSpec, update: bool
) -> Environment:
    """Call builder.from_spec(), printing a clean error and exiting on ValueError."""
    try:
        return builder.from_spec(spec, update=update)
    except ValueError as e:
        _log.error(f"{e} Use 'jgo add <coordinate>' to add dependencies.")
        ctx.exit(1)


def _parse_coord_or_die(ctx: click.Context, coord_str: str) -> Coordinate:
    """Parses a string to a Coordinate, guaranteeing non-None."""
    try:
        return Coordinate.parse(coord_str)
    except ValueError:
        _log.exception(f"Invalid coordinate string: {coord_str}")
        ctx.exit(1)


def _print_deps(ctx: click.Context, endpoint: str | None, list_mode: bool) -> None:
    """Common logic for deptree and deplist."""

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, endpoint=endpoint, command="info")

    context = create_maven_context(args, config.to_dict())
    builder = create_environment_builder(args, config.to_dict(), context)

    # Local POM file mode: resolve the real project POM directly.
    try:
        pom_path = resolve_pom_input(endpoint)
    except ValueError as e:
        _log.error(str(e))
        ctx.exit(1)
    if pom_path is not None:
        if not pom_path.exists():
            _log.error(f"{pom_path} not found")
            ctx.exit(1)
        try:
            print_pom_dependencies(
                pom_path,
                context,
                list_mode=list_mode,
                optional_depth=args.get_effective_optional_depth(),
            )
        except (RuntimeError, ValueError) as e:
            _log.error(f"Failed to resolve {pom_path}: {e}")
            ctx.exit(1)
        ctx.exit(0)

    # Parse coordinates into dependencies
    if args.is_spec_mode():
        spec_file = args.get_spec_file()
        if not spec_file.exists():
            _log.error(f"{spec_file} not found")
            ctx.exit(1)
        spec = EnvironmentSpec.load(spec_file)
        try:
            dependencies = builder.spec_to_dependencies(spec)
        except ValueError as e:
            _log.error(f"Invalid coordinate format: {e}")
            ctx.exit(1)
    else:
        if not endpoint:
            _log.error("No endpoint specified")
            ctx.exit(1)
        try:
            parsed = Endpoint.parse(endpoint)
        except ValueError as e:
            _log.error(f"Invalid endpoint format: {e}")
            ctx.exit(1)
        dependencies = builder._coordinates_to_dependencies(parsed.coordinates)

    print_dependencies(dependencies, context, list_mode=list_mode)
    ctx.exit(0)
