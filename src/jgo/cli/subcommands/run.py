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

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Import here to avoid circular dependency
    from ..commands import JgoCommands

    # Delegate to existing JgoCommands implementation
    commands = JgoCommands(args, config)

    # Handle spec file mode vs endpoint mode
    if args.is_spec_mode():
        return commands._cmd_run_spec()
    else:
        return commands._cmd_run_endpoint()
