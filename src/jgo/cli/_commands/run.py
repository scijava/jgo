"""jgo run - Execute Java applications from Maven coordinates or jgo.toml"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...env import EnvironmentSpec
from ...parse import Endpoint
from ...styles import (
    AT_MAINCLASS,
    DOUBLE_DASH,
    JGO_TOML,
    MAVEN_COORDINATES,
    PLUS_OPERATOR,
    TIP_DRY_RUN,
    action,
    secondary,
)
from ...util.logging import is_debug_enabled
from .._args import build_parsed_args, parse_remaining
from .._context import (
    create_environment_builder,
    create_java_runner,
    create_maven_context,
)

if TYPE_CHECKING:
    from .._args import ParsedArgs

_log = logging.getLogger(__name__)

# Long and short forms of every global jgo flag (from _parser.py global_options).
# Used to give a targeted hint when a flag is mistakenly placed after the subcommand.
# fmt: off
_GLOBAL_FLAGS: frozenset[str] = frozenset([
    "--verbose", "-v",
    "--quiet", "-q",
    "--wrap",
    "--color",
    "--file", "-f",
    "--dry-run",
    "--update", "-u",
    "--offline",
    "--no-cache",
    "--cache-dir",
    "--repo-cache",
    "--resolver",
    "--repository", "-r",
    "--include-optional",
    "--managed", "-m",
    "--java-version",
    "--java-vendor",
    "--system-java",
    "--gc",
    "--max-heap",
    "--min-heap",
    "--platform",
    "--os-name",
    "--os-family",
    "--os-arch",
    "--os-version",
    "--property", "-D",
    "--links",
    "--lenient",
    "--class-path-only",
    "--module-path-only",
    "--full-coordinates",
    "--ignore-config",
    "--ignore-jgorc",
    "--version",
])
# fmt: on


@click.command(
    help=f"Run a Java application from {MAVEN_COORDINATES} or {JGO_TOML}.",
    epilog=TIP_DRY_RUN,
    context_settings=dict(ignore_unknown_options=True, allow_interspersed_args=False),
)
@click.option(
    "--main-class",
    metavar="CLASS",
    help=f"Main class to run (supports {action('auto-completion')} for simple names)",
)
@click.option(
    "--entrypoint",
    metavar="NAME",
    help=f"Run specific entrypoint from {JGO_TOML}",
)
@click.option(
    "--add-classpath",
    multiple=True,
    metavar="PATH",
    help=f"Append to classpath ({secondary('JARs, directories, etc.')})",
)
@click.option(
    "--global",
    "force_global",
    is_flag=True,
    help=f"Ignore {JGO_TOML} and use global configuration only (endpoint mode).",
)
@click.option(
    "--local",
    "force_local",
    is_flag=True,
    help=f"Force {JGO_TOML} project mode even when an endpoint-like argument is present.",
)
@click.argument(
    "endpoint",
    required=False,
    cls=click.RichArgument,
    help=f"Maven coordinates (single or combined with {PLUS_OPERATOR}) "
    f"optionally followed by {AT_MAINCLASS}",
)
@click.argument(
    "remaining",
    nargs=-1,
    type=click.UNPROCESSED,
    cls=click.RichArgument,
    help=f"JVM arguments and program arguments, separated by {DOUBLE_DASH}. "
    f"Example: {secondary('-- -Xmx2G -- script.py')}",
)
@click.pass_context
def run(
    ctx,
    main_class,
    entrypoint,
    add_classpath,
    force_global,
    force_local,
    endpoint,
    remaining,
):
    """
    Run a Java application from Maven coordinates or jgo.toml.

    ENDPOINT FORMAT:
      coord[+coord...][@MainClass]
      where coord = groupId:artifactId[:version][:classifier][:packaging][!]

    Multiple coordinates are joined with '+':
      org.scijava:scijava-common+org.scijava:parsington

    The '!' suffix disables BOM dependency management for that coordinate:
      net.imagej:imagej:2.17.0!

    Main class can be specified in two ways:
      1. Using @ syntax: org.scijava:scijava-common@ScriptREPL
      2. Using --main-class: --main-class ScriptREPL

    Simple class names are auto-completed. For example:
      ScriptREPL → org.scijava.script.ScriptREPL

    If no endpoint is provided, runs the default entrypoint from jgo.toml.

    EXAMPLES:
      jgo run org.python:jython-standalone
      jgo run org.scijava:scijava-common@ScriptREPL
      jgo run --main-class ScriptREPL org.scijava:scijava-common
      jgo run org.python:jython-standalone:2.7.3 -- -Xmx2G -- script.py
      jgo run --local --main-class groovy.ui.GroovyMain -- script.groovy
      jgo run --global my-shortcut -- script.groovy

    TIP:
      Use 'jgo --dry-run run' to see the command without executing it.
    """

    # Get global options from context
    opts = ctx.obj

    # Add run-specific options
    if main_class:
        opts["main_class"] = main_class
    if entrypoint:
        opts["entrypoint"] = entrypoint
    if add_classpath:
        opts["add_classpath"] = add_classpath
    if force_global:
        opts["force_global"] = True

    # --local: force spec/project mode.  Click may have captured a positional
    # token as `endpoint` (e.g. when the user typed `-- script.groovy` and
    # click consumed the `--`).  Move it back to the front of `remaining` so
    # it ends up as an app arg rather than being treated as a Maven coordinate.
    if force_local and endpoint:
        remaining = (endpoint,) + remaining
        endpoint = None

    # Parse remaining args for JVM/app args
    jvm_args, app_args = parse_remaining(remaining)

    # Load config
    if opts.get("ignore_config"):
        config = GlobalSettings()
    else:
        config = GlobalSettings.load()

    # Build ParsedArgs
    args = build_parsed_args(
        opts, endpoint=endpoint, jvm_args=jvm_args, app_args=app_args, command="run"
    )

    # Execute
    exit_code = execute(args, config.to_dict())
    ctx.exit(exit_code)


def execute(args: ParsedArgs, config: dict) -> int:
    """
    Execute the run command.

    Handles resolution order for shortcut expansion:
    1. If jgo.toml exists and endpoint is an entrypoint name → use entrypoint (spec mode)
    2. Else if endpoint is a shortcut → expand shortcut and run (endpoint mode)
    3. Else treat as literal Maven coordinate (endpoint mode)

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """

    # --global: bypass jgo.toml entirely and run in endpoint mode
    if args.force_global:
        return _run_endpoint(args, config)

    # Check if we're in spec mode (jgo.toml exists)
    spec_file = Path("jgo.toml")
    if spec_file.exists() and not args.endpoint:
        # No endpoint specified, use jgo.toml
        return _run_spec(args, config)

    # If endpoint is specified and jgo.toml exists, check resolution order
    if args.endpoint and spec_file.exists():
        try:
            spec = EnvironmentSpec.load(spec_file)
            # Check if endpoint is an entrypoint name
            if args.endpoint in spec.entrypoints:
                # Use entrypoint from jgo.toml (project-local wins)
                _log.info(f"Using entrypoint '{args.endpoint}' from jgo.toml")
                # Set entrypoint argument and run in spec mode
                args.entrypoint = args.endpoint
                args.endpoint = None  # Clear endpoint to trigger spec mode
                return _run_spec(args, config)

        except Exception:
            # If we can't load spec, fall through to endpoint mode
            pass

    # Not an entrypoint, expand shortcuts
    if args.endpoint:
        shortcuts = config.get("shortcuts", {})
        jgoconfig = GlobalSettings(shortcuts=shortcuts)
        expanded = jgoconfig.expand_shortcuts(args.endpoint)

        if expanded != args.endpoint:
            _log.info(f"Expanded shortcut: {args.endpoint} → {expanded}")

        # Update endpoint with expanded value
        args.endpoint = expanded

    # Run in endpoint mode
    return _run_endpoint(args, config)


def _run_spec(args: ParsedArgs, config: dict) -> int:
    """
    Run from jgo.toml spec file.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """

    debug = is_debug_enabled()

    spec_file = args.get_spec_file()

    if not spec_file.exists():
        _log.error(f"{spec_file} not found")
        return 1

    # Load spec
    spec = EnvironmentSpec.load(spec_file)

    # Create Maven context and environment builder
    context = create_maven_context(args, config)
    builder = create_environment_builder(args, config, context)

    # Build environment
    _log.info(f"Building environment from {spec_file}...")

    try:
        environment = builder.from_spec(
            spec, update=args.update, entrypoint=args.entrypoint
        )
    except ValueError as e:
        _log.error(f"{e} Use 'jgo add <coordinate>' to add dependencies.")
        return 1

    # Create runner and execute
    _log.info(f"Running {spec.name}...")

    runner = create_java_runner(args, config, spec=spec)
    # CLI --main-class overrides environment's configured main class
    main_class_to_use = args.main_class or environment.get_main_class(args.entrypoint)
    result = runner.run(
        environment=environment,
        main_class=main_class_to_use,
        app_args=args.app_args,
        additional_jvm_args=args.jvm_args,
        additional_classpath=args.classpath_append,
        print_command=debug,
        dry_run=args.dry_run,
        module_mode=args.module_mode,
    )

    return result.returncode


def _run_endpoint(args: ParsedArgs, config: dict) -> int:
    """
    Run from endpoint string.

    Args:
        args: Parsed command line arguments
        config: Global settings

    Returns:
        Exit code (0 for success, non-zero for failure)
    """

    debug = is_debug_enabled()

    if not args.endpoint:
        _log.error("No endpoint specified")
        _log.error("Use 'jgo --help' for usage information")
        return 1

    # Create Maven context and environment builder
    context = create_maven_context(args, config)
    builder = create_environment_builder(args, config, context)

    # Validate endpoint format before attempting to build the environment.
    # Only parse errors (malformed coordinate strings) warrant the "not a valid
    # endpoint" message; resolution errors (missing versions, network issues,
    # etc.) should propagate as-is so the user sees the real cause.
    endpoint = args.endpoint
    try:
        Endpoint.parse(endpoint)
    except ValueError:
        _log.error(f"'{endpoint}' is not a valid endpoint")
        # Strip =value suffix (e.g. --gc=G1 → --gc) before checking
        flag_name = endpoint.split("=")[0] if "=" in endpoint else endpoint
        if flag_name in _GLOBAL_FLAGS:
            _log.error(
                f"Hint: {flag_name} is a global flag; "
                f"did you mean: jgo {flag_name} run?"
            )
        else:
            _log.error("Endpoints use Maven coordinates: groupId:artifactId[:version]")
        return 1

    # Build environment
    _log.info(f"Building environment for {endpoint}...")

    environment = builder.from_endpoint(
        endpoint,
        update=args.update,
        main_class=args.main_class,
    )

    # Create runner and execute
    _log.info("Running Java application...")

    runner = create_java_runner(args, config, spec=None)
    # Use environment's main class (which includes auto-completed CLI override if provided)
    main_class_to_use = environment.main_class
    result = runner.run(
        environment=environment,
        main_class=main_class_to_use,
        app_args=args.app_args,
        additional_jvm_args=args.jvm_args,
        additional_classpath=args.classpath_append,
        print_command=debug,
        dry_run=args.dry_run,
        module_mode=args.module_mode,
    )

    return result.returncode
