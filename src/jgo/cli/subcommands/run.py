"""jgo run - Execute Java applications from Maven coordinates or jgo.toml"""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from ..parser import ParsedArgs


@click.command(help="Run a Java application from Maven coordinates or jgo.toml")
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
    """
    from ...config.jgorc import JgoConfig
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
    if opts.get("ignore_jgorc"):
        config = JgoConfig()
    else:
        config = JgoConfig.load()

    # Build ParsedArgs for backwards compat with existing code
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
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from pathlib import Path

    # Import here to avoid circular dependency
    from ...config.jgorc import JgoConfig
    from ...env import EnvironmentSpec
    from ..commands import JgoCommands

    # Check if we're in spec mode (jgo.toml exists)
    spec_file = Path("jgo.toml")
    if spec_file.exists() and not args.endpoint:
        # No endpoint specified, use jgo.toml
        return JgoCommands(args, config)._cmd_run_spec()

    # If endpoint is specified and jgo.toml exists, check resolution order
    if args.endpoint and spec_file.exists():
        try:
            spec = EnvironmentSpec.load(spec_file)
            # Check if endpoint is an entrypoint name
            if args.endpoint in spec.entrypoints:
                # Use entrypoint from jgo.toml (project-local wins)
                if args.verbose > 0:
                    print(f"Using entrypoint '{args.endpoint}' from jgo.toml")
                # Set entrypoint argument and run in spec mode
                args.entrypoint = args.endpoint
                args.endpoint = None  # Clear endpoint to trigger spec mode
                return JgoCommands(args, config)._cmd_run_spec()
        except Exception:
            # If we can't load spec, fall through to endpoint mode
            pass

    # Not an entrypoint, expand shortcuts
    if args.endpoint:
        shortcuts = config.get("shortcuts", {})
        jgoconfig = JgoConfig(shortcuts=shortcuts)
        expanded = jgoconfig.expand_shortcuts(args.endpoint)

        if expanded != args.endpoint and args.verbose > 0:
            print(f"Expanded shortcut: {args.endpoint} → {expanded}")

        # Update endpoint with expanded value
        args.endpoint = expanded

    # Run in endpoint mode
    return JgoCommands(args, config)._cmd_run_endpoint()
