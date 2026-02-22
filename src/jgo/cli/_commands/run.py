"""jgo run - Execute Java applications from Maven coordinates or jgo.toml"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...env import EnvironmentSpec
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
def run(ctx, main_class, entrypoint, add_classpath, endpoint, remaining):
    """
    Run a Java application from Maven coordinates or jgo.toml.

    ENDPOINT FORMAT:
      groupId:artifactId[:version][:classifier][@mainClass]

    Multiple coordinates can be combined with '+':
      org.scijava:scijava-common+org.scijava:parsington

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

    environment = builder.from_spec(
        spec, update=args.update, entrypoint=args.entrypoint
    )

    # Create runner and execute
    _log.info(f"Running {spec.name}...")

    runner = create_java_runner(args, config, spec=spec)
    # Use environment's main class if set, otherwise fall back to args.main_class
    main_class_to_use = environment.main_class or args.main_class
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

    # Build environment
    _log.info(f"Building environment for {args.endpoint}...")

    environment = builder.from_endpoint(
        args.endpoint,
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
