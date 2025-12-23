"""jgo run - Execute Java applications from Maven coordinates or jgo.toml"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(
    help="Run a Java application from Maven coordinates or jgo.toml",
    epilog="TIP: Use 'jgo --dry-run run' to see the command without executing it.",
    context_settings=dict(ignore_unknown_options=True, allow_interspersed_args=False),
)
@click.option(
    "--main-class",
    metavar="CLASS",
    help="Main class to run (supports auto-completion for simple names)",
)
@click.option(
    "--entrypoint",
    metavar="NAME",
    help="Run specific entrypoint from jgo.toml",
)
@click.option(
    "--add-classpath",
    multiple=True,
    metavar="PATH",
    help="Append to classpath (JARs, directories, etc.)",
)
@click.argument("endpoint", required=False)
@click.argument("remaining", nargs=-1, type=click.UNPROCESSED)
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
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args, _parse_remaining

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
    jvm_args, app_args = _parse_remaining(remaining)

    # Load config
    if opts.get("ignore_config"):
        config = GlobalSettings()
    else:
        config = GlobalSettings.load()

    # Build ParsedArgs
    args = _build_parsed_args(
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
    from ...config import GlobalSettings
    from ...env import EnvironmentSpec

    verbose = args.verbose > 0 and not args.quiet

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
                if verbose:
                    print(f"Using entrypoint '{args.endpoint}' from jgo.toml")
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

        if expanded != args.endpoint and verbose:
            print(f"Expanded shortcut: {args.endpoint} → {expanded}")

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
    from ...env import EnvironmentSpec
    from ..context import (
        create_environment_builder,
        create_java_runner,
        create_maven_context,
    )
    from ..output import print_classpath, print_java_info

    verbose = args.verbose > 0 and not args.quiet
    debug = args.verbose >= 2

    spec_file = args.get_spec_file()

    if not spec_file.exists():
        print(f"Error: {spec_file} not found", file=sys.stderr)
        return 1

    # Load spec
    spec = EnvironmentSpec.load(spec_file)

    # Create Maven context and environment builder
    context = create_maven_context(args, config)
    builder = create_environment_builder(args, config, context)

    # Build environment
    if verbose:
        print(f"Building environment from {spec_file}...")

    environment = builder.from_spec(
        spec, update=args.update, entrypoint=args.entrypoint
    )

    # If --print-classpath, just print and exit
    if args.print_classpath:
        print_classpath(environment)
        return 0

    # If --print-java-info, just print and exit
    if args.print_java_info:
        print_java_info(environment)
        return 0

    # Create runner and execute
    if verbose:
        print(f"Running {spec.name}...")

    runner = create_java_runner(args, config)
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
    from ..context import (
        create_environment_builder,
        create_java_runner,
        create_maven_context,
    )
    from ..output import print_classpath, print_java_info

    verbose = args.verbose > 0 and not args.quiet
    debug = args.verbose >= 2

    if not args.endpoint:
        print("Error: No endpoint specified", file=sys.stderr)
        print("Use 'jgo --help' for usage information", file=sys.stderr)
        return 1

    # Create Maven context and environment builder
    context = create_maven_context(args, config)
    builder = create_environment_builder(args, config, context)

    # Build environment
    if verbose:
        print(f"Building environment for {args.endpoint}...")

    environment = builder.from_endpoint(
        args.endpoint,
        update=args.update,
    )

    # If --print-classpath, just print and exit
    if args.print_classpath:
        print_classpath(environment)
        return 0

    # If --print-java-info, just print and exit
    if args.print_java_info:
        print_java_info(environment)
        return 0

    # Create runner and execute
    if verbose:
        print("Running Java application...")

    runner = create_java_runner(args, config)
    # CLI main_class override takes precedence, otherwise use environment's main class
    main_class_to_use = args.main_class or environment.main_class
    result = runner.run(
        environment=environment,
        main_class=main_class_to_use,
        app_args=args.app_args,
        additional_jvm_args=args.jvm_args,
        additional_classpath=args.classpath_append,
        print_command=debug,
        dry_run=args.dry_run,
    )

    return result.returncode
